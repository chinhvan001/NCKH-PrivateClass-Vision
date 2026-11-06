from flask import Blueprint, request, jsonify
from services.report_service import ReportService

report_bp = Blueprint('report_bp', __name__)

@report_bp.route('/api/v1/reports', methods=['GET'])
def get_reports():
    try:
        query_params = request.args.to_dict()
        result = ReportService.get_reports_overview(query_params)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@report_bp.route('/api/v1/reports', methods=['POST'])
def create_report():
    try:
        data = request.get_json() or {}
        result = ReportService.create_report(data)
        if not result.get("success"):
            return jsonify(result), 400
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@report_bp.route('/api/v1/students/<student_id>/reports/<report_id>', methods=['PUT'])
def update_report(student_id, report_id):
    try:
        data = request.get_json() or {}
        result = ReportService.update_report(student_id, report_id, data)
        if not result.get("success"):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@report_bp.route('/api/v1/students/<student_id>/reports/<report_id>', methods=['DELETE'])
def delete_report(student_id, report_id):
    try:
        result = ReportService.delete_report(student_id, report_id)
        if not result.get("success"):
            return jsonify(result), 404
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500