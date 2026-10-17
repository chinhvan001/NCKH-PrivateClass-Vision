"""Cong Firestore cua 1 edge node theo schema cua nhom (UC02, UC04, UC07, UC09).

Edge ghi (layout day du o ``src/sync/README.md``):

- ``session_results/{session_id}``: trang thai hien tai moi ghe, ghi de (``set_result``).
- ``session_evaluations/{session_id}_{seat_id}``: tong hop tung ghe, ghi de (``set_evaluations``).
- ``sessions/{session_id}/alerts/{id}``: canh bao, chi them moi (``add_alert``).
- ``edge_nodes/{camera_id}``: heartbeat thiet bi, ghi de (``set_heartbeat``).

va nghe ``sessions`` co ``class_id`` cua lop (``watch_sessions``).

Pipeline goi cac ham tren ngay trong vong lap frame nen chung chi cap nhat hang
doi trong RAM. Thread nen gom thanh WriteBatch va commit; loi mang thi giu
nguyen item va thu lai voi exponential backoff + jitter (UC02 luong phu: dong
bo Firebase loi -> xep hang du lieu khong sinh trac hoc). Document ghi de chi giu
ban moi nhat cho moi duong dan nen mat mang lau khong lam hang doi phinh ra.
Sink song suot tien trinh, khong theo phien, de du lieu cua phien da ket thuc
van duoc gui khi co mang.

Doc ID alert sinh 1 lan luc xep hang: commit lai sau loi mo ho (server da ghi
nhung client timeout) chi ghi de document cu, khong tao ban trung. Moi document
cua phien co ``expire_at`` = luc xep hang + ``retention_days`` de TTL cua
Firestore tu xoa (docs/cloud_data_compliance_checklist.md muc 3.6).
"""

from __future__ import annotations

import logging
import os
import random
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from src.privacy import AlertEvent, SeatEvaluation, SessionResult, check_session_id

logger = logging.getLogger("camera_ai.sync")

MAX_BATCH_WRITES = 500  # gioi han so write trong 1 WriteBatch cua Firestore
_COMMIT_TIMEOUT_SEC = 10.0

# idle: khong co phien. monitoring: dang nhan frame. paused: giao vien tam dung.
# unavailable: phien dang chay nhung camera khong cho frame (UC02: tam khong kha dung).
# outside_schedule: phien dang chay ngoai cua so lich trong config, camera khong bat.
EDGE_STATUSES = frozenset({"idle", "monitoring", "paused", "unavailable", "outside_schedule"})

# ``status`` cua phien (schema cua nhom) -> trang thai EdgeRuntime dung. Gia tri khac giu
# nguyen: ``paused`` van chay duoc; ``scheduled``/``cancelled`` khong phai phien song.
# ponytail: "live"/"completed" la gia tri cu cua nhanh Web; bo khi Web chuyen sang running/ended.
WEB_STATUS_TO_STATE = {"running": "active", "ended": "ended", "live": "active", "completed": "ended"}


