from datetime import datetime

from repositories.dashboard_repository import DashboardRepository
from services import monitoring_service
from services.evaluation_service import level, usable

ALERT_TITLES = {
    "head_drop": "Cúi đầu kéo dài",
    "back_turn": "Quay lưng lại",
    "side_conversation": "Nói chuyện riêng",
}
SESSION_STATUS_LABELS = {"running": "Đang giám sát", "paused": "Tạm dừng"}
RECENT_LIMIT = 5


class DashboardService:
    @staticmethod
    def get_dashboard_summary():
        teachers = DashboardRepository.get_all("teachers")
        classes = {item["id"]: item for item in DashboardRepository.get_all("classes2")}
        sessions = DashboardRepository.get_all("sessions")
        # ponytail: đọc toàn bộ session_evaluations mỗi lần tải; khi dữ liệu lớn thì lọc theo captured_at
        evaluations = [item for item in DashboardRepository.get_all("session_evaluations") if usable(item)]
        edge_nodes = DashboardRepository.get_all("edge_nodes")

        total_teachers = len(teachers)
        active_teachers = sum(1 for t in teachers if t.get("is_active") is not False)
        inactive_teachers = total_teachers - active_teachers

        # Tổng hợp bộ môn
        subjects_set = set()
        for t in teachers:
            subj = t.get("subject")
            if isinstance(subj, list):
                subjects_set.update(subj)
            elif isinstance(subj, str) and subj.strip():
                subjects_set.add(subj.strip())

        for c in classes.values():
            subj = c.get("subject")
            if isinstance(subj, str) and subj.strip():
                subjects_set.add(subj.strip())

        teacher_names = {t["id"]: t.get("name") or t.get("full_name") or "Giáo viên" for t in teachers}

        # Tiết đang giám sát và cảnh báo mới nhất của chúng (edge node ghi sessions/{s}/alerts)
        active_sessions = []
        alerts = []
        for session in sessions:
            status = session.get("status")
            if status not in monitoring_service.LIVE_STATUSES:
                continue
            class_data = classes.get(session.get("class_id"), {})
            class_name = class_data.get("class_name") or "Lớp học"
            student_count = len(monitoring_service.seat_assignments(class_data))
            active_sessions.append({
                "id": session["id"],
                "class_name": class_name,
                "teacher": teacher_names.get(session.get("teacher_id"), "Giáo viên"),
                "students": student_count or "--",
                "status": SESSION_STATUS_LABELS[status],
            })
            for alert in monitoring_service.recent_alerts(session["id"], RECENT_LIMIT):
                minute = int(alert.get("start_sec") or 0) // 60 + 1
                alerts.append({
                    "title": ALERT_TITLES.get(alert.get("type"), "Cảnh báo"),
                    "description": f"{class_name} · ghế {alert.get('seat_id')} · phút {minute}",
                    "handled": alert.get("status") in monitoring_service.ALERT_STATUSES,
                })

        # Mức độ tập trung từ đánh giá theo ghế của edge node, trung bình theo thời gian quan sát
        levels = [level(item["avg_concentration"]) for item in evaluations]
        total_evals = len(levels)
        if total_evals > 0:
            observed = sum(item["observed_sec"] for item in evaluations)
            weighted = sum(item["avg_concentration"] * item["observed_sec"] for item in evaluations)
            concentration_stats = {
                "high": round(levels.count("good") / total_evals * 100, 1),
                "medium": round(levels.count("stable") / total_evals * 100, 1),
                "low": round(levels.count("attention") / total_evals * 100, 1),
                "avg_score": round(weighted / observed, 1),
                "has_data": True
            }
        else:
            concentration_stats = {
                "high": 0,
                "medium": 0,
                "low": 0,
                "avg_score": 0,
                "has_data": False
            }

        online_edges = sum(1 for node in edge_nodes if monitoring_service.is_online(node))
        if edge_nodes:
            monitoring = f"{online_edges}/{len(edge_nodes)} camera AI trực tuyến"
        else:
            monitoring = "Chưa có camera AI"

        # Hoạt động gần đây: các lần bắt đầu/kết thúc giám sát
        events = []
        for session in sessions:
            class_name = classes.get(session.get("class_id"), {}).get("class_name") or "Lớp học"
            for field, title in (("started_at", "Bắt đầu giám sát"), ("ended_at", "Kết thúc giám sát")):
                if isinstance(session.get(field), datetime):
                    events.append((session[field], {
                        "title": title,
                        "description": f"{class_name} · {session.get('subject') or 'Chưa rõ môn'}",
                        "time": session[field].isoformat(),
                    }))
        events.sort(key=lambda event: event[0], reverse=True)

        return {
            "success": True,
            "stats": {
                "total_teachers": total_teachers,
                "active_teachers": active_teachers,
                "inactive_teachers": inactive_teachers,
                "total_subjects": len(subjects_set)
            },
            "active_sessions": active_sessions,
            "concentration": concentration_stats,
            "system_status": {
                "backend": "Đang hoạt động",
                "firebase": "Đang hoạt động",
                "monitoring": monitoring,
                "monitoring_ok": online_edges > 0,
            },
            "alerts": alerts[:RECENT_LIMIT],
            "activities": [event for _, event in events[:RECENT_LIMIT]]
        }
