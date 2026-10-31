from repositories.session_repository import SessionRepository
from routes.test_helpers import json_value, server_timestamp
from services import monitoring_service

class SessionService:
    @staticmethod
    def fetch_all_schedules():
        sessions = SessionRepository.get_all_sessions()
        formatted = [{"id": item.get("id"), **json_value(item)} for item in sessions]
        formatted.sort(key=lambda x: x.get("session_date", ""), reverse=True)
        return formatted

    @staticmethod
    def fetch_all_teachers():
        teachers = SessionRepository.get_all_teachers()
        return [{"id": item.get("id"), **json_value(item)} for item in teachers]

    @staticmethod
    def fetch_all_rooms():
        rooms = SessionRepository.get_all_rooms()
        return [{"id": item.get("id"), **json_value(item)} for item in rooms]

    @staticmethod
    def create_new_session(data):
        class_id = data.get("class_id")
        teacher_id = data.get("teacher_id")
        
        if not class_id or not SessionRepository.get_class_exists(class_id):
            return {"success": False, "message": "Không tìm thấy lớp học.", "status": 404}
        if not teacher_id or not SessionRepository.get_teacher_exists(teacher_id):
            return {"success": False, "message": "Không tìm thấy giáo viên.", "status": 404}
            
        session_ref = SessionRepository.create_session(data)
        doc = session_ref.get()
        return {"success": True, "data": {"id": doc.id, **json_value(doc.to_dict())}, "status": 201}

    @staticmethod
    def update_session_status(session_id, new_status, valid_transitions, force=False):
        session_ref, session_doc = SessionRepository.get_session_by_id(session_id)
        if not session_doc.exists:
            return {"success": False, "message": "Không tìm thấy lịch học/phiên.", "status": 404}

        session = session_doc.to_dict() or {}
        current_status = session.get("status")
        if new_status not in valid_transitions.get(current_status, set()):
            return {"success": False, "message": "Chuyển trạng thái không hợp lệ.", "status": 409}

        update_data = {"status": new_status}
        if current_status == "scheduled" and new_status == "running":
            class_data, problem = monitoring_service.check_start(session_id, session, force)
            if problem:
                message = monitoring_service.START_PROBLEMS[problem]
                return {"success": False, "code": problem, "message": message, "status": 409}
            monitoring_service.freeze_roster(session_id, class_data)
            update_data["started_at"] = server_timestamp()
            if class_data.get("camera_id"):  # camera của tiết theo sơ đồ đã chốt: camera của lớp lúc bắt đầu
                update_data["camera_id"] = class_data["camera_id"]
        elif new_status == "completed":
            # end_time là giờ kết thúc theo thời khóa biểu, giữ nguyên
            update_data["ended_at"] = server_timestamp()

        updated_doc = SessionRepository.update_status(session_ref, update_data)
        return {"success": True, "data": {"id": updated_doc.id, **json_value(updated_doc.to_dict())}, "status": 200}