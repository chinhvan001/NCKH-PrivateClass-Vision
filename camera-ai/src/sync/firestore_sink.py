"""Cong Firestore cua 1 edge node: ghi record/alert/tong ket/heartbeat theo batch,
nghe trang thai phien (UC02, UC04, UC09).

Pipeline goi ``add_*`` ngay trong vong lap frame nen cac ham nay chi xep hang
trong RAM. Thread nen gom hang doi thanh WriteBatch va commit; loi mang thi giu
nguyen item va thu lai voi exponential backoff + jitter (UC02 luong phu: dong
bo Firebase loi -> xep hang du lieu khong sinh trac hoc). Sink song suot tien
trinh, khong theo phien, de du lieu cua phien da ket thuc van duoc gui khi co mang.

Doc ID sinh 1 lan luc xep hang: commit lai sau loi mo ho (server da ghi nhung
client timeout) chi ghi de document cu, khong tao ban trung.
"""

from __future__ import annotations

import logging
import os
import random
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.privacy import AlertEvent, AnonymizedEngagementRecord, SessionSummary, check_session_id

logger = logging.getLogger("camera_ai.sync")

MAX_BATCH_WRITES = 500  # gioi han so write trong 1 WriteBatch cua Firestore
_COMMIT_TIMEOUT_SEC = 10.0

# idle: khong co phien. monitoring: dang nhan frame. paused: giao vien tam dung.
# unavailable: phien dang chay nhung camera khong cho frame (UC02: tam khong kha dung).
# outside_schedule: phien dang chay ngoai cua so lich trong config, camera khong bat.
EDGE_STATUSES = frozenset({"idle", "monitoring", "paused", "unavailable", "outside_schedule"})

# ``status`` cua phien tren web admin -> trang thai EdgeRuntime dung. Gia tri khac giu
# nguyen: ``paused`` van chay duoc; ``scheduled``/``cancelled`` khong phai phien song.
WEB_STATUS_TO_STATE = {"live": "active", "completed": "ended"}


@dataclass(frozen=True)
class EdgeHeartbeat:
    """Trang thai thiet bi, khong co du lieu hoc sinh. Thoi gian la wall-clock UTC
    cua edge (can dong bo NTP); app coi edge offline neu ``updated_at`` qua cu."""

    online: bool
    status: str
    session_id: str | None
    fps: float  # frame da inference / giay, tu heartbeat truoc
    camera_ok: bool | None  # None: chua mo camera lan nao
    last_frame_at: datetime | None
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.status not in EDGE_STATUSES:
            raise ValueError(f"status phai thuoc {sorted(EDGE_STATUSES)}.")

    def to_dict(self) -> dict:
        return asdict(self)


def firestore_client_from_env() -> Any:
    """Firestore client dang nhap bang file key service account o ``GOOGLE_APPLICATION_CREDENTIALS``.

    Key nam NGOAI repo va ngoai config local; khong log noi dung key.
    ``firebase_admin`` duoc import muon de CI/test chay khong can SDK hay credential.
    """
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path or not Path(key_path).is_file():
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS phai tro toi file key service account (dat ngoai repo).")
    import firebase_admin
    from firebase_admin import credentials, firestore

    try:
        app = firebase_admin.get_app()
    except ValueError:  # chua khoi tao app mac dinh
        app = firebase_admin.initialize_app(credentials.Certificate(key_path))
    return firestore.client(app)


def _session_state(data: dict | None) -> str | None:
    """``status`` do web admin ghi -> trang thai cho EdgeRuntime; khong phai chuoi (document
    sua tay hong) -> None, tuc khong phai phien song, thay vi lam chet listener."""
    status = (data or {}).get("status")
    return WEB_STATUS_TO_STATE.get(status, status) if isinstance(status, str) else None


