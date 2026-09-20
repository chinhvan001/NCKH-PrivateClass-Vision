from flask import Blueprint, jsonify
from firebase_config import db
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
    get_json_body,
)


session_bp = Blueprint(
    "session_bp",
    __name__
)


def authorize_admin():

    decoded_token = verify_request_token()

    if not decoded_token:
        return (
            None,
            jsonify({
                "success": False,
                "message": "Unauthorized."
            }),
            401
        )

    _, current_user = get_current_user(
        decoded_token
    )

    if not current_user:
        return (
            None,
            jsonify({
                "success": False,
                "message": "Tài khoản không tồn tại."
            }),
            403
        )

    if not is_admin_user(current_user):
        return (
            None,
            jsonify({
                "success": False,
                "message": "Bạn không có quyền truy cập."
            }),
            403
        )

    return current_user, None, None


def build_session_data(doc):

    data = doc.to_dict() or {}

    class_id = data.get("class_id")
    teacher_uid = data.get("teacher_uid")
    classroom_id = data.get("classroom_id")

    class_name = ""
    teacher_name = ""
    classroom_name = ""

    if class_id:

        class_doc = db.collection(
            "classes"
        ).document(class_id).get()

        if class_doc.exists:
            class_data = class_doc.to_dict() or {}

            class_name = class_data.get(
                "class_name",
                ""
            )

    if teacher_uid:

        teacher_doc = db.collection(
            "users"
        ).document(teacher_uid).get()

        if teacher_doc.exists:
            teacher_data = teacher_doc.to_dict() or {}

            teacher_name = teacher_data.get(
                "name",
                ""
            )

    if classroom_id:

        classroom_doc = db.collection(
            "classrooms"
        ).document(classroom_id).get()

        if classroom_doc.exists:
            classroom_data = (
                classroom_doc.to_dict()
                or {}
            )

            classroom_name = (
                classroom_data.get("class_name")
                or classroom_data.get("room_name")
                or classroom_data.get("name")
                or ""
            )

    return {
        "id": doc.id,
        "class_id": class_id,
        "class_name": class_name,
        "teacher_uid": teacher_uid,
        "teacher_name": teacher_name,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "subject": data.get(
            "subject",
            ""
        ),
        "date": data.get(
            "date",
            ""
        ),
        "start": data.get(
            "start",
            ""
        ),
        "end": data.get(
            "end",
            ""
        ),
        "status": data.get(
            "status",
            "scheduled"
        ),
        "focus": data.get(
            "focus"
        ),
    }


@session_bp.route(
    "/api/admin/sessions",
    methods=["GET"]
)
def get_sessions():

    _, error_response, error_code = authorize_admin()

    if error_response:
        return error_response, error_code

    try:

        sessions = []

        docs = (
            db.collection("sessions")
            .order_by("date")
            .stream()
        )

        for doc in docs:
            sessions.append(
                build_session_data(doc)
            )

        return jsonify({
            "success": True,
            "sessions": sessions,
            "total": len(sessions),
        }), 200

    except Exception as error:

        print(
            "Get sessions error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể lấy danh sách phiên học."
        }), 500


@session_bp.route(
    "/api/admin/sessions",
    methods=["POST"]
)
def create_session():

    _, error_response, error_code = authorize_admin()

    if error_response:
        return error_response, error_code

    try:

        data = get_json_body()

        class_id = str(
            data.get("class_id", "")
        ).strip()

        date = str(
            data.get("date", "")
        ).strip()

        start = str(
            data.get("start", "")
        ).strip()

        end = str(
            data.get("end", "")
        ).strip()

        if not class_id:
            return jsonify({
                "success": False,
                "message": "Vui lòng chọn lớp học."
            }), 400

        if not date:
            return jsonify({
                "success": False,
                "message": "Ngày học không được để trống."
            }), 400

        if not start or not end:
            return jsonify({
                "success": False,
                "message": "Vui lòng nhập thời gian phiên học."
            }), 400

        class_ref = db.collection(
            "classes"
        ).document(class_id)

        class_doc = class_ref.get()

        if not class_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy lớp học."
            }), 404

        class_data = class_doc.to_dict() or {}

        if class_data.get(
            "is_active",
            True
        ) is False:

            return jsonify({
                "success": False,
                "message": "Lớp học đang không hoạt động."
            }), 400

        session_data = {
            "class_id": class_id,
            "teacher_uid": class_data.get(
                "teacher_uid"
            ),
            "classroom_id": class_data.get(
                "classroom_id"
            ),
            "subject": class_data.get(
                "subject",
                ""
            ),
            "date": date,
            "start": start,
            "end": end,
            "status": "scheduled",
            "focus": None,
        }

        session_ref = (
            db.collection("sessions")
            .document()
        )

        session_ref.set(session_data)

        return jsonify({
            "success": True,
            "message": "Tạo phiên học thành công.",
            "session": build_session_data(
                session_ref.get()
            ),
        }), 201

    except Exception as error:

        print(
            "Create session error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể tạo phiên học."
        }), 500


@session_bp.route(
    "/api/admin/sessions/<session_id>",
    methods=["PUT"]
)
def update_session(session_id):

    _, error_response, error_code = authorize_admin()

    if error_response:
        return error_response, error_code

    try:

        session_ref = db.collection(
            "sessions"
        ).document(session_id)

        session_doc = session_ref.get()

        if not session_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy phiên học."
            }), 404

        data = get_json_body()

        update_data = {}

        for field in [
            "date",
            "start",
            "end",
        ]:

            if field in data:

                value = str(
                    data.get(field, "")
                ).strip()

                if not value:
                    return jsonify({
                        "success": False,
                        "message": f"{field} không được để trống."
                    }), 400

                update_data[field] = value

        if "status" in data:

            allowed_statuses = {
                "scheduled",
                "live",
                "completed",
                "cancelled",
            }

            status = data.get("status")

            if status not in allowed_statuses:
                return jsonify({
                    "success": False,
                    "message": "Trạng thái phiên học không hợp lệ."
                }), 400

            update_data["status"] = status

        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu cần cập nhật."
            }), 400

        session_ref.update(
            update_data
        )

        return jsonify({
            "success": True,
            "message": "Cập nhật phiên học thành công.",
            "session": build_session_data(
                session_ref.get()
            ),
        }), 200

    except Exception as error:

        print(
            "Update session error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể cập nhật phiên học."
        }), 500


@session_bp.route(
    "/api/admin/sessions/<session_id>",
    methods=["DELETE"]
)
def delete_session(session_id):

    _, error_response, error_code = authorize_admin()

    if error_response:
        return error_response, error_code

    try:

        session_ref = db.collection(
            "sessions"
        ).document(session_id)

        session_doc = session_ref.get()

        if not session_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy phiên học."
            }), 404

        session_ref.delete()

        return jsonify({
            "success": True,
            "message": "Xóa phiên học thành công."
        }), 200

    except Exception as error:

        print(
            "Delete session error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể xóa phiên học."
        }), 500