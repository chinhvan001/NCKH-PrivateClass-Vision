from datetime import datetime, timedelta
from repositories.session_repository import SessionRepository
from routes.test_helpers import json_value, server_timestamp

class SessionService:
    @staticmethod
    def fetch_all_schedules():
        sessions = SessionRepository.get_all_sessions()
        formatted = [{"id": item.get("id"), **json_value(item)} for item in sessions]
        formatted.sort(key=lambda x: x.get("session_date", ""), reverse=True)
        return formatted

    @staticmethod
    def fetch_all_classes():
        return [{"id": item.get("id"), **json_value(item)} for item in SessionRepository.get_all_classes()]

    @staticmethod
    def fetch_all_teachers():
        return [{"id": item.get("id"), **json_value(item)} for item in SessionRepository.get_all_teachers()]

    @staticmethod
    def fetch_all_rooms():
        return [{"id": item.get("id"), **json_value(item)} for item in SessionRepository.get_all_rooms()]

    @staticmethod
    def create_new_session(data):
        class_id = data.get("class_id")
        teacher_id = data.get("teacher_id")
        subject = data.get("subject")
        start_date_str = data.get("session_date") # YYYY-MM-DD
        repeat_count = int(data.get("repeat_count", 1))
        day_configs = data.get("day_configs", {}) # e.g. {"1": {"shift": "morning", "period": 1}, "3": {"shift": "afternoon", "period": 2}}
        room = data.get("room", "301")

        if not class_id or not SessionRepository.get_class_exists(class_id):
            return {"success": False, "message": "Không tìm thấy lớp học.", "status": 404}
        if not teacher_id or not SessionRepository.get_teacher_exists(teacher_id):
            return {"success": False, "message": "Không tìm thấy giáo viên.", "status": 404}

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_date = datetime.now()

        # Tạo danh sách các buổi học lặp lại sang các tuần
        sessions_to_create = []
        created_count = 0
        current_week_offset = 0

        # day_configs chứa các thứ được chọn (1: T2, 2: T3, 3: T4, 4: T5, 5: T6, 6: T7)
        selected_days = sorted([int(k) for k in day_configs.keys()]) if day_configs else [start_date.weekday() + 1]

        while created_count < repeat_count:
            # Lặp qua từng tuần
            for target_day in selected_days:
                if created_count >= repeat_count:
                    break
                
                # Tính khoảng cách ngày từ start_date
                # Python weekday: Mon = 0, Tue = 1 ... Sun = 6
                # target_day UI: T2 = 1, T3 = 2 ... T7 = 6
                py_target_weekday = target_day - 1
                
                # Tìm ngày rơi vào thứ mong muốn trong tuần hiện tại
                days_ahead = py_target_weekday - start_date.weekday()
                if days_ahead < 0: 
                    days_ahead += 7 # Chuyển sang tuần sau nếu thứ đã trôi qua trong tuần đầu
                
                session_dt = start_date + timedelta(days=days_ahead + (current_week_offset * 7))
                session_date_fmt = session_dt.strftime("%Y-%m-%d")

                config = day_configs.get(str(target_day), {})
                shift = config.get("shift", data.get("morning_or_afternoon", "morning"))
                period = int(config.get("period", data.get("period", 1)))

                payload = {
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "session_date": session_date_fmt,
                    "day_of_week": target_day,
                    "session_type": shift,
                    "period": period,
                    "room": room,
                }
                sessions_to_create.append(payload)
                created_count += 1

            current_week_offset += 1

        created_ids = SessionRepository.create_batch_sessions(sessions_to_create)
        return {
            "success": True, 
            "message": f"Đã tạo thành công {len(created_ids)} buổi học lặp lại!",
            "data": {"created_count": len(created_ids)}, 
            "status": 201
        }