from flask import Blueprint, jsonify
from routes.test_helpers import admin_only
from services.evaluation_service import EvaluationService

evaluation_bp = admin_only(Blueprint('evaluation_bp', __name__))

@evaluation_bp.route('/api/v1/evaluations/classes-overview', methods=['GET'])
def get_classes_overview():
    try:
        result = EvaluationService.get_classes_overview()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@evaluation_bp.route('/api/v1/evaluations/classes/<class_id>/details', methods=['GET'])
def get_class_details(class_id):
    try:
        data = EvaluationService.get_class_details(class_id)
        if data is None:
            return jsonify({"success": False, "error": "Không tìm thấy lớp học."}), 404
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
