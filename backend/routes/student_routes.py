from flask import Blueprint, request, jsonify
from routes.test_helpers import admin_only
from services.student_service import StudentService

student_bp = admin_only(Blueprint('student_bp', __name__))

@student_bp.route('/api/v1/students', methods=['GET'])
def get_students():
    try:
        query_params = request.args.to_dict()
        result = StudentService.get_students_overview(query_params)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@student_bp.route('/api/v1/students/<student_id>', methods=['GET'])
def get_student_detail(student_id):
    try:
        result = StudentService.get_student_detail(student_id)
        if not result.get("success"):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@student_bp.route('/api/v1/students', methods=['POST'])
def create_student():
    try:
        data = request.get_json() or {}
        result = StudentService.create_student(data)
        if not result.get("success"):
            return jsonify(result), 400
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@student_bp.route('/api/v1/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        data = request.get_json() or {}
        result = StudentService.update_student(student_id, data)
        if not result.get("success"):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@student_bp.route('/api/v1/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        result = StudentService.delete_student(student_id)
        if not result.get("success"):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500