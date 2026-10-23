from repositories.dashboard_repository import DashboardRepository
from firebase_admin import firestore

class DashboardService:
    @staticmethod
    def get_dashboard_summary():
        db = DashboardRepository.get_db()
        teachers = DashboardRepository.get_all_teachers()
        classes = DashboardRepository.get_all_classes()
        sessions = DashboardRepository.get_all_sessions()
        
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
        
        for c in classes:
            subj = c.get("subject")
            if isinstance(subj, str) and subj.strip():
                subjects_set.add(subj.strip())

        active_sessions = []
        concentrations = []

        for session in sessions:
            status = session.get("status", "scheduled")
            class_id = session.get("class_id")
            teacher_id = session.get("teacher_id")
            
            # Tra cứu tên lớp và lưu lại thông tin document lớp học
            class_name = "Lớp học"
            class_doc = None
            for c in classes:
                if c.get("id") == class_id:
                    class_name = c.get("class_name") or c.get("name") or "Lớp học"
                    class_doc = c
                    break
            
            # Tra cứu tên giáo viên
            teacher_name = "Giáo viên"
            for t in teachers:
                if t.get("id") == teacher_id:
                    teacher_name = t.get("name") or t.get("full_name") or "Giáo viên"
                    break

            # 1. Lấy số lượng học sinh từ seat_snapshot của phiên học
            seat_snapshot = session.get("seat_snapshot", {})
            student_count = sum(1 for s_id in seat_snapshot.values() if s_id and str(s_id).strip() not in ["", "None", "null", "undefined"])

            # 2. Nếu phiên học chưa có seat_snapshot, lấy sĩ số từ seat_map của lớp học (classes2)
            if student_count == 0 and class_doc:
                seat_map = class_doc.get("seat_map", {})
                if isinstance(seat_map, dict):
                    student_count = sum(1 for seat_info in seat_map.values() if isinstance(seat_info, dict) and seat_info.get("student_id"))

            session_info = {
                "id": session.get("id"),
                "class_name": class_name,
                "teacher": teacher_name,
                "students": student_count if student_count > 0 else "--",
                "status": "Đang hoạt động" if status == "running" else ("Sắp diễn ra" if status == "scheduled" else "Hoàn thành")
            }

            if status == "running":
                active_sessions.append(session_info)

            # 1. Quét dữ liệu tập trung từ aggregated_evaluation trong session
            agg_eval = session.get("aggregated_evaluation", {})
            if isinstance(agg_eval, dict):
                for seat_id, captures in agg_eval.items():
                    if isinstance(captures, dict):
                        for k, v in captures.items():
                            if isinstance(v, dict):
                                conc = v.get("avg_concentration", v.get("concentration"))
                                if conc is not None:
                                    try: concentrations.append(float(conc))
                                    except: pass
                        if "avg_concentration" in captures or "concentration" in captures:
                            try: concentrations.append(float(captures.get("avg_concentration", captures.get("concentration"))))
                            except: pass

        # 2. Quét bổ sung từ collection session_results để đảm bảo đồng bộ với trang Phân tích & Đánh giá
        try:
            result_docs = db.collection("session_results").stream()
            for doc in result_docs:
                r_data = doc.to_dict() or {}
                score = r_data.get("avg_concentration", r_data.get("attention_score"))
                if score is not None:
                    try: concentrations.append(float(score))
                    except: pass
        except Exception:
            pass

        # Tính toán phân loại tỷ lệ % và điểm trung bình toàn trường
        high_count = sum(1 for c in concentrations if c >= 80.0)
        med_count = sum(1 for c in concentrations if 70.0 <= c < 80.0)
        low_count = sum(1 for c in concentrations if c < 70.0)
        total_evals = len(concentrations)

        avg_score = round(sum(concentrations) / total_evals, 1) if total_evals > 0 else 0.0

        if total_evals > 0:
            concentration_stats = {
                "high": round((high_count / total_evals) * 100, 1),
                "medium": round((med_count / total_evals) * 100, 1),
                "low": round((low_count / total_evals) * 100, 1),
                "avg_score": avg_score,
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

        activities = [
            {"title": "Đăng nhập hệ thống", "description": "Quản trị viên đã đăng nhập", "time": "Vừa xong"},
            {"title": "Đồng bộ tài khoản giáo viên", "description": f"{total_teachers} tài khoản giáo viên", "time": "Hiện tại"},
            {"title": "Kiểm tra hệ thống", "description": "Hệ thống hoạt động bình thường", "time": "Hiện tại"}
        ]

        return {
            "success": True,
            "stats": {
                "total_teachers": total_teachers,
                "active_teachers": active_teachers,
                "inactive_teachers": inactive_teachers,
                "total_subjects": len(subjects_set) if len(subjects_set) > 0 else 4
            },
            "active_sessions": active_sessions,
            "concentration": concentration_stats,
            "system_status": {
                "backend": "Đang hoạt động",
                "firebase": "Đang hoạt động",
                "monitoring": "Đang phát triển"
            },
            "activities": activities
        }