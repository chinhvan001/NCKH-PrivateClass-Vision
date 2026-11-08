from flask import Blueprint, jsonify, request
from routes.test_helpers import get_json_body, require_admin
from services.class_service import ClassService

class_bp = Blueprint("class_bp", __name__)


@class_bp.route("/api/admin/classes", methods=["GET"])
def get_classes():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    result, status_code = ClassService.get_classes(request.args.to_dict())
    return jsonify(result), status_code


@class_bp.route("/api/admin/classes", methods=["POST"])
def create_class():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    data = get_json_body()
    result, status_code = ClassService.create_class(data)
    return jsonify(result), status_code


@class_bp.route("/api/admin/classes/<class_id>", methods=["GET", "PUT", "DELETE"])
def class_detail(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error

    if request.method == "GET":
        result, status_code = ClassService.get_class_detail(class_id)
        return jsonify(result), status_code

    if request.method == "DELETE":
        result, status_code = ClassService.delete_class(class_id)
        return jsonify(result), status_code

    data = get_json_body()
    result, status_code = ClassService.update_class(class_id, data)
    return jsonify(result), status_code


@class_bp.route("/api/admin/classes/<class_id>/students", methods=["GET"])
def class_students(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    result, status_code = ClassService.get_class_students(class_id)
    return jsonify(result), status_code


@class_bp.route("/api/admin/classes/<class_id>/seats", methods=["GET"])
def class_seats(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    result, status_code = ClassService.get_class_seats(class_id)
    return jsonify(result), status_code


@class_bp.route("/api/admin/classes/<class_id>/seats/<seat_id>", methods=["PUT"])
def update_seat(class_id, seat_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    data = get_json_body()
    student_id = data.get("student_id")
    result, status_code = ClassService.update_seat(class_id, seat_id, student_id)
    return jsonify(result), status_code
