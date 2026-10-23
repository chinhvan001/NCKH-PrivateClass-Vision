from flask import Blueprint, jsonify
from services.evaluation_service import EvaluationService

evaluation_bp = Blueprint('evaluation_bp', __name__)

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
        result = EvaluationService.get_class_details(class_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500