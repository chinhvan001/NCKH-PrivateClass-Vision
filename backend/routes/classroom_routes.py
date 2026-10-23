from flask import Blueprint, jsonify, request
from firebase_config import db
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
    get_json_body,
)

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

def normalize_int(value, field_name, default=None):
    if value is None or value == "":
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} phải là số nguyên")


def build_classroom_data(doc):
    data = doc.to_dict() or {}

    return {
        "id": doc.id,
        "classroom_name": data.get("classroom_name", ""),
        "camera_name": data.get("camera_name", ""),
        "ip_address": data.get("ip_address", ""),
        "rtsp_port": data.get("rtsp_port", ""),
        "rtsp_url": data.get("rtsp_url", ""),
        "row_number": data.get("row_number", 0),
        "column_number": data.get("column_number", 0),
        "status": data.get("status", "offline"),
    }


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
        try:
            classrooms_ref = db.collection("classrooms").stream()

            classroom_list = []

            for doc in classrooms_ref:
                classroom_list.append(build_classroom_data(doc))

            classroom_list.sort(
                key=lambda item: item.get("classroom_name", "")
            )

            return jsonify({
                "success": True,
                "classrooms": classroom_list,
                "total": len(classroom_list),
            }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Không thể lấy danh sách phòng học: {str(e)}"
            }), 500

    try:
        data = get_json_body()

        classroom_name = str(
            data.get("classroom_name", "")
        ).strip()

        if not classroom_name:
            return jsonify({
                "success": False,
                "message": "Tên phòng học là bắt buộc"
            }), 400

        existing_classrooms = db.collection("classrooms").where(
            "classroom_name",
            "==",
            classroom_name
        ).stream()

        for doc in existing_classrooms:
            return jsonify({
                "success": False,
                "message": "Phòng học đã tồn tại"
            }), 409

        camera_name = str(
            data.get("camera_name", "")
        ).strip()

        ip_address = str(
            data.get("ip_address", "")
        ).strip()

        rtsp_port = str(
            data.get("rtsp_port", "")
        ).strip()

        rtsp_url = str(
            data.get("rtsp_url", "")
        ).strip()

        status = str(
            data.get("status", "offline")
        ).strip().lower()

        if status not in ["online", "offline"]:
            status = "offline"

        try:
            row_number = normalize_int(
                data.get("row_number"),
                "row_number",
                0
            )

            column_number = normalize_int(
                data.get("column_number"),
                "column_number",
                0
            )
        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        if row_number < 0 or column_number < 0:
            return jsonify({
                "success": False,
                "message": "Số hàng và số cột không được nhỏ hơn 0"
            }), 400

        classroom_data = {
            "classroom_name": classroom_name,
            "camera_name": camera_name,
            "ip_address": ip_address,
            "rtsp_port": rtsp_port,
            "rtsp_url": rtsp_url,
            "row_number": row_number,
            "column_number": column_number,
            "status": status,
        }

        classroom_id = str(
            data.get("id", "")
        ).strip()

        if classroom_id:
            classroom_ref = db.collection("classrooms").document(
                classroom_id
            )

            if classroom_ref.get().exists:
                return jsonify({
                    "success": False,
                    "message": "ID phòng học đã tồn tại"
                }), 409

            classroom_ref.set(classroom_data)
        else:
            classroom_ref = db.collection("classrooms").document()
            classroom_ref.set(classroom_data)

        classroom_doc = classroom_ref.get()

        return jsonify({
            "success": True,
            "message": "Tạo phòng học thành công",
            "classroom": build_classroom_data(classroom_doc),
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Không thể tạo phòng học: {str(e)}"
        }), 500


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

    classroom_ref = db.collection("classrooms").document(classroom_id)

    try:
        classroom_doc = classroom_ref.get()

        if not classroom_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy phòng học"
            }), 404

        if request.method == "DELETE":
            classes_ref = db.collection("classes").where(
                "classroom_id",
                "==",
                classroom_id
            ).stream()

            linked_classes = list(classes_ref)

            if linked_classes:
                return jsonify({
                    "success": False,
                    "message": "Không thể xóa phòng học đang được sử dụng bởi lớp học"
                }), 409

            classroom_ref.delete()

            return jsonify({
                "success": True,
                "message": "Xóa phòng học thành công"
            }), 200

        data = get_json_body()

        current_data = classroom_doc.to_dict() or {}

        classroom_name = str(
            data.get(
                "classroom_name",
                current_data.get("classroom_name", "")
            )
        ).strip()

        if not classroom_name:
            return jsonify({
                "success": False,
                "message": "Tên phòng học là bắt buộc"
            }), 400

        if classroom_name != current_data.get("classroom_name", ""):
            existing_classrooms = db.collection("classrooms").where(
                "classroom_name",
                "==",
                classroom_name
            ).stream()

            for doc in existing_classrooms:
                if doc.id != classroom_id:
                    return jsonify({
                        "success": False,
                        "message": "Phòng học đã tồn tại"
                    }), 409

        try:
            row_number = normalize_int(
                data.get(
                    "row_number",
                    current_data.get("row_number", 0)
                ),
                "row_number",
                0
            )

            column_number = normalize_int(
                data.get(
                    "column_number",
                    current_data.get("column_number", 0)
                ),
                "column_number",
                0
            )
        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        if row_number < 0 or column_number < 0:
            return jsonify({
                "success": False,
                "message": "Số hàng và số cột không được nhỏ hơn 0"
            }), 400

        status = str(
            data.get(
                "status",
                current_data.get("status", "offline")
            )
        ).strip().lower()

        if status not in ["online", "offline"]:
            status = "offline"

        updated_data = {
            "classroom_name": classroom_name,
            "camera_name": str(
                data.get(
                    "camera_name",
                    current_data.get("camera_name", "")
                )
            ).strip(),
            "ip_address": str(
                data.get(
                    "ip_address",
                    current_data.get("ip_address", "")
                )
            ).strip(),
            "rtsp_port": str(
                data.get(
                    "rtsp_port",
                    current_data.get("rtsp_port", "")
                )
            ).strip(),
            "rtsp_url": str(
                data.get(
                    "rtsp_url",
                    current_data.get("rtsp_url", "")
                )
            ).strip(),
            "row_number": row_number,
            "column_number": column_number,
            "status": status,
        }

        classroom_ref.update(updated_data)

        updated_doc = classroom_ref.get()

        return jsonify({
            "success": True,
            "message": "Cập nhật phòng học thành công",
            "classroom": build_classroom_data(updated_doc),
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Không thể xử lý phòng học: {str(e)}"
        }), 500