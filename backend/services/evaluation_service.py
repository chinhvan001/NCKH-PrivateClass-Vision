from routes.class_routes import get_vietnamese_sort_key, teacher_name
from routes.test_helpers import db
from services.monitoring_service import data_status, result_status, roster

# Đánh giá theo ghế do edge node ghi (session_evaluations/{session}_{seat}): avg_concentration 0-100
# từ đầu tiết, observed_sec là thời gian ghế có người. Ghế chỉ có người đi ngang qua không được tính.
MIN_OBSERVED_SEC = 60


def level(score):
    if score >= 80.0:
        return "good"
    if score >= 70.0:
        return "stable"
    return "attention"


def usable(evaluation):
    score, observed = evaluation.get("avg_concentration"), evaluation.get("observed_sec")
    return (
        isinstance(score, (int, float))
        and isinstance(observed, int)
        and observed >= MIN_OBSERVED_SEC
        and isinstance(evaluation.get("session_id"), str)
    )


def student_scores(evaluations, class_data):
    """Điểm tập trung của từng học sinh, trung bình theo observed_sec qua các tiết.

    Ghế được đổi ra học sinh qua roster của từng tiết; ghế chưa xếp học sinh giữ khóa "seat:<seat_id>"."""
    rosters, totals = {}, {}
    for evaluation in filter(usable, evaluations):
        session_id = evaluation["session_id"]
        if session_id not in rosters:
            rosters[session_id] = roster(session_id, class_data)
        seat = evaluation.get("seat_id")
        total = totals.setdefault(rosters[session_id].get(seat) or f"seat:{seat}", [0.0, 0])
        total[0] += evaluation["avg_concentration"] * evaluation["observed_sec"]
        total[1] += evaluation["observed_sec"]
    return {key: round(weighted / observed, 1) for key, (weighted, observed) in totals.items()}


class EvaluationService:
    @staticmethod
    def get_classes_overview():
        classes = {doc.id: doc.to_dict() or {} for doc in db.collection("classes2").stream()}
        session_class = {doc.id: (doc.to_dict() or {}).get("class_id") for doc in db.collection("sessions").stream()}
        by_class = {}
        # ponytail: đọc toàn bộ session_evaluations mỗi lần mở trang; khi dữ liệu lớn thì lọc theo captured_at
        for doc in db.collection("session_evaluations").stream():
            evaluation = doc.to_dict() or {}
            class_id = session_class.get(evaluation.get("session_id"))
            if class_id in classes:
                by_class.setdefault(class_id, []).append(evaluation)

        result = []
        for class_id, evaluations in by_class.items():
            scores = student_scores(evaluations, classes[class_id])
            if not scores:
                continue
            data = classes[class_id]
            attention = round(sum(scores.values()) / len(scores), 1)
            result.append({
                "id": class_id,
                "name": data.get("class_name") or class_id,
                "subject": data.get("subject") or "Chưa xác định",
                "teacher": teacher_name(data.get("teacher_id")),
                "students": len(scores),
                "attention": attention,
                "status": level(attention),
            })
        result.sort(key=lambda item: item["name"])
        return {"success": True, "data": result}

    @staticmethod
    def get_class_details(class_id):
        """Báo cáo từng học sinh và từng tiết của lớp, None nếu không có lớp."""
        class_doc = db.collection("classes2").document(class_id).get()
        if not class_doc.exists:
            return None
        data = class_doc.to_dict() or {}
        sessions = {
            doc.id: doc.to_dict() or {} for doc in db.collection("sessions").where("class_id", "==", class_id).stream()
        }
        evaluations = [
            doc.to_dict() or {}
            for session_id in sessions
            for doc in db.collection("session_evaluations").where("session_id", "==", session_id).stream()
        ]

        students = []
        for key, score in student_scores(evaluations, data).items():
            if key.startswith("seat:"):
                name = f"Ghế {key[5:]} (chưa xếp học sinh)"
            else:
                student_doc = db.collection("students2").document(key).get(field_paths=["full_name"])
                name = (student_doc.to_dict() or {}).get("full_name") if student_doc.exists else None
            students.append({
                "student_id": key,
                "name": name or "Học sinh không còn trong hệ thống",
                "attention_score": score,
                "status": level(score),
            })
        students.sort(key=lambda item: get_vietnamese_sort_key(item["name"]))

        # Từng tiết đã diễn ra, đánh dấu tiết bị gián đoạn (data_status "partial")
        by_session = {}
        for evaluation in filter(usable, evaluations):
            by_session.setdefault(evaluation["session_id"], []).append(evaluation)
        session_rows = []
        for session_id, session in sessions.items():
            if session.get("status") not in ("running", "paused", "completed"):
                continue  # chưa diễn ra hoặc đã hủy
            items = by_session.get(session_id, [])
            observed = sum(item["observed_sec"] for item in items)
            weighted = sum(item["avg_concentration"] * item["observed_sec"] for item in items)
            session_rows.append({
                "id": session_id,
                "session_date": session.get("session_date"),
                "start_time": session.get("start_time"),
                "subject": session.get("subject"),
                "data_status": data_status(session, result_status(session_id)),
                "seats": len(items),
                "attention": round(weighted / observed, 1) if observed else None,
            })
        session_rows.sort(key=lambda row: (row["session_date"] or "", row["start_time"] or ""), reverse=True)

        class_name = data.get("class_name") or class_id
        subject = data.get("subject") or next((s["subject"] for s in sessions.values() if s.get("subject")), "Chưa rõ")
        return {
            "name": class_name,
            "class_name": class_name,
            "subject": subject,
            "teacher": teacher_name(data.get("teacher_id")),
            "classroom": class_name,
            "students": students,
            "sessions": session_rows,
        }
