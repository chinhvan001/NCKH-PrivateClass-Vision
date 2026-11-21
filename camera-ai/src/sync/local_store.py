"""Thu muc chung voi web admin tren cung may (``edge-data/`` o goc repo, UC02, UC04, UC07, UC09).

Camera AI va backend web chay tren cung 1 may nen giao tiep qua file JSON thay cho Firestore: camera AI
khong can Firebase, va cac lan ghi 10 s/lan (ket qua, window, heartbeat) khong ton quota cua project.
Phia web la ``backend/services/edge_store.py``; layout day du o ``src/sync/README.md``.

Web admin ghi, edge doc:

- ``cameras/{camera_id}.json``: ``angle_type``, ``source`` (URL RTSP kem mat khau: khong log).
- ``camera_sessions/{camera_id}.json``: tiet hien tai cua camera: ``session_id``, ``status``, ``class_id``,
  ``row_count``, ``column_count``, ``seat_regions`` (o ghe ve tren web, chot luc bat dau tiet).

Edge ghi (``LocalSink``), web doc:

- ``edge_nodes/{camera_id}.json``: heartbeat.
- ``sessions/{session_id}/result.json``, ``evaluations.json`` (``{seat_id: ...}``), ``windows.jsonl`` va
  ``alerts.jsonl`` (moi dong 1 document, chi them). Web ghi them ``handled_alerts.json`` vao thu muc nay.

File ghi de duoc ghi nguyen tu (file tam roi ``os.replace``): ben doc thay ban cu hoac ban moi day du.
Moi file JSONL chi co 1 thread ghi; dong cuoi dang ghi do thi ben doc bo qua.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from src.privacy import AlertEvent, SeatEvaluation, SessionResult, SessionWindow, check_session_id

logger = logging.getLogger("camera_ai.sync")

DATA_DIR = Path(__file__).resolve().parents[3] / "edge-data"  # backend/services/edge_store.py dung cung thu muc
_REPLACE_TRIES = 50  # Windows: os.replace loi khi tien trinh kia dang mo file de doc; thu lai sau 10 ms

# idle: khong co phien. monitoring: dang nhan frame. paused: giao vien tam dung.
# unavailable: phien dang chay nhung camera khong cho frame hoac chua nap duoc so do ghe (UC02).
# outside_schedule: phien dang chay ngoai cua so lich trong cai dat, camera khong bat.
EDGE_STATUSES = frozenset({"idle", "monitoring", "paused", "unavailable", "outside_schedule"})

# ``status`` web admin ghi (scheduled -> running <-> paused -> completed, hoac cancelled) ->
# trang thai EdgeRuntime dung. Gia tri khac giu nguyen: ``paused`` van chay duoc;
# ``scheduled``/``cancelled`` khong phai phien song. "live"/"ended" la ten cu, van nhan.
WEB_STATUS_TO_STATE = {"running": "active", "completed": "ended", "live": "active", "ended": "ended"}


@dataclass(frozen=True)
class EdgeHeartbeat:
    """Trang thai thiet bi, khong co du lieu hoc sinh. Thoi gian la wall-clock UTC; web coi edge
    offline neu ``updated_at`` qua cu."""

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


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Khong ghi duoc {type(value).__name__} ra JSON.")


def _private(path: Path, flags: int) -> int:
    """Mo file moi chi chu tai khoan doc duoc (0o600) ngay tu luc tao; Windows bo qua mode (ACL: README)."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return os.open(path, os.O_WRONLY | os.O_CREAT | flags | getattr(os, "O_BINARY", 0), 0o600)


def write_json(path: Path, data: Any) -> None:
    """Ghi de nguyen tu: ben doc khong bao gio thay file ghi do."""
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with os.fdopen(_private(tmp, os.O_EXCL), "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, default=_json_default))
    for attempt in range(_REPLACE_TRIES):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == _REPLACE_TRIES - 1:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.01)


