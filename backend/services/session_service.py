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
        classes = SessionRepository.get_all_classes()
        return [{"id": item.get("id"), **json_value(item)} for item in classes]

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
    def update_session_status(session_id, new_status, valid_transitions):
        session_ref, session_doc = SessionRepository.get_session_by_id(session_id)
        if not session_doc.exists:
            return {"success": False, "message": "Không tìm thấy lịch học/phiên.", "status": 404}
            
        current_status = (session_doc.to_dict() or {}).get("status")
        if new_status not in valid_transitions.get(current_status, set()):
            return {"success": False, "message": "Chuyển trạng thái không hợp lệ.", "status": 409}
            
        update_data = {"status": new_status}
        if new_status == "completed":
            update_data["end_time"] = server_timestamp()
            
        updated_doc = SessionRepository.update_status(session_ref, update_data)
        return {"success": True, "data": {"id": updated_doc.id, **json_value(updated_doc.to_dict())}, "status": 200}