@dataclass(frozen=True)
class EdgeHeartbeat:
    """Trang thai thiet bi, khong co du lieu hoc sinh. Thoi gian la wall-clock UTC
    cua edge (can dong bo NTP); app coi edge offline neu ``updated_at`` qua cu."""

    class_id: str
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
    """Ghi du lieu cua 1 camera (edge node) theo layout o ``src/sync/README.md``.
    ``client`` la ``firestore.Client`` (xem ``firestore_client_from_env``) hoac fake trong test.

    Alert giu trong hang doi gioi han ``max_queue`` (day thi bo cai cu nhat). Ket
    qua, tong hop va heartbeat la document ghi de: chi giu ban moi nhat cho moi
    duong dan, ban moi thay ban cu chua gui duoc.
    """

    def __init__(
        self,
        client: Any,
        class_id: str,
        camera_id: str,
        *,
        retention_days: int,
        max_queue: int = 20_000,
        batch_size: int = MAX_BATCH_WRITES,
        flush_interval_sec: float = 2.0,
        max_backoff_sec: float = 60.0,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        for name, value in (("class_id", class_id), ("camera_id", camera_id)):
            if not isinstance(value, str) or not value.strip() or "/" in value:
                raise ValueError(f"{name} phai la chuoi khong rong, khong chua '/'.")
        if not isinstance(retention_days, int) or isinstance(retention_days, bool) or retention_days < 1:
            raise ValueError("retention_days phai la so nguyen >= 1.")
        if not 1 <= batch_size <= MAX_BATCH_WRITES:
            raise ValueError(f"batch_size phai trong [1, {MAX_BATCH_WRITES}].")
        if max_queue < 1 or flush_interval_sec <= 0 or max_backoff_sec < flush_interval_sec:
            raise ValueError("Can max_queue >= 1, flush_interval_sec > 0, max_backoff_sec >= flush_interval_sec.")
        self.max_queue = max_queue
        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec
        self.max_backoff_sec = max_backoff_sec
        self.retention = timedelta(days=retention_days)
        self.dropped = 0  # item bi bo do hang doi day hoac Firestore tu choi du lieu
        self.failures = 0  # so lan flush loi lien tiep, quyet dinh backoff
        self._client = client
        self._class_id = class_id
        self._camera_id = camera_id
        self._now = now
        # ponytail: hang doi chi nam trong RAM, mat khi tat tien trinh; ghi xuong dia
        # thi phai ma hoa (docs/cloud_data_compliance_checklist.md muc 3.5).
        self._alerts: deque = deque()
        self._latest: dict[str, dict] = {}  # duong dan -> du lieu moi nhat cua document ghi de
        self._lock = threading.Lock()  # bao ve hang doi va ``dropped``
        self._flush_lock = threading.Lock()  # moi luc chi 1 batch dang gui
        self._wake = threading.Event()
        self._closing = False
        self._thread: threading.Thread | None = None

    @property
    def pending(self) -> int:
        with self._lock:
            return len(self._alerts) + len(self._latest)

    @property
    def backoff_sec(self) -> float:
        """Thoi gian cho truoc lan thu lai ke tiep (chua jitter): x2 sau moi lan loi, toi da ``max_backoff_sec``."""
        return min(self.max_backoff_sec, self.flush_interval_sec * 2 ** min(self.failures, 16))

    def add_alert(self, alert: AlertEvent) -> None:
        if not isinstance(alert, AlertEvent):
            raise TypeError("Chi nhan AlertEvent (schema allowlist).")
        with self._lock:
            self._alerts.append((f"sessions/{alert.session_id}/alerts/{uuid.uuid4().hex}", self._expiring(alert)))
            self._trim()
        self._wake.set()  # gui ngay, khong doi chu ky flush (QA01: alert < 1s)

    def set_result(self, result: SessionResult) -> None:
        """Ghi de ``session_results/{session_id}``; ket qua cuoi phien duoc gui ngay."""
        if not isinstance(result, SessionResult):
            raise TypeError("Chi nhan SessionResult (schema allowlist).")
        self._put(f"session_results/{result.session_id}", self._expiring(result))
        if result.monitoring_status != "running":
            self._wake.set()

    def set_evaluations(self, evaluations: Iterable[SeatEvaluation]) -> None:
        """Ghi de ``session_evaluations/{session_id}_{seat_id}`` cho tung ghe."""
        evaluations = list(evaluations)
        if not all(isinstance(evaluation, SeatEvaluation) for evaluation in evaluations):
            raise TypeError("Chi nhan SeatEvaluation (schema allowlist).")
        for evaluation in evaluations:
            self._put(f"session_evaluations/{evaluation.session_id}_{evaluation.seat_id}", self._expiring(evaluation))

    def set_heartbeat(self, heartbeat: EdgeHeartbeat) -> None:
        """Ghi de ``edge_nodes/{camera_id}`` o lan flush ke tiep."""
        if not isinstance(heartbeat, EdgeHeartbeat):
            raise TypeError("Chi nhan EdgeHeartbeat.")
        self._put(f"edge_nodes/{self._camera_id}", heartbeat.to_dict())

    def result_exists(self, session_id: str) -> bool:
        """Da co ket qua cua phien nay chua (vd tien trinh truoc chet giua phien).
        Doc dong bo; loi mang -> coi nhu chua (khong co bang chung gian doan)."""
        path = f"session_results/{check_session_id(session_id)}"
        try:
            return self._client.document(path).get(retry=None, timeout=_COMMIT_TIMEOUT_SEC).exists
        except Exception as error:
            logger.warning("Khong doc duoc ket qua phien (%s), coi nhu phien moi.", type(error).__name__)
            return False

    def watch_sessions(self, on_change: Callable[[dict[str, Any]], None]) -> Any:
        """Nghe ``sessions`` co ``class_id`` la lop nay: goi ``on_change({session_id: state})``
        (``status`` da doi qua ``WEB_STATUS_TO_STATE``) tren thread cua listener moi khi co
        thay doi. Tra ve watch co ``unsubscribe()``."""
        # where() positional thay vi FieldFilter: module khong import SDK, CI chay khong can no.
        # ponytail: snapshot gom moi phien cua lop ke ca da xong (de thay ``ended``); loc
        # them theo status thi phien vua xong bien mat -> runtime ghi ``incomplete`` thay vi ``completed``.
        query = self._client.collection("sessions").where("class_id", "==", self._class_id)
        return query.on_snapshot(
            lambda docs, changes, read_time: on_change({doc.id: _session_state(doc.to_dict()) for doc in docs})
        )

    def flush(self) -> bool:
        """Commit het hang doi theo batch (alert truoc). Tra False neu gap loi tam thoi:
        batch dang gui duoc tra lai hang doi de thu lai sau."""
        with self._flush_lock:
            while True:
                with self._lock:
                    taken = []
                    while self._alerts and len(taken) < self.batch_size:
                        taken.append((True, self._alerts.popleft()))
                    while self._latest and len(taken) < self.batch_size:
                        path = next(iter(self._latest))
                        taken.append((False, (path, self._latest.pop(path))))
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
                        for is_alert, (path, data) in reversed(taken):
                            if is_alert:
                                self._alerts.appendleft((path, data))
                            else:
                                self._latest.setdefault(path, data)  # ban moi hon (neu co) thang
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
        """Bat thread nen: flush moi ``flush_interval_sec``, ngay khi co alert/ket qua cuoi phien, backoff khi loi."""
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

    def _expiring(self, item: Any) -> dict:
        return {**item.to_dict(), "expire_at": self._now() + self.retention}

    def _put(self, path: str, data: dict) -> None:
        with self._lock:
            self._latest[path] = data

    def _trim(self) -> None:
        """Goi khi dang giu ``_lock``: hang doi alert day thi bo alert cu nhat."""
        while len(self._alerts) > self.max_queue:
            self._alerts.popleft()
            self.dropped += 1

    def _run(self) -> None:
        delay = self.flush_interval_sec
        while True:
            self._wake.wait(delay)
            self._wake.clear()
            if self._closing:
                return  # close() flush lan cuoi
            delay = self.flush_interval_sec if self.flush() else self.backoff_sec * random.uniform(0.5, 1.0)
