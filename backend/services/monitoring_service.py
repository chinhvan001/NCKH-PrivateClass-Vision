"""Phía web của hợp đồng Firestore với edge node camera-ai (camera-ai/docs/web_admin_integration.md).

Edge node nghe sessions có class_id của lớp và ghi session_results/{s}, session_evaluations/{s}_{seat},
sessions/{s}/alerts/{id} và edge_nodes/{camera_id}. Web chỉ đọc các document đó; riêng cảnh báo,
web ghi thêm status, handled_by, handled_at khi xử lý, và xóa chúng khi xóa tiết. Edge node đọc
seat_regions/{camera_id} (ô ghế admin vẽ trên trang Quản lý camera) lúc bắt đầu tiết.
"""

from datetime import datetime, timedelta, timezone

from firebase_admin import firestore

from routes.test_helpers import commit_writes, db, json_document, json_value, server_timestamp

EDGE_STALE_SEC = 30  # edge node gửi heartbeat 10 s/lần
MAX_GRID_SIDE = 50  # edge node từ chối sơ đồ lớn hơn
MAX_IMAGE_SIDE = 10000  # ảnh chụp từ camera để vẽ ô ghế
LIVE_STATUSES = ("running", "paused")  # edge node coi cả hai là tiết đang giám sát
# monitored_student của sơ đồ đã chốt: subcollection của tiết (không phải map trong document tiết), vì edge
# node nghe document tiết và không được thấy mã học sinh (camera-ai/docs/backend_scoring_and_schema_proposal.md)
MONITORED_STUDENTS = "monitored_students"
ALERT_TYPES = ("head_drop", "back_turn", "side_conversation")
ALERT_STATUSES = {"acknowledged", "dismissed"}
ALERT_LIMIT = 20
EMPTY_STUDENT_IDS = (None, "", "None", "null", "undefined")
# Edge node mất mạng lúc kết thúc tiết thì chốt kết quả muộn: chờ tối đa chừng này rồi coi là gián đoạn.
FINALIZE_WAIT_SEC = 1800
# Giáo viên quên bấm Kết thúc: job tự kết thúc tiết sau giờ kết thúc theo thời khóa biểu chừng này, để camera
# không quay lớp học sau giờ học. Giờ trong thời khóa biểu là giờ Việt Nam (UTC+7, không đổi theo mùa).
FORGOTTEN_AFTER_SEC = 1800
SCHOOL_TZ = timezone(timedelta(hours=7))

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


def monitored_students(session_id):
    return db.collection("sessions").document(session_id).collection(MONITORED_STUDENTS)


def roster_data(session_id):
    """Ghế -> học sinh chốt lúc tiết bắt đầu (sessions/{s}/monitored_students/{ghế}), None nếu chưa chốt."""
    seats = {doc.id: (doc.to_dict() or {}).get("student_id") for doc in monitored_students(session_id).stream()}
    return {seat: student_id for seat, student_id in seats.items() if student_id} or None


def roster(session_id, class_data):
    """Ghế -> học sinh của tiết: bản chốt lúc bắt đầu, nếu không có thì seat_map hiện tại của lớp."""
    seats = roster_data(session_id)
    return seats if seats is not None else seat_assignments(class_data)


def result_status(session_id):
    """monitoring_status của session_results/{s}, None nếu camera AI chưa ghi kết quả nào."""
    doc = db.collection("session_results").document(session_id).get(field_paths=["monitoring_status"])
    return (doc.to_dict() or {}).get("monitoring_status") if doc.exists else None


def data_status(session, monitoring_status):
    """Dữ liệu camera AI của một tiết: "live" (đang giám sát), "pending" (camera AI chưa chốt),
    "complete", "partial" (tiết bị gián đoạn: chỉ có một phần) hoặc "no_data"."""
    if session.get("status") in LIVE_STATUSES:
        return "live"
    if monitoring_status is None:
        return "no_data"
    if monitoring_status == "completed":
        return "complete"
    if monitoring_status == "running":  # tiết đã kết thúc mà edge node chưa chốt
        ended_at = session.get("ended_at")
        if isinstance(ended_at, datetime) and (utc_now() - ended_at).total_seconds() < FINALIZE_WAIT_SEC:
            return "pending"
    return "partial"


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


def close_forgotten_sessions():
    """Kết thúc các tiết còn running/paused quá FORGOTTEN_AFTER_SEC sau end_time của ngày session_date: camera AI
    tắt camera và chốt kết quả như khi bấm Kết thúc. Tiết thiếu session_date/end_time dạng chuỗi thì bỏ qua.
    Trả danh sách ID tiết đã kết thúc."""
    closed = []
    for status in LIVE_STATUSES:
        for doc in db.collection("sessions").where("status", "==", status).stream():
            session = doc.to_dict() or {}
            try:
                end = datetime.fromisoformat(f"{session['session_date']}T{session['end_time']}").replace(tzinfo=SCHOOL_TZ)
            except (KeyError, TypeError, ValueError):
                continue
            if (utc_now() - end).total_seconds() > FORGOTTEN_AFTER_SEC:
                db.collection("sessions").document(doc.id).update({"status": "completed", "ended_at": server_timestamp()})
                closed.append(doc.id)
    return closed


