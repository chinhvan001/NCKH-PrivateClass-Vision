"""Báo cáo cho phụ huynh (UC03): students2/{student_id}/reports/{session_id}.

Job jobs/parent_reports.py gọi build_pending_reports() định kỳ: mỗi tiết kết thúc trong LOOKBACK_DAYS
ngày gần nhất được tạo báo cáo một lần, khi camera AI đã chốt kết quả, rồi đánh dấu reports_at và
report_count trong sessions/{s}.
Một báo cáo chỉ có thông tin tiết học và kết quả của chính học sinh đó, không có seat_id hay học sinh khác.
"""

from collections import Counter
from datetime import timedelta

from repositories.report_repository import ReportRepository
from routes.test_helpers import commit_writes, db, server_timestamp
from services import edge_store, monitoring_service, scoring_service
from services.evaluation_service import level, usable

LOOKBACK_DAYS = 7


class ReportService:
    @staticmethod
    def get_reports_overview(query_params):
        raw_reports = ReportRepository.get_all_reports()
        
        total = len(raw_reports)
        # Thống kê theo môn học
        subject_stats = {}
        for r in raw_reports:
            subj = r.get('subject', 'Khác')
            subject_stats[subj] = subject_stats.get(subj, 0) + 1

        return {
            "success": True,
            "stats": {
                "total": total,
                "subjects": subject_stats
            },
            "data": raw_reports
        }

    @staticmethod
    def create_report(data):
        student_id = data.get('student_id')
        content = data.get('content')
        if not student_id or not content:
            return {"success": False, "error": "Thiếu học sinh hoặc nội dung báo cáo"}
            
        report_data = {
            "content": content,
            "session_id": data.get('session_id', ''),
            "created_by": data.get('teacher_id', '')
        }
        
        new_id = ReportRepository.create_report(student_id, report_data)
        return {"success": True, "id": new_id, "message": "Tạo báo cáo thành công"}

    @staticmethod
    def update_report(student_id, report_id, data):
        success = ReportRepository.update_report(student_id, report_id, data)
        if not success:
            return {"success": False, "error": "Cập nhật báo cáo thất bại"}
        return {"success": True, "message": "Cập nhật báo cáo thành công"}

    @staticmethod
    def delete_report(student_id, report_id):
        success = ReportRepository.delete_report(student_id, report_id)
        if not success:
            return {"success": False, "error": "Xóa báo cáo thất bại"}
        return {"success": True, "message": "Xóa báo cáo thành công"}


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
    evaluations = {evaluation.get("seat_id"): evaluation for evaluation in edge_store.evaluations(session_id)}
    if not evaluations:
        windows = edge_store.windows(session_id)
        if windows:
            _, evaluations = scoring_service.compute_session_scores(windows)
    alerts = Counter((alert.get("seat_id"), alert.get("type")) for alert in edge_store.alerts(session_id))

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

    # App giáo viên/phụ huynh: điền có mặt và điểm vào map monitored_students, và session_results cho màn điểm danh
    roster = dict(session.get("monitored_students") or {})
    live = (edge_store.result(session_id) or {}).get("result_map") or {}
    result_map = {}
    for seat, student_id in seats.items():
        evaluation = evaluations.get(seat)
        present = evaluation is not None and usable(evaluation)
        score = evaluation["avg_concentration"] if present else None
        entry = dict(roster.get(seat) or {"student_id": student_id})
        entry.update({"is_present": present, "attention_score": score, "is_attention": bool(present and score >= 70)})
        roster[seat] = entry
        seat_status = live.get(seat, {}).get("status", "focused") if present else "absent"
        result_map[seat] = {"student_id": student_id, "status": seat_status}
    writes.append((db.collection("session_results").document(session_id), {
        "session_id": session_id,
        "class_id": class_id,
        "captured_at": session.get("ended_at") or server_timestamp(),
        "monitoring_status": "completed" if status == "complete" else "incomplete",
        "result_map": result_map,
    }))
    commit_writes(writes)
    db.collection("sessions").document(session_id).update({
        "reports_at": server_timestamp(),
        "report_count": len(writes) - 1,
        "monitored_students": roster,
    })
    return len(writes) - 1


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
