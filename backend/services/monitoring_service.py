"""Phía web của hợp đồng Firestore với edge node camera-ai (camera-ai/docs/web_admin_integration.md).

Edge node nghe sessions có class_id của lớp và ghi session_results/{s}, session_evaluations/{s}_{seat},
sessions/{s}/alerts/{id} và edge_nodes/{camera_id}. Web chỉ đọc các document đó; riêng cảnh báo,
web ghi thêm status, handled_by, handled_at khi xử lý.
"""

from datetime import datetime, timezone

from firebase_admin import firestore

from routes.test_helpers import db, json_document, json_value, server_timestamp

EDGE_STALE_SEC = 30  # edge node gửi heartbeat 10 s/lần
MAX_GRID_SIDE = 50  # edge node từ chối sơ đồ lớn hơn
LIVE_STATUSES = ("running", "paused")  # edge node coi cả hai là tiết đang giám sát
ALERT_STATUSES = {"acknowledged", "dismissed"}
ALERT_LIMIT = 20
EMPTY_STUDENT_IDS = (None, "", "None", "null", "undefined")

START_PROBLEMS = {
    "class_busy": "Lớp đang có một tiết khác được giám sát. Hãy kết thúc tiết đó trước.",
    "no_seat_plan": f"Lớp chưa có sơ đồ chỗ ngồi hợp lệ (1–{MAX_GRID_SIDE} hàng và cột).",
    "edge_offline": "Camera AI của lớp đang offline hoặc chưa được cài đặt.",
}


def utc_now():
    return datetime.now(timezone.utc)


def seat_id(row, column, column_count):
    """Giống ensure_class_seats và edge node: S01, S02... đánh số theo từng hàng."""
    return f"S{(row - 1) * column_count + column:02d}"


def grid_size(class_data):
    """(số hàng, số cột) mà edge node dùng được, hoặc None."""
    size = (class_data.get("row_count"), class_data.get("column_count"))
    if all(isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_GRID_SIDE for value in size):
        return size
    return None


def seat_assignments(class_data):
    """seat_map của lớp -> {seat_id: student_id}, chỉ các ghế đã xếp học sinh."""
    return {
        seat: info["student_id"]
        for seat, info in (class_data.get("seat_map") or {}).items()
        if isinstance(info, dict) and info.get("student_id") not in EMPTY_STUDENT_IDS
    }


def roster(session_id, class_data):
    """Ghế -> học sinh của tiết: bản chốt lúc bắt đầu, nếu không có thì seat_map hiện tại của lớp."""
    doc = db.collection("session_rosters").document(session_id).get()
    if doc.exists:
        return (doc.to_dict() or {}).get("seats") or {}
    return seat_assignments(class_data)


def is_online(heartbeat):
    """Offline khi edge node tự báo tắt hoặc quá EDGE_STALE_SEC không gửi heartbeat (đồng hồ edge cần NTP)."""
    updated_at = heartbeat.get("updated_at")
    return (
        heartbeat.get("online") is True
        and isinstance(updated_at, datetime)
        and (utc_now() - updated_at).total_seconds() <= EDGE_STALE_SEC
    )


def edge_status(class_id):
    """Heartbeat mới nhất của edge node gắn với lớp, None nếu lớp chưa có edge node."""
    nodes = [
        (doc.id, doc.to_dict() or {}) for doc in db.collection("edge_nodes").where("class_id", "==", class_id).stream()
    ]
    nodes = [(camera_id, data) for camera_id, data in nodes if isinstance(data.get("updated_at"), datetime)]
    if not nodes:
        return None
    camera_id, data = max(nodes, key=lambda node: node[1]["updated_at"])
    fields = ("status", "session_id", "fps", "camera_ok", "last_frame_at", "updated_at")
    return {"camera_id": camera_id, "online": is_online(data), **json_value({key: data.get(key) for key in fields})}


