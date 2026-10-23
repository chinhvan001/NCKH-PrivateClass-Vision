from flask import Blueprint, jsonify
from services.session_service import SessionService
from routes.test_helpers import get_json_body, require_admin, required_string

session_bp = Blueprint("session_bp", __name__) 
ALLOWED_STATUS = {"scheduled", "running", "completed", "cancelled"}
VALID_TRANSITIONS = {
    "scheduled": {"running", "cancelled"},
    "running": {"completed"},
}

def error(message, status=400):
    return jsonify({"success": False, "message": message}), status

@session_bp.route("/api/admin/schedules", methods=["GET"])
def get_schedules():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    try:
        data = SessionService.fetch_all_schedules()
        return jsonify({"success": True, "data": data}), 200
    except Exception as exc:
        print("Get schedules error:", exc)
        return error("Không thể lấy danh sách lịch học.", 500)

@session_bp.route("/api/admin/teachers", methods=["GET"])
def get_teachers():
    _, auth_error = require_admin()
    if auth_error: return auth_error
    try:
        data = SessionService.fetch_all_teachers()
        return jsonify({"success": True, "data": data}), 200
    except Exception as exc:
        return jsonify({"success": False, "message": "Không thể lấy danh sách giáo viên."}), 500

@session_bp.route("/api/admin/rooms", methods=["GET"])
def get_rooms():
    _, auth_error = require_admin()
    if auth_error: return auth_error
    try:
        data = SessionService.fetch_all_rooms()
        return jsonify({"success": True, "data": data}), 200
    except Exception as exc:
        return jsonify({"success": False, "message": "Không thể lấy danh sách phòng học."}), 500

@session_bp.route("/api/admin/classes", methods=["GET"])
def get_classes():
    _, auth_error = require_admin()
    if auth_error: return auth_error
    try:
        data = SessionService.fetch_all_classes()
        return jsonify({"success": True, "data": data}), 200
    except Exception as exc:
        return jsonify({"success": False, "message": "Không thể lấy danh sách lớp học."}),

@session_bp.route("/api/admin/schedules", methods=["POST"])
def create_schedule():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    data = get_json_body()
    
    class_id, msg = required_string(data, "class_id")
    if msg: return error(msg)
    teacher_id, msg = required_string(data, "teacher_id")
    if msg: return error(msg)
    subject, msg = required_string(data, "subject")
    if msg: return error(msg)
    
    result = SessionService.create_new_session(data)
    if not result["success"]:
        return error(result["message"], result["status"])
    return jsonify(result), result["status"]

@session_bp.route("/api/admin/schedules/<session_id>/status", methods=["PUT"])
def update_status(session_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    status = get_json_body().get("status")
    if status not in ALLOWED_STATUS:
        return error("Trạng thái không hợp lệ.")
        
    result = SessionService.update_session_status(session_id, status, VALID_TRANSITIONS)
    if not result["success"]:
        return error(result["message"], result["status"])
    return jsonify(result), result["status"]