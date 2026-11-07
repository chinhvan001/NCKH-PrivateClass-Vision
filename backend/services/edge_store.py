"""Thư mục chung với camera AI trên cùng máy (edge-data/ ở gốc repo; camera-ai/src/sync/local_store.py).

Web admin và camera AI luôn chạy trên một máy nên trao đổi qua file JSON thay cho Firestore: kết quả 10 s/lần,
window, cảnh báo và heartbeat không tốn lượt ghi miễn phí của Firebase, URL camera kèm mật khẩu không lên cloud.

Web ghi, camera AI đọc:
- cameras/{camera_id}.json: angle_type, source (URL RTSP kèm mật khẩu; API không bao giờ trả về).
- camera_sessions/{camera_id}.json: tiết hiện tại của camera, ghi lúc bắt đầu tiết và mỗi lần đổi trạng thái:
  session_id, status, class_id, row_count, column_count, seat_regions (ô ghế vẽ trên web, chốt lúc bắt đầu).

Camera AI ghi, web đọc:
- edge_nodes/{camera_id}.json: heartbeat.
- sessions/{s}/result.json, evaluations.json ({seat_id: ...}), windows.jsonl, alerts.jsonl (mỗi dòng một bản ghi).
Web ghi thêm sessions/{s}/handled_alerts.json (cảnh báo đã xử lý) và kết quả của worker tính điểm.
"""

import json
import os
import re
import shutil
import threading
import time
import uuid
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "edge-data"  # camera AI dùng cùng thư mục
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")  # như camera AI: ID tự sinh của Firestore đều khớp
# Tên camera là tên file: không ký tự Windows cấm, không cách/chấm ở hai đầu, không tên thiết bị (CON, COM1...)
_BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_LOCK = threading.Lock()  # đọc-sửa-ghi trong backend (Flask nhiều luồng)


def valid_camera_id(camera_id):
    return (
        isinstance(camera_id, str)
        and 0 < len(camera_id) <= 100
        and camera_id == camera_id.strip(" .")
        and not _BAD_CHARS.search(camera_id)
        and camera_id.split(".")[0].upper() not in _RESERVED
    )


def _camera_path(kind, camera_id):
    if not valid_camera_id(camera_id):
        raise ValueError("Tên camera không dùng được làm tên file.")
    return ROOT / kind / f"{camera_id}.json"


def _session_dir(session_id):
    """None với ID camera AI không nhận (tiết đó không bao giờ có dữ liệu camera AI)."""
    return ROOT / "sessions" / session_id if isinstance(session_id, str) and SESSION_ID.fullmatch(session_id) else None


def _parse_times(data):
    """Thời gian camera AI ghi dạng ISO (captured_at, updated_at, ...) -> datetime, như Firestore trả về."""
    for key, value in data.items():
        if key.endswith("_at") and isinstance(value, str):
            try:
                data[key] = datetime.fromisoformat(value)
            except ValueError:
                pass
    return data


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Không ghi được {type(value).__name__} ra JSON.")


def read(path):
    """Nội dung file, None khi chưa có hoặc hỏng (sửa tay)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_hook=_parse_times)
    except (FileNotFoundError, ValueError):
        return None


def read_lines(path):
    """Các dòng JSONL; dòng cuối camera AI đang ghi dở thì bỏ qua."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    rows = []
    for line in text.splitlines():
        try:
            rows.append(json.loads(line, object_hook=_parse_times))
        except ValueError:
            continue
    return rows