def freeze_roster(session_id, class_data):
    """Chốt ghế -> học sinh lúc bắt đầu, để báo cáo của tiết không đổi khi sơ đồ lớp đổi sau đó. Worker tính
    điểm (gói A) ghi thêm is_present, attention_score, is_attention vào cùng document khi tiết kết thúc."""
    seat_map = class_data.get("seat_map") or {}
    students = monitored_students(session_id)
    commit_writes([
        (
            students.document(seat),
            {"student_id": student_id, "row": seat_map[seat].get("row"), "column": seat_map[seat].get("column")},
        )
        for seat, student_id in seat_assignments(class_data).items()
    ])


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
    session = session_doc.to_dict() or {}
    class_id = session.get("class_id")
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
    return {
        "row_count": rows,
        "column_count": columns,
        "seats": plan,
        # Job báo cáo phụ huynh ghi 2 field này vào tiết sau khi tiết kết thúc (services/report_service.py)
        "report_count": session.get("report_count"),
        "reports_at": json_value(session.get("reports_at")),
    }


def delete_session(session_id):
    """Xóa tiết cùng dữ liệu của nó: cảnh báo, kết quả, đánh giá và window 10 s của camera AI, bản chốt ghế,
    báo cáo phụ huynh. Trả "not_found", "live" (đang giám sát, phải kết thúc trước) hoặc None khi đã xóa."""
    session_ref = db.collection("sessions").document(session_id)
    session_doc = session_ref.get()
    if not session_doc.exists:
        return "not_found"
    if (session_doc.to_dict() or {}).get("status") in LIVE_STATUSES:
        return "live"
    students = set((roster_data(session_id) or {}).values())
    writes = []
    for name in ("alerts", MONITORED_STUDENTS):
        collection = session_ref.collection(name)
        writes += [(collection.document(doc.id), None) for doc in collection.stream()]
    for name in ("session_evaluations", "session_windows"):
        collection = db.collection(name)
        writes += [(collection.document(doc.id), None) for doc in collection.where("session_id", "==", session_id).stream()]
    writes += [
        (db.collection("students2").document(student_id).collection("reports").document(session_id), None)
        for student_id in students
    ]
    # session_rosters: bản chốt ghế kiểu cũ (trước monitored_students), xóa nếu còn
    writes += [(db.collection(name).document(session_id), None) for name in ("session_results", "session_rosters")]
    commit_writes(writes)
    # ponytail: edge node mất mạng mà vẫn tưởng tiết đang chạy sẽ ghi lại kết quả khi có mạng;
    # các document đó có expire_at nên TTL của Firestore dọn được
    session_ref.delete()  # xóa sau cùng: lỗi giữa chừng thì tiết vẫn còn để xóa lại
    return None


def clean_seat_regions(data):
    """Ô ghế admin vẽ trên ảnh chụp từ camera, lưu ở seat_regions/{camera_id}; edge node đọc lại lúc bắt đầu
    tiết (camera-ai/src/config/class_layout.py). seats: {seat_id: [x1, y1, x2, y2]} theo pixel của ảnh.
    Trả (document để lưu, None) hoặc (None, thông báo lỗi)."""
    class_id = data.get("class_id")
    class_doc = db.collection("classes2").document(class_id).get() if isinstance(class_id, str) and class_id else None
    size = grid_size(class_doc.to_dict() or {}) if class_doc is not None and class_doc.exists else None
    if size is None:
        return None, START_PROBLEMS["no_seat_plan"]
    width, height = data.get("image_width"), data.get("image_height")
    if not all(isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= MAX_IMAGE_SIDE for v in (width, height)):
        return None, "Kích thước ảnh không hợp lệ."
    seats = data.get("seats")
    if not isinstance(seats, dict):
        return None, "Danh sách ô ghế không hợp lệ."
    rows, columns = size
    seat_ids = {seat_id(row, column, columns) for row in range(1, rows + 1) for column in range(1, columns + 1)}
    cleaned = {}
    for seat, box in seats.items():
        if seat not in seat_ids:
            return None, f"Ghế {seat} không có trong sơ đồ lớp."
        if not (
            isinstance(box, list)
            and len(box) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in box)
            and 0 <= box[0] < box[2] <= width
            and 0 <= box[1] < box[3] <= height
        ):
            return None, f"Ô của ghế {seat} không hợp lệ hoặc nằm ngoài ảnh."
        cleaned[seat] = [round(float(v), 1) for v in box]
    return {"class_id": class_id, "image_width": width, "image_height": height, "seats": cleaned}, None


def handle_alert(session_id, alert_id, status, uid):
    """Ghi nhận đã xử lý cảnh báo (UC09). False nếu không có cảnh báo đó."""
    ref = db.collection("sessions").document(session_id).collection("alerts").document(alert_id)
    if not ref.get().exists:
        return False
    ref.update({"status": status, "handled_by": uid, "handled_at": server_timestamp()})
    return True
