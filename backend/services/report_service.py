"""Báo cáo cho phụ huynh (UC03): students2/{student_id}/reports/{session_id}.

Job jobs/parent_reports.py gọi build_pending_reports() định kỳ: mỗi tiết kết thúc trong LOOKBACK_DAYS
ngày gần nhất được tạo báo cáo một lần, khi camera AI đã chốt kết quả, rồi đánh dấu reports_at và
report_count trong sessions/{s} (edge node nhận lại document tiết qua listener, chỉ thêm 1 lần đọc).
Một báo cáo chỉ có thông tin tiết học và kết quả của chính học sinh đó, không có seat_id hay học sinh khác.
"""

from collections import Counter
from datetime import timedelta

from routes.test_helpers import commit_writes, db, server_timestamp
from services import monitoring_service
from services.evaluation_service import level, usable

LOOKBACK_DAYS = 7


def build_session_reports(session_id, force=False):
    """Ghi báo cáo của tiết cho từng học sinh có dữ liệu. Trả số báo cáo đã ghi, hoặc None khi chưa tạo
    được: tiết chưa kết thúc, hoặc camera AI chưa chốt kết quả (force=True thì không chờ)."""
    session_doc = db.collection("sessions").document(session_id).get()
    session = (session_doc.to_dict() or {}) if session_doc.exists else {}
    if session.get("status") != "completed":
        return None
    status = monitoring_service.data_status(session, monitoring_service.result_status(session_id))
    if status == "pending" and not force:
        return None

    class_id = session.get("class_id")
    class_doc = db.collection("classes2").document(class_id).get() if class_id else None
    class_data = (class_doc.to_dict() or {}) if class_doc and class_doc.exists else {}
    seats = monitoring_service.roster_data(session_id)
    if seats is None:  # tiết bắt đầu trước khi có bản chốt: chốt sơ đồ hiện tại để báo cáo tạo lại vẫn như cũ
        monitoring_service.freeze_roster(session_id, class_data)
        seats = monitoring_service.seat_assignments(class_data)
    evaluations = {}
    for doc in db.collection("session_evaluations").where("session_id", "==", session_id).stream():
        evaluation = doc.to_dict() or {}
        evaluations[evaluation.get("seat_id")] = evaluation
    alerts = Counter()
    for doc in db.collection("sessions").document(session_id).collection("alerts").stream():
        alert = doc.to_dict() or {}
        alerts[(alert.get("seat_id"), alert.get("type"))] += 1

    writes = []
    for seat, student_id in seats.items():
        evaluation = evaluations.get(seat)
        if evaluation is None or not usable(evaluation):
            continue  # vắng, ngoài khung hình hoặc chỉ đi ngang qua: không có báo cáo
        report = {
            "session_id": session_id,
            "class_id": class_id,
            "class_name": class_data.get("class_name", ""),
            "subject": session.get("subject", ""),
            "session_date": session.get("session_date"),
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "avg_concentration": evaluation["avg_concentration"],
            "level": level(evaluation["avg_concentration"]),
            "observed_min": round(evaluation["observed_sec"] / 60),
            "alerts": {alert_type: alerts[(seat, alert_type)] for alert_type in monitoring_service.ALERT_TYPES},
            "partial": status != "complete",  # tiết bị gián đoạn: điểm chỉ phản ánh một phần tiết
            "created_at": server_timestamp(),
        }
        report_ref = db.collection("students2").document(student_id).collection("reports").document(session_id)
        writes.append((report_ref, report))

    commit_writes(writes)
    db.collection("sessions").document(session_id).update({"reports_at": server_timestamp(), "report_count": len(writes)})
    return len(writes)


def build_pending_reports():
    """Tạo báo cáo cho các tiết kết thúc trong LOOKBACK_DAYS ngày qua mà chưa có. Trả {session_id: số báo cáo}."""
    since = monitoring_service.utc_now() - timedelta(days=LOOKBACK_DAYS)
    built = {}
    for doc in db.collection("sessions").where("ended_at", ">=", since).stream():
        if "reports_at" in (doc.to_dict() or {}):
            continue
        count = build_session_reports(doc.id)
        if count is not None:
            built[doc.id] = count
    return built