def write(path, data):
    """Ghi đè nguyên tử: camera AI không bao giờ đọc phải file ghi dở. File tạo ra chỉ chủ tài khoản đọc được
    (0o600; Windows bỏ qua mode, thư mục edge-data/ dùng ACL: camera-ai/src/sync/README.md)."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, default=_json_default))
    for attempt in range(50):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:  # Windows: camera AI đang mở file để đọc
            if attempt == 49:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.01)


# --- Web ghi cho camera AI ---


def camera(camera_id):
    """{angle_type, source} của camera, None nếu chưa có."""
    return read(_camera_path("cameras", camera_id)) if valid_camera_id(camera_id) else None


def save_camera(camera_id, angle_type, source):
    write(_camera_path("cameras", camera_id), {"angle_type": angle_type, "source": source})


def delete_camera(camera_id):
    """Camera AI dừng edge node của camera trong 30 s; heartbeat cuối của nó vẫn còn nhưng không được liệt kê."""
    for kind in ("cameras", "camera_sessions"):
        _camera_path(kind, camera_id).unlink(missing_ok=True)


def assign_session(camera_id, session_id, class_id, size, regions):
    """Giao tiết cho camera lúc bắt đầu: sơ đồ ghế và ô ghế chốt cho cả tiết, như monitored_students."""
    rows, columns = size
    seat_regions = {key: regions.get(key) for key in ("image_width", "image_height", "seats")} if regions else None
    order = {
        "session_id": session_id,
        "status": "running",
        "class_id": class_id,
        "row_count": rows,
        "column_count": columns,
        "seat_regions": seat_regions,
    }
    write(_camera_path("camera_sessions", camera_id), order)


def set_session_status(camera_id, session_id, status):
    """Báo camera AI tiết đổi trạng thái (paused, running, completed). Bỏ qua khi camera đã sang tiết khác."""
    if not valid_camera_id(camera_id):
        return
    path = _camera_path("camera_sessions", camera_id)
    with _LOCK:  # ponytail: chỉ khóa trong tiến trình; job báo cáo tự kết thúc tiết thì chạy ở tiến trình khác
        order = read(path)
        if order and order.get("session_id") == session_id:
            write(path, {**order, "status": status})


# --- Camera AI ghi cho web ---


def heartbeat(camera_id):
    return read(_camera_path("edge_nodes", camera_id)) if valid_camera_id(camera_id) else None


def heartbeats():
    """{camera_id: heartbeat} của mọi edge node từng chạy trên máy."""
    nodes = {}
    for path in sorted((ROOT / "edge_nodes").glob("*.json")):
        data = read(path)
        if isinstance(data, dict):
            nodes[path.stem] = data
    return nodes


def session_file(session_id, name):
    directory = _session_dir(session_id)
    return read(directory / name) if directory else None


def write_session_file(session_id, name, data):
    directory = _session_dir(session_id)
    if directory is None:
        raise ValueError("session_id không hợp lệ.")
    write(directory / name, data)


def result(session_id):
    return session_file(session_id, "result.json")


def evaluations(session_id):
    """Đánh giá theo ghế của tiết (camera AI ghi 5 phút/lần và khi hết tiết)."""
    return list((session_file(session_id, "evaluations.json") or {}).values())


def all_evaluations():
    # ponytail: đọc mọi tiết còn trên máy mỗi lần mở trang; khi nhiều thì lọc theo ngày của tiết
    return [item for path in sorted((ROOT / "sessions").glob("*")) for item in evaluations(path.name)]


def windows(session_id):
    directory = _session_dir(session_id)
    return read_lines(directory / "windows.jsonl") if directory else []


def alerts(session_id):
    """Cảnh báo của tiết, kèm status, handled_by, handled_at nếu đã xử lý."""
    directory = _session_dir(session_id)
    if directory is None:
        return []
    handled = read(directory / "handled_alerts.json") or {}
    return [{**alert, **handled.get(alert.get("id"), {})} for alert in read_lines(directory / "alerts.jsonl")]


def handle_alert(session_id, alert_id, status, uid, handled_at):
    """False nếu tiết không có cảnh báo đó."""
    directory = _session_dir(session_id)
    if directory is None or not any(alert.get("id") == alert_id for alert in read_lines(directory / "alerts.jsonl")):
        return False
    with _LOCK:
        handled = read(directory / "handled_alerts.json") or {}
        handled[alert_id] = {"status": status, "handled_by": uid, "handled_at": handled_at}
        write(directory / "handled_alerts.json", handled)
    return True


def delete_session(session_id):
    """Xóa mọi dữ liệu camera AI của tiết."""
    directory = _session_dir(session_id)
    for attempt in range(5):
        try:
            if directory is not None:
                shutil.rmtree(directory)
            return
        except FileNotFoundError:
            return
        except PermissionError:  # Windows: camera AI hoặc job đang mở một file của tiết
            if attempt == 4:
                raise
            time.sleep(0.1)