class FirestoreSink:
    """Ghi du lieu cua 1 camera (edge node) vao ``sessions/{session_id}`` cua web admin
    va heartbeat vao ``classrooms/{classroom_id}``; layout day du o ``src/sync/README.md``.
    ``client`` la ``firestore.Client`` (xem ``firestore_client_from_env``) hoac fake trong test.

    Pipeline phat 1 record/ghe/frame; sink chi giu 1 record moi
    ``record_interval_sec`` cho moi ghe, hoac ngay khi ``posture_state`` doi.
    Diem va bo dem trong record la luy ke nen record bo qua khong mat thong tin.

    Hang doi gioi han ``max_queue`` item: khi day, bo record cu nhat truoc; alert
    va tong ket phien chi bi bo khi hang doi khong con record (QA03: khong lam roi
    alert). Heartbeat khong xep hang: chi giu ban moi nhat.
    """

    def __init__(
        self,
        client: Any,
        classroom_id: str,
        camera_id: str,
        *,
        max_queue: int = 20_000,
        batch_size: int = MAX_BATCH_WRITES,
        flush_interval_sec: float = 2.0,
        max_backoff_sec: float = 60.0,
        record_interval_sec: float = 10.0,
    ) -> None:
        for name, value in (("classroom_id", classroom_id), ("camera_id", camera_id)):
            if not isinstance(value, str) or not value.strip() or "/" in value:
                raise ValueError(f"{name} phai la chuoi khong rong, khong chua '/'.")
        if not 1 <= batch_size <= MAX_BATCH_WRITES:
            raise ValueError(f"batch_size phai trong [1, {MAX_BATCH_WRITES}].")
        if max_queue < 1 or flush_interval_sec <= 0 or max_backoff_sec < flush_interval_sec:
            raise ValueError("Can max_queue >= 1, flush_interval_sec > 0, max_backoff_sec >= flush_interval_sec.")
        self.max_queue = max_queue
        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec
        self.max_backoff_sec = max_backoff_sec
        self.record_interval_sec = record_interval_sec
        self.dropped = 0  # item bi bo do hang doi day hoac Firestore tu choi du lieu
        self.failures = 0  # so lan flush loi lien tiep, quyet dinh backoff
        self._client = client
        self._classroom_id = classroom_id
        self._camera_id = camera_id
        # ponytail: hang doi chi nam trong RAM, mat khi tat tien trinh; ghi xuong dia
        # thi phai ma hoa (docs/cloud_data_compliance_checklist.md muc 3.5).
        self._priority: deque = deque()  # alert + tong ket phien
        self._records: deque = deque()
        self._heartbeat: tuple[str, dict] | None = None
        self._last_record: dict[str, AnonymizedEngagementRecord] = {}
        self._throttle_session: str | None = None
        self._lock = threading.Lock()  # bao ve hang doi, heartbeat va ``dropped``
        self._flush_lock = threading.Lock()  # moi luc chi 1 batch dang gui
        self._wake = threading.Event()
        self._closing = False
        self._thread: threading.Thread | None = None

    @property
    def pending(self) -> int:
        with self._lock:
            return len(self._priority) + len(self._records) + (self._heartbeat is not None)

    @property
    def backoff_sec(self) -> float:
        """Thoi gian cho truoc lan thu lai ke tiep (chua jitter): x2 sau moi lan loi, toi da ``max_backoff_sec``."""
        return min(self.max_backoff_sec, self.flush_interval_sec * 2 ** min(self.failures, 16))

    def add_record(self, session_id: str, record: AnonymizedEngagementRecord) -> None:
        if not isinstance(record, AnonymizedEngagementRecord):
            raise TypeError("Chi nhan AnonymizedEngagementRecord (schema allowlist).")
        if session_id != self._throttle_session:  # phien moi: ghe nao cung gui record dau tien
            self._throttle_session = check_session_id(session_id)
            self._last_record.clear()
        last = self._last_record.get(record.seat_id)
        if (
            last is not None
            and record.posture_state == last.posture_state
            and record.observed_at_sec - last.observed_at_sec < self.record_interval_sec
        ):
            return
        self._last_record[record.seat_id] = record
        self._enqueue(self._records, f"sessions/{session_id}/engagement/{uuid.uuid4().hex}", record)

    def add_alert(self, alert: AlertEvent) -> None:
        if not isinstance(alert, AlertEvent):
            raise TypeError("Chi nhan AlertEvent (schema allowlist).")
        self._enqueue(self._priority, f"sessions/{alert.session_id}/alerts/{uuid.uuid4().hex}", alert)
        self._wake.set()  # gui ngay, khong doi chu ky flush (QA01: alert < 1s)

    def add_summary(self, summary: SessionSummary) -> None:
        """Ghi de ``sessions/{session_id}/summaries/{camera_id}`` (moi camera 1 document)."""
        if not isinstance(summary, SessionSummary):
            raise TypeError("Chi nhan SessionSummary (schema allowlist).")
        self._enqueue(self._priority, self._summary_path(summary.session_id), summary)
        self._wake.set()

    def set_heartbeat(self, heartbeat: EdgeHeartbeat) -> None:
        """Ghi de ``classrooms/{classroom_id}/edge_nodes/{camera_id}`` o lan flush ke tiep;
        heartbeat cu chua gui bi thay."""
        if not isinstance(heartbeat, EdgeHeartbeat):
            raise TypeError("Chi nhan EdgeHeartbeat.")
        with self._lock:
            self._heartbeat = (f"classrooms/{self._classroom_id}/edge_nodes/{self._camera_id}", heartbeat.to_dict())

    def summary_exists(self, session_id: str) -> bool:
        """Camera nay da tung xu ly phien chua (vd tien trinh truoc chet giua phien).
        Doc dong bo; loi mang -> coi nhu chua (khong co bang chung gian doan)."""
        path = self._summary_path(check_session_id(session_id))
        try:
            return self._client.document(path).get(retry=None, timeout=_COMMIT_TIMEOUT_SEC).exists
        except Exception as error:
            logger.warning("Khong doc duoc tong ket phien (%s), coi nhu phien moi.", type(error).__name__)
            return False

    def watch_sessions(self, on_change: Callable[[dict[str, Any]], None]) -> Any:
        """Nghe ``sessions`` cua web admin co ``classroom_id`` la lop nay: goi
        ``on_change({session_id: state})`` (``status`` da doi qua ``WEB_STATUS_TO_STATE``)
        tren thread cua listener moi khi co thay doi. Tra ve watch co ``unsubscribe()``."""
        # where() positional thay vi FieldFilter: module khong import SDK, CI chay khong can no.
        # ponytail: snapshot gom moi phien cua lop ke ca da xong (de thay ``completed``); loc
        # them theo status thi phien vua xong bien mat -> runtime ghi ``incomplete`` thay vi ``completed``.
        query = self._client.collection("sessions").where("classroom_id", "==", self._classroom_id)
        return query.on_snapshot(
            lambda docs, changes, read_time: on_change({doc.id: _session_state(doc.to_dict()) for doc in docs})
        )

    def flush(self) -> bool:
        """Commit het hang doi theo batch (heartbeat, alert, tong ket truoc). Tra False
        neu gap loi tam thoi: batch dang gui duoc tra lai dau hang doi de thu lai sau."""
        with self._flush_lock:
            while True:
                with self._lock:
                    taken = [(None, self._heartbeat)] if self._heartbeat is not None else []
                    self._heartbeat = None
                    for queue in (self._priority, self._records):
                        while queue and len(taken) < self.batch_size:
                            taken.append((queue, queue.popleft()))
                if not taken:
                    self.failures = 0
                    return True
                try:
                    batch = self._client.batch()
                    for _, (path, data) in taken:
                        batch.set(self._client.document(path), data)
                    batch.commit(retry=None, timeout=_COMMIT_TIMEOUT_SEC)  # retry/backoff do sink quyet dinh
                except Exception as error:
                    # Chi log ten loi: message cua server co the lap lai gia tri du lieu.
                    if getattr(error, "code", None) == 400 or isinstance(error, (TypeError, ValueError)):
                        # Du lieu bi tu choi: thu lai cung vo ich, bo batch de hang doi khong ket mai.
                        with self._lock:
                            self.dropped += len(taken)
                        logger.error("Firestore tu choi batch %d item (%s), da bo.", len(taken), type(error).__name__)
                        continue
                    with self._lock:
                        for queue, item in reversed(taken):
                            if queue is None:
                                self._heartbeat = self._heartbeat or item  # heartbeat moi hon (neu co) thang
                            else:
                                queue.appendleft(item)
                        self._trim()
                    self.failures += 1
                    logger.warning(
                        "Ghi Firestore loi (%s), thu lai sau ~%.0fs; dang cho %d item, da bo %d.",
                        type(error).__name__,
                        self.backoff_sec,
                        self.pending,
                        self.dropped,
                    )
                    return False

    def start(self) -> None:
        """Bat thread nen: flush moi ``flush_interval_sec``, ngay khi co alert/tong ket, backoff khi loi."""
        if self._thread and self._thread.is_alive():
            return
        self._closing = False
        self._thread = threading.Thread(target=self._run, name="firestore-sink", daemon=True)
        self._thread.start()

    def close(self, timeout: float = 30.0) -> None:
        """Dung thread va flush lan cuoi. Item chua gui duoc (dang mat mang) se mat
        khi tat tien trinh vi hang doi chi nam trong RAM."""
        self._closing = True
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)
        if not self.flush():
            logger.warning("Dong sink khi con %d item chua gui duoc len Firestore.", self.pending)

    def __enter__(self) -> "FirestoreSink":
        self.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _summary_path(self, session_id: str) -> str:
        return f"sessions/{session_id}/summaries/{self._camera_id}"

    def _enqueue(self, queue: deque, path: str, item: Any) -> None:
        with self._lock:
            queue.append((path, item.to_dict()))
            self._trim()

    def _trim(self) -> None:
        """Goi khi dang giu ``_lock``: bo item cu nhat, record truoc alert/tong ket."""
        while len(self._priority) + len(self._records) > self.max_queue:
            (self._records or self._priority).popleft()
            self.dropped += 1

    def _run(self) -> None:
        delay = self.flush_interval_sec
        while True:
            self._wake.wait(delay)
            self._wake.clear()
            if self._closing:
                return  # close() flush lan cuoi
            delay = self.flush_interval_sec if self.flush() else self.backoff_sec * random.uniform(0.5, 1.0)
