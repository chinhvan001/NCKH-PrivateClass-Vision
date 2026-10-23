from flask import Blueprint, jsonify
from services import monitoring_service
from services.session_service import SessionService
from routes.test_helpers import get_json_body, require_admin, required_string

session_bp = Blueprint("session_bp", __name__)
# Edge node camera-ai giám sát khi running, tắt camera khi paused, chốt kết quả khi completed.
ALLOWED_STATUS = {"scheduled", "running", "paused", "completed", "cancelled"}
VALID_TRANSITIONS = {
    "scheduled": {"running", "cancelled"},
    "running": {"paused", "completed"},
    "paused": {"running", "completed"},
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
    data = get_json_body()
    status = data.get("status")
    if status not in ALLOWED_STATUS:
        return error("Trạng thái không hợp lệ.")

    # force: bắt đầu dù camera AI offline (lỗi có code "edge_offline")
    result = SessionService.update_session_status(
        session_id, status, VALID_TRANSITIONS, force=data.get("force") is True
    )
    return jsonify(result), result["status"]


@session_bp.route("/api/admin/schedules/<session_id>/monitoring", methods=["GET"])
def get_monitoring(session_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    data = monitoring_service.live_view(session_id)
    if data is None:
        return error("Không tìm thấy lịch học/phiên.", 404)
    return jsonify({"success": True, "data": data}), 200


@session_bp.route("/api/admin/schedules/<session_id>/seats", methods=["GET"])
def get_session_seats(session_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    data = monitoring_service.seat_plan(session_id)
    if data is None:
        return error("Không tìm thấy lịch học/phiên.", 404)
    return jsonify({"success": True, "data": data}), 200


@session_bp.route("/api/admin/schedules/<session_id>/alerts/<alert_id>", methods=["PUT"])
def update_alert(session_id, alert_id):
    uid, auth_error = require_admin()
    if auth_error:
        return auth_error
    status = get_json_body().get("status")
    if status not in monitoring_service.ALERT_STATUSES:
        return error("Trạng thái cảnh báo không hợp lệ.")
    if not monitoring_service.handle_alert(session_id, alert_id, status, uid):
        return error("Không tìm thấy cảnh báo.", 404)
    return jsonify({"success": True}), 200