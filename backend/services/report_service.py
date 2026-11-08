from repositories.report_repository import ReportRepository

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


# ============================================================
# Hàm tạo báo cáo phụ huynh từ dữ liệu Camera AI (UC03)
# Được thêm vào khi sync từ Test workspace
# Dùng bởi jobs/parent_reports.py và jobs/scoring_worker.py
# ============================================================
from collections import Counter
from datetime import timedelta

from routes.test_helpers import commit_writes, db, server_timestamp
from services import monitoring_service, scoring_service


_LOOKBACK_DAYS = 7


def _report_level(score):
    if score >= 80.0:
        return "good"
    if score >= 70.0:
        return "stable"
    return "attention"


def _report_usable(evaluation):
    score = evaluation.get("avg_concentration")
    observed = evaluation.get("observed_sec")
    return (
        isinstance(score, (int, float))
        and isinstance(observed, int)
        and observed >= 60
        and isinstance(evaluation.get("session_id"), str)
    )


def build_session_reports(session_id, force=False):
    """Ghi báo cáo của tiết cho từng học sinh có dữ liệu.
    Trả số báo cáo đã ghi, hoặc None khi chưa tạo được:
    tiết chưa kết thúc, hoặc camera AI chưa chốt kết quả
    (force=True thì không chờ)."""
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
    if seats is None:
        monitoring_service.freeze_roster(session_id, class_data)
        seats = monitoring_service.seat_assignments(class_data)

    evaluations = {}
    for doc in db.collection("session_evaluations").where("session_id", "==", session_id).stream():
        evaluation = doc.to_dict() or {}
        evaluations[evaluation.get("seat_id")] = evaluation

    if not evaluations:
        windows = [
            d.to_dict()
            for d in db.collection("session_windows").where("session_id", "==", session_id).stream()
            if d.to_dict()
        ]
        if windows:
            _, evals = scoring_service.compute_session_scores(windows)
            evaluations = evals

    alerts = Counter()
    for doc in db.collection("sessions").document(session_id).collection("alerts").stream():
        alert = doc.to_dict() or {}
        alerts[(alert.get("seat_id"), alert.get("type"))] += 1

    writes = []
    for seat, student_id in seats.items():
        evaluation = evaluations.get(seat)
        if evaluation is None or not _report_usable(evaluation):
            continue
        report = {
            "session_id": session_id,
            "class_id": class_id,
            "class_name": class_data.get("class_name", ""),
            "subject": session.get("subject", ""),
            "session_date": session.get("session_date"),
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "avg_concentration": evaluation["avg_concentration"],
            "level": _report_level(evaluation["avg_concentration"]),
            "observed_min": round(evaluation["observed_sec"] / 60),
            "alerts": {
                alert_type: alerts[(seat, alert_type)]
                for alert_type in monitoring_service.ALERT_TYPES
            },
            "partial": status != "complete",
            "created_at": server_timestamp(),
        }
        report_ref = (
            db.collection("students2").document(student_id).collection("reports").document(session_id)
        )
        writes.append((report_ref, report))

    commit_writes(writes)
    db.collection("sessions").document(session_id).update(
        {"reports_at": server_timestamp(), "report_count": len(writes)}
    )
    return len(writes)


def build_pending_reports():
    """Tạo báo cáo cho các tiết kết thúc trong _LOOKBACK_DAYS ngày qua mà
    chưa có. Trả {session_id: số báo cáo}."""
    since = monitoring_service.utc_now() - timedelta(days=_LOOKBACK_DAYS)
    built = {}
    for doc in db.collection("sessions").where("ended_at", ">=", since).stream():
        if "reports_at" in (doc.to_dict() or {}):
            continue
        count = build_session_reports(doc.id)
        if count is not None:
            built[doc.id] = count
    return built