def append_jsonl(path: Path, data: Any) -> None:
    with os.fdopen(_private(path, os.O_APPEND), "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, default=_json_default) + "\n")


def read_json(path: Path) -> Any:
    """Noi dung file, None khi chua co. File hong (sua tay) -> ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def cameras(root: Path) -> dict[str, dict]:
    """{camera_id: cameras/{camera_id}.json} cua cac camera admin them tren trang Quan ly camera."""
    found = {}
    for path in sorted((root / "cameras").glob("*.json")):
        data = read_json(path)
        if isinstance(data, dict):  # None: vua bi xoa tren web
            found[path.stem] = data
    return found


def camera_source(root: Path, camera_id: str) -> str | None:
    """URL RTSP admin nhap tren web (kem mat khau: khong log, khong ghi ra dau); None khi chua co."""
    source = (read_json(root / "cameras" / f"{camera_id}.json") or {}).get("source")
    return source if isinstance(source, str) and source.strip() else None


def camera_session(root: Path, camera_id: str) -> dict | None:
    """Tiet hien tai cua camera do web admin ghi luc bat dau tiet, None khi camera chua co tiet nao."""
    data = read_json(root / "camera_sessions" / f"{camera_id}.json")
    return data if isinstance(data, dict) else None


def session_states(order: dict | None) -> dict[str, str | None]:
    """{session_id: trang thai cho EdgeRuntime} tu file tiet hien tai; ``status`` khong phai chuoi (file
    sua tay hong) -> None, tuc khong phai phien song; session_id sai -> khong co phien."""
    if not order:
        return {}
    try:
        session_id = check_session_id(order.get("session_id"))
    except ValueError:
        return {}
    status = order.get("status")
    return {session_id: WEB_STATUS_TO_STATE.get(status, status) if isinstance(status, str) else None}


def prune_sessions(root: Path, retention_days: int, now: Callable[[], float] = time.time) -> int:
    """Xoa du lieu cac tiet khong co file nao moi hon ``retention_days`` ngay. Tra so tiet da xoa."""
    cutoff, removed = now() - retention_days * 86400, 0
    for directory in (root / "sessions").glob("*"):
        try:
            if directory.is_dir() and max((f.stat().st_mtime for f in directory.iterdir()), default=0) < cutoff:
                shutil.rmtree(directory)
                removed += 1
        except OSError as error:  # web dang doc file cua tiet: lan sau xoa
            logger.warning("Chua xoa duoc du lieu tiet cu (%s).", type(error).__name__)
    return removed


class LocalSink:
    """Ghi output cua edge node camera ``camera_id`` vao ``root``. Chi nhan schema allowlist o ``privacy/``
    va ``EdgeHeartbeat``. Ghi ngay luc goi (vai ms moi file), du nhanh cho vong lap frame: ket qua va window
    moi 10 s, heartbeat toi da 10 s/lan. Loi dia (day, bi khoa) chi log ten loi va dem ``dropped``."""

    def __init__(self, root: Path, camera_id: str) -> None:
        if not isinstance(camera_id, str) or not camera_id.strip() or any(c in camera_id for c in "/\\"):
            raise ValueError("camera_id phai la chuoi khong rong, khong chua '/' hay '\\'.")
        self.root = Path(root)
        self.dropped = 0
        self._camera_id = camera_id

    def add_alert(self, alert: AlertEvent) -> None:
        if not isinstance(alert, AlertEvent):
            raise TypeError("Chi nhan AlertEvent (schema allowlist).")
        # id sinh 1 lan: web dung no de danh dau da xu ly (handled_alerts.json)
        self._write(
            append_jsonl, self._session(alert.session_id) / "alerts.jsonl", {"id": uuid.uuid4().hex, **alert.to_dict()}
        )

    def add_window(self, window: SessionWindow) -> None:
        if not isinstance(window, SessionWindow):
            raise TypeError("Chi nhan SessionWindow (schema allowlist).")
        self._write(append_jsonl, self._session(window.session_id) / "windows.jsonl", window.to_dict())

    def set_result(self, result: SessionResult) -> None:
        if not isinstance(result, SessionResult):
            raise TypeError("Chi nhan SessionResult (schema allowlist).")
        self._write(write_json, self._session(result.session_id) / "result.json", result.to_dict())

    def set_evaluations(self, evaluations: Iterable[SeatEvaluation]) -> None:
        """Ghi de tong hop cua tung ghe; ghe chi thay o lan chay truoc cua tiet (edge chay lai) duoc giu."""
        evaluations = list(evaluations)
        if not all(isinstance(evaluation, SeatEvaluation) for evaluation in evaluations):
            raise TypeError("Chi nhan SeatEvaluation (schema allowlist).")
        by_session = defaultdict(dict)
        for evaluation in evaluations:
            by_session[evaluation.session_id][evaluation.seat_id] = evaluation.to_dict()
        for session_id, seats in by_session.items():
            path = self._session(session_id) / "evaluations.json"
            self._write(lambda p, new: write_json(p, {**(read_json(p) or {}), **new}), path, seats)

    def set_heartbeat(self, heartbeat: EdgeHeartbeat) -> None:
        if not isinstance(heartbeat, EdgeHeartbeat):
            raise TypeError("Chi nhan EdgeHeartbeat.")
        self._write(write_json, self.root / "edge_nodes" / f"{self._camera_id}.json", heartbeat.to_dict())

    def result_exists(self, session_id: str) -> bool:
        """Da co ket qua cua phien nay chua (vd tien trinh truoc chet giua phien)."""
        return (self._session(session_id) / "result.json").exists()

    def _session(self, session_id: str) -> Path:
        return self.root / "sessions" / check_session_id(session_id)

    def _write(self, write: Callable[[Path, Any], None], path: Path, data: Any) -> None:
        try:
            write(path, data)
        except (OSError, ValueError) as error:  # chi ten loi va bo dem: khong log noi dung
            self.dropped += 1
            logger.error("Khong ghi duoc %s (%s), da bo %d lan ghi.", path.name, type(error).__name__, self.dropped)