def check_start(session_id, session, force=False):
    """Kiểm tra trước khi bắt đầu giám sát (UC04 bước 3). Trả (dữ liệu lớp, mã lỗi hoặc None).

    force=True cho bắt đầu khi edge node offline: edge node nhận tiết ngay khi chạy lại."""
    class_id = session.get("class_id")
    if not class_id:
        return {}, "no_seat_plan"
    for doc in db.collection("sessions").where("class_id", "==", class_id).stream():
        # ponytail: không khóa giao dịch, 2 admin bấm cùng lúc vẫn lọt; edge node khi đó chọn tiết có id nhỏ nhất
        if doc.id != session_id and (doc.to_dict() or {}).get("status") in LIVE_STATUSES:
            return {}, "class_busy"
    class_doc = db.collection("classes2").document(class_id).get()
    class_data = (class_doc.to_dict() or {}) if class_doc.exists else {}
    if grid_size(class_data) is None:
        return class_data, "no_seat_plan"
    edge = edge_status(class_id)
    if not force and not (edge and edge["online"]):
        return class_data, "edge_offline"
    return class_data, None


def freeze_roster(session_id, class_id, class_data):
    """Chốt ghế -> học sinh lúc bắt đầu, để báo cáo của tiết không đổi khi sơ đồ lớp đổi sau đó."""
    db.collection("session_rosters").document(session_id).set(
        {"class_id": class_id, "seats": seat_assignments(class_data), "created_at": server_timestamp()}
    )


def recent_alerts(session_id, limit=ALERT_LIMIT):
    query = (
        db.collection("sessions")
        .document(session_id)
        .collection("alerts")
        .order_by("start_sec", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [json_document(doc) for doc in query.stream()]


def live_view(session_id):
    """Trạng thái tiết, heartbeat, kết quả trực tiếp và cảnh báo mới nhất (UC07, UC09), None nếu không có tiết."""
    session_doc = db.collection("sessions").document(session_id).get()
    if not session_doc.exists:
        return None
    session = session_doc.to_dict() or {}
    result_doc = db.collection("session_results").document(session_id).get()
    return {
        "session": {"id": session_id, **json_value(session)},
        "edge": edge_status(session.get("class_id")),
        "result": json_value(result_doc.to_dict() or {}) if result_doc.exists else None,
        "alerts": recent_alerts(session_id),
    }


def seat_plan(session_id):
    """Sơ đồ ghế của tiết kèm tên học sinh, theo bản chốt; None nếu không có tiết."""
    session_doc = db.collection("sessions").document(session_id).get()
    if not session_doc.exists:
        return None
    class_id = (session_doc.to_dict() or {}).get("class_id")
    class_doc = db.collection("classes2").document(class_id).get() if class_id else None
    class_data = (class_doc.to_dict() or {}) if class_doc and class_doc.exists else {}
    size = grid_size(class_data)
    if size is None:
        return {"row_count": 0, "column_count": 0, "seats": []}
    rows, columns = size
    seats = roster(session_id, class_data)
    names = {}
    for student_id in set(seats.values()):
        doc = db.collection("students2").document(student_id).get(field_paths=["full_name"])
        names[student_id] = (doc.to_dict() or {}).get("full_name", "") if doc.exists else ""
    plan = []
    for row in range(1, rows + 1):
        for column in range(1, columns + 1):
            student_id = seats.get(seat_id(row, column, columns))
            plan.append(
                {
                    "seat_id": seat_id(row, column, columns),
                    "row": row,
                    "column": column,
                    "student_id": student_id,
                    "student_name": names.get(student_id, ""),
                }
            )
    return {"row_count": rows, "column_count": columns, "seats": plan}


def handle_alert(session_id, alert_id, status, uid):
    """Ghi nhận đã xử lý cảnh báo (UC09). False nếu không có cảnh báo đó."""
    ref = db.collection("sessions").document(session_id).collection("alerts").document(alert_id)
    if not ref.get().exists:
        return False
    ref.update({"status": status, "handled_by": uid, "handled_at": server_timestamp()})
    return True
