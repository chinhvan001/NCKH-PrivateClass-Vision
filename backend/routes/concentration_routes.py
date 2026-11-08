"""
Presentation Tier (Routes / Controller): Concentration Routes
Chịu trách nhiệm tiếp nhận và điều hướng HTTP Requests từ các camera-ai edge nodes:
- Nhận HTTP POST request định kỳ 3-5 giây chứa thông tin học sinh, behavior_state, duration_counter.
- Kiểm tra tính toàn vẹn và hợp lệ của dữ liệu đầu vào (Input Validation).
- Gọi Use Case / Service của Business Logic Tier để tính toán và lưu trữ.
- Trả về chuẩn HTTP Response (200 OK, 400 Bad Request, 500 Internal Server Error).
"""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from services.concentration_service import ConcentrationService, VALID_BEHAVIOR_STATES

logger = logging.getLogger("concentration.routes")

concentration_bp = Blueprint("concentration", __name__, url_prefix="/api/v1/concentration")

# Khởi tạo service dùng chung cho controller
_service = ConcentrationService()


def _validate_student_item(item: dict, index: int) -> list[str]:
    """Kiểm tra tính hợp lệ của từng bản ghi học sinh trong payload."""
    errors = []
    if not isinstance(item, dict):
        return [f"Phần tử thứ {index} trong danh sách students phải là một JSON object."]

    student_id = item.get("student_id")
    if not student_id or not isinstance(student_id, (str, int)) or not str(student_id).strip():
        errors.append(f"Học sinh tại mục {index}: thiếu hoặc không hợp lệ trường 'student_id'.")

    behavior_state = item.get("behavior_state")
    if not behavior_state or not isinstance(behavior_state, str):
        errors.append(f"Học sinh tại mục {index}: thiếu trường 'behavior_state'.")
    elif behavior_state.strip().lower() not in VALID_BEHAVIOR_STATES:
        errors.append(
            f"Học sinh tại mục {index}: 'behavior_state'='{behavior_state}' không hợp lệ. "
            f"Các giá trị hợp lệ: {sorted(VALID_BEHAVIOR_STATES)}."
        )

    duration = item.get("duration_counter")
    if duration is not None:
        try:
            val = float(duration)
            if val < 0:
                errors.append(f"Học sinh tại mục {index}: 'duration_counter' phải >= 0.")
        except (ValueError, TypeError):
            errors.append(f"Học sinh tại mục {index}: 'duration_counter' phải là một số thực hoặc số nguyên.")

    return errors


@concentration_bp.route("/process-score", methods=["POST"])
def process_score():
    """
    Endpoint chính tiếp nhận HTTP POST payload từ camera-ai edge node định kỳ mỗi 3-5 giây.
    
    Cấu trúc Request Body mẫu:
    {
        "classroom_id": "CR_101",
        "students": [
            {
                "student_id": "ST_001",
                "behavior_state": "attentive",
                "duration_counter": 5.0,
                "seat_id": "S01"
            },
            {
                "student_id": "ST_002",
                "behavior_state": "using_phone",
                "duration_counter": 25.0,
                "seat_id": "S02"
            }
        ]
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Content-Type phải là application/json."
            }), 400

        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "Request body JSON không được để trống hoặc sai định dạng."
            }), 400

        # Lấy classroom_id từ body hoặc query param
        classroom_id = data.get("classroom_id") or request.args.get("classroom_id")
        if not classroom_id or not isinstance(classroom_id, str) or not classroom_id.strip():
            return jsonify({
                "success": False,
                "message": "Trường 'classroom_id' là bắt buộc và phải là chuỗi ký tự hợp lệ."
            }), 400

        classroom_id = classroom_id.strip()

        # Kiểm tra danh sách học sinh
        students = data.get("students")
        if not students or not isinstance(students, list):
            return jsonify({
                "success": False,
                "message": "Trường 'students' phải là một danh sách (array) chứa thông tin các học sinh."
            }), 400

        # Validate từng phần tử học sinh
        validation_errors = []
        for idx, student in enumerate(students):
            errors = _validate_student_item(student, idx)
            validation_errors.extend(errors)

        if validation_errors:
            return jsonify({
                "success": False,
                "message": "Dữ liệu học sinh không hợp lệ.",
                "errors": validation_errors
            }), 400

        # Chuyển quyền xử lý xuống Business Logic Tier
        result = _service.process_camera_ai_payload(classroom_id, students)

        return jsonify({
            "success": True,
            "message": "Tính toán và cập nhật điểm tập trung học sinh thành công.",
            "data": result
        }), 200

    except ValueError as ve:
        logger.warning("Validation error in process_score: %s", str(ve))
        return jsonify({
            "success": False,
            "message": str(ve)
        }), 400

    except Exception as exc:
        logger.error("Internal error processing camera AI score: %s", str(exc), exc_info=True)
        return jsonify({
            "success": False,
            "message": "Lỗi máy chủ nội bộ trong quá trình xử lý điểm tập trung.",
            "error_detail": str(exc)
        }), 500


@concentration_bp.route("/classrooms/<classroom_id>/live-scores", methods=["POST"])
def process_classroom_scores(classroom_id: str):
    """
    Endpoint linh hoạt với classroom_id nằm trên đường dẫn URL.
    Cho phép camera-ai gửi trực tiếp POST tới:
    /api/v1/concentration/classrooms/{classroom_id}/live-scores
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Content-Type phải là application/json."
            }), 400

        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "Request body JSON không được để trống hoặc sai định dạng."
            }), 400

        students = data.get("students")
        if not students or not isinstance(students, list):
            return jsonify({
                "success": False,
                "message": "Trường 'students' phải là một danh sách (array)."
            }), 400

        validation_errors = []
        for idx, student in enumerate(students):
            errors = _validate_student_item(student, idx)
            validation_errors.extend(errors)

        if validation_errors:
            return jsonify({
                "success": False,
                "message": "Dữ liệu học sinh không hợp lệ.",
                "errors": validation_errors
            }), 400

        result = _service.process_camera_ai_payload(classroom_id, students)

        return jsonify({
            "success": True,
            "message": f"Cập nhật thành công điểm tập trung cho lớp {classroom_id}.",
            "data": result
        }), 200

    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as exc:
        logger.error("Internal error in process_classroom_scores: %s", str(exc), exc_info=True)
        return jsonify({
            "success": False,
            "message": "Lỗi máy chủ nội bộ trong quá trình xử lý điểm tập trung.",
            "error_detail": str(exc)
        }), 500


@concentration_bp.route("/history/<classroom_id>/<student_id>", methods=["GET"])
def get_student_history(classroom_id: str, student_id: str):
    """
    Truy vấn chuỗi lịch sử điểm số của một học sinh phục vụ vẽ biểu đồ thống kê cuối giờ.
    Query param: ?limit=120
    """
    try:
        limit = request.args.get("limit", default=120, type=int)
        if limit <= 0 or limit > 1000:
            limit = 120

        logs = _service.get_student_history(classroom_id, student_id, limit=limit)
        return jsonify({
            "success": True,
            "classroom_id": classroom_id,
            "student_id": student_id,
            "total_records": len(logs),
            "history_logs": logs
        }), 200

    except Exception as exc:
        logger.error("Error retrieving student history: %s", str(exc), exc_info=True)
        return jsonify({
            "success": False,
            "message": "Không thể lấy lịch sử điểm tập trung.",
            "error_detail": str(exc)
        }), 500
