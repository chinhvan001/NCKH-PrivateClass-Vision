from flask import Blueprint, jsonify, request
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
    get_json_body,
)
from services.classroom_service import ClassroomService

classroom_bp = Blueprint("classroom_bp", __name__)


def authorize_admin():
    if request.method == "OPTIONS":
        return None, None

    decoded_token = verify_request_token()

    if not decoded_token:
        return None, (
            jsonify({
                "success": False,
                "message": "Unauthorized"
            }),
            401,
        )

    user_ref, current_user = get_current_user(decoded_token)

    if not current_user:
        return None, (
            jsonify({
                "success": False,
                "message": "Không tìm thấy người dùng"
            }),
            401,
        )

    if not is_admin_user(current_user):
        return None, (
            jsonify({
                "success": False,
                "message": "Bạn không có quyền thực hiện thao tác này"
            }),
            403,
        )

    return current_user, None


@classroom_bp.route(
    "/api/admin/classrooms",
    methods=["GET", "POST", "OPTIONS"]
)
def classrooms():
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    current_user, error_response = authorize_admin()
    if error_response:
        return error_response

    if request.method == "GET":
        result, status_code = ClassroomService.get_all_classrooms()
        return jsonify(result), status_code

    data = get_json_body()
    result, status_code = ClassroomService.create_classroom(data)
    return jsonify(result), status_code


@classroom_bp.route(
    "/api/admin/classrooms/<classroom_id>",
    methods=["PUT", "DELETE", "OPTIONS"]
)
def classroom_detail(classroom_id):
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    current_user, error_response = authorize_admin()
    if error_response:
        return error_response

    if request.method == "DELETE":
        result, status_code = ClassroomService.delete_classroom(classroom_id)
        return jsonify(result), status_code

    data = get_json_body()
    result, status_code = ClassroomService.update_classroom(classroom_id, data)
    return jsonify(result), status_code
