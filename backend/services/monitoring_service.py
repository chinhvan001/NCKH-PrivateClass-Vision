"""Phía web của hợp đồng với edge node camera-ai (camera-ai/docs/web_admin_integration.md).

Camera AI chạy cùng máy và trao đổi với web qua file trong edge-data/ (services/edge_store.py), không qua
Firestore. Lúc bắt đầu tiết, web giao tiết cho camera của lớp kèm sơ đồ ghế và ô ghế vẽ trên trang Quản lý
camera; mỗi lần đổi trạng thái tiết, web báo lại. Edge node ghi kết quả, đánh giá theo ghế, cảnh báo và
heartbeat; web đọc lại, ghi thêm trạng thái xử lý cảnh báo, và xóa chúng khi xóa tiết.
"""

from datetime import datetime, timedelta, timezone

from routes.test_helpers import commit_writes, db, json_value, server_timestamp
from services import edge_store

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
    "no_seat_regions": "Camera của lớp chưa được xác định chỗ ngồi: vào Quản lý camera, chọn Xác định chỗ ngồi.",
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
    """monitoring_status của kết quả camera AI ghi cho tiết, None nếu chưa có kết quả nào."""
    return (edge_store.result(session_id) or {}).get("monitoring_status")


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


def edge_status(camera_id):
    """Heartbeat của edge node của camera, None nếu camera chưa có edge node chạy."""
    data = edge_store.heartbeat(camera_id) if camera_id else None
    if not isinstance(data, dict) or not isinstance(data.get("updated_at"), datetime):
        return None
    fields = ("status", "session_id", "fps", "camera_ok", "last_frame_at", "updated_at")
    return {"camera_id": camera_id, "online": is_online(data), **json_value({key: data.get(key) for key in fields})}


def check_start(session_id, session, force=False):
    """Kiểm tra trước khi bắt đầu giám sát (UC04 bước 3). Trả (dữ liệu lớp, ô ghế của camera, mã lỗi hoặc None).

    force=True cho bắt đầu khi edge node offline: edge node nhận tiết ngay khi chạy lại."""
    class_id = session.get("class_id")
    if not class_id:
        return {}, None, "no_seat_plan"
    for doc in db.collection("sessions").where("class_id", "==", class_id).stream():
        # ponytail: không khóa giao dịch, 2 admin bấm cùng lúc vẫn lọt; edge node khi đó chọn tiết có id nhỏ nhất
        if doc.id != session_id and (doc.to_dict() or {}).get("status") in LIVE_STATUSES:
            return {}, None, "class_busy"
    class_doc = db.collection("classes2").document(class_id).get()
    class_data = (class_doc.to_dict() or {}) if class_doc.exists else {}
    if grid_size(class_data) is None:
        return class_data, None, "no_seat_plan"
    camera_id = class_data.get("camera_id")
    regions_doc = db.collection("seat_regions").document(camera_id).get() if camera_id else None
    regions = (regions_doc.to_dict() or {}) if regions_doc is not None and regions_doc.exists else None
    if camera_id and (regions is None or regions.get("class_id") != class_id):
        # camera AI chỉ lấy vị trí ghế từ ô vẽ trên web cho đúng lớp này
        return class_data, None, "no_seat_regions"
    edge = edge_status(camera_id)
    if not force and not (edge and edge["online"]):
        return class_data, regions, "edge_offline"
    return class_data, regions, None


def publish_status(session, session_id, status):
    """Báo camera AI của tiết (camera chốt lúc bắt đầu) rằng tiết đổi trạng thái."""
    edge_store.set_session_status(session.get("camera_id"), session_id, status)


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
                publish_status(session, doc.id, "completed")
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
    alerts = sorted(edge_store.alerts(session_id), key=lambda alert: alert.get("start_sec") or 0, reverse=True)
    return [json_value(alert) for alert in alerts[:limit]]


def session_camera(session):
    """Camera của tiết: camera chốt lúc bắt đầu, tiết chưa bắt đầu thì camera hiện tại của lớp."""
    if session.get("camera_id"):
        return session["camera_id"]
    class_id = session.get("class_id")
    class_doc = db.collection("classes2").document(class_id).get(field_paths=["camera_id"]) if class_id else None
    return (class_doc.to_dict() or {}).get("camera_id") if class_doc is not None and class_doc.exists else None


def live_view(session_id):
    """Trạng thái tiết, heartbeat, kết quả trực tiếp và cảnh báo mới nhất (UC07, UC09), None nếu không có tiết."""
    session_doc = db.collection("sessions").document(session_id).get()
    if not session_doc.exists:
        return None
    session = session_doc.to_dict() or {}
    result = edge_store.result(session_id)
    return {
        "session": {"id": session_id, **json_value(session)},
        "edge": edge_status(session_camera(session)),
        "result": json_value(result) if result else None,
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
    """Xóa tiết cùng dữ liệu của nó: kết quả, đánh giá, window 10 s và cảnh báo của camera AI, bản chốt ghế,
    báo cáo phụ huynh. Trả "not_found", "live" (đang giám sát, phải kết thúc trước) hoặc None khi đã xóa."""
    session_ref = db.collection("sessions").document(session_id)
    session_doc = session_ref.get()
    if not session_doc.exists:
        return "not_found"
    if (session_doc.to_dict() or {}).get("status") in LIVE_STATUSES:
        return "live"
    students = set((roster_data(session_id) or {}).values())
    collection = session_ref.collection(MONITORED_STUDENTS)
    writes = [(collection.document(doc.id), None) for doc in collection.stream()]
    writes += [
        (db.collection("students2").document(student_id).collection("reports").document(session_id), None)
        for student_id in students
    ]
    # session_rosters: bản chốt ghế kiểu cũ (trước monitored_students), xóa nếu còn
    writes.append((db.collection("session_rosters").document(session_id), None))
    commit_writes(writes)
    edge_store.delete_session(session_id)
    session_ref.delete()  # xóa sau cùng: lỗi giữa chừng thì tiết vẫn còn để xóa lại
    return None


def clean_seat_regions(data):
    """Ô ghế admin vẽ trên ảnh chụp từ camera, lưu ở seat_regions/{camera_id}; lúc bắt đầu tiết web chép chúng vào
    tiết giao cho camera AI (camera-ai/src/config/class_layout.py). seats: {seat_id: [x1, y1, x2, y2]} theo pixel.
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
    return edge_store.handle_alert(session_id, alert_id, status, uid, utc_now())
