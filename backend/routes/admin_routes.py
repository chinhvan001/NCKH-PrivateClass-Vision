from flask import Blueprint, jsonify
from utils.auth import (
    get_current_user,
    get_json_body,
    is_admin_user,
    verify_request_token,
)
from services.admin_service import AdminService

admin_bp = Blueprint("admin_bp", __name__)


def require_admin():
    decoded_token = verify_request_token()

    if not decoded_token:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Unauthorized."
            }),
            401
        )

    uid = decoded_token.get("uid")

    if not uid:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Token không hợp lệ."
            }),
            401
        )

    _, admin_data = get_current_user(decoded_token)

    if not admin_data:
        return None, None, (
            jsonify({
                "success": False,
                "message": "Tài khoản admin không tồn tại."
            }),
            403
        )

    if not is_admin_user(admin_data):
        return None, None, (
            jsonify({
                "success": False,
                "message": "Tài khoản admin đã bị vô hiệu hóa."
            }),
            403
        )

    return uid, admin_data, None


@admin_bp.route("/api/admin/users", methods=["GET"])
def get_admin_users():
    uid, admin_data, error_response = require_admin()
    if error_response:
        return error_response

    result, status_code = AdminService.get_teachers()
    return jsonify(result), status_code


@admin_bp.route("/api/admin/teachers", methods=["POST"])
def create_teacher():
    uid, admin_data, error_response = require_admin()
    if error_response:
        return error_response

    data = get_json_body()
    result, status_code = AdminService.create_teacher(data)
    return jsonify(result), status_code


@admin_bp.route("/api/users/<uid>", methods=["PUT"])
def update_teacher(uid):
    admin_uid, admin_data, error_response = require_admin()
    if error_response:
        return error_response

    data = get_json_body()
    result, status_code = AdminService.update_teacher(uid, data)
    return jsonify(result), status_code


@admin_bp.route("/api/admin/teachers/<uid>", methods=["DELETE"])
def delete_teacher(uid):
    admin_uid, admin_data, error_response = require_admin()
    if error_response:
        return error_response

    result, status_code = AdminService.delete_teacher(uid)
    return jsonify(result), status_code


@admin_bp.route("/api/admin/profile/<uid>", methods=["GET"])
def get_admin_profile(uid):
    decoded_token = verify_request_token()
    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    current_uid = decoded_token.get("uid")
    if current_uid != uid:
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền xem profile này."
        }), 403

    result, status_code = AdminService.get_admin_profile(uid)
    return jsonify(result), status_code


@admin_bp.route("/api/admin/profile/<uid>", methods=["PUT"])
def update_admin_profile(uid):
    decoded_token = verify_request_token()
    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    current_uid = decoded_token.get("uid")
    if current_uid != uid:
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền chỉnh sửa profile này."
        }), 403

    data = get_json_body()
    result, status_code = AdminService.update_admin_profile(uid, data)
    return jsonify(result), status_code


@admin_bp.route("/api/admin/change-password", methods=["POST"])
def change_admin_password():
    decoded_token = verify_request_token()
    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    uid = decoded_token.get("uid")
    if not uid:
        return jsonify({
            "success": False,
            "message": "Token không hợp lệ."
        }), 401

    data = get_json_body()
    result, status_code = AdminService.change_admin_password(uid, data)
    return jsonify(result), status_code
