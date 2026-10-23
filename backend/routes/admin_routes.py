from flask import Blueprint, jsonify, request
from firebase_admin import auth
import requests

from firebase_config import (
    db,
    FIREBASE_API_KEY,
)

from utils.auth import (
    get_current_user,
    get_json_body,
    is_admin_user,
    verify_request_token,
)


FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)


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

    try:
        teachers_ref = db.collection("teachers")
        teachers = []

        for doc in teachers_ref.stream():
            teacher_data = doc.to_dict() or {}

            teachers.append({
                "id": doc.id,
                "uid": teacher_data.get("uid"),
                "email": teacher_data.get("email", ""),
                "name": teacher_data.get("name", ""),
                "phone_number": teacher_data.get(
                    "phone_number",
                    ""
                ),
                "is_active": teacher_data.get(
                    "is_active",
                    True
                ),
                "subject": teacher_data.get(
                    "subject",
                    ""
                ),
                "create_date": teacher_data.get(
                    "create_date"
                ),
                "auth_provider": teacher_data.get(
                    "auth_provider",
                    ""
                ),
                "auth_status": teacher_data.get(
                    "auth_status",
                    ""
                )
            })

        return jsonify({
            "success": True,
            "users": teachers,
            "total": len(teachers)
        }), 200

    except Exception as error:
        print("Get teachers error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể lấy danh sách giáo viên."
        }), 500


@admin_bp.route("/api/admin/teachers", methods=["POST"])
def create_teacher():
    uid, admin_data, error_response = require_admin()

    if error_response:
        return error_response

    try:
        data = get_json_body()

        name = str(
            data.get("name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        subject = str(
            data.get("subject", "")
        ).strip()

        is_active = data.get(
            "is_active",
            True
        )

        if not name:
            return jsonify({
                "success": False,
                "message": "Họ và tên không được để trống."
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "message": "Email không được để trống."
            }), 400

        if not subject:
            return jsonify({
                "success": False,
                "message": "Bộ môn không được để trống."
            }), 400

        if not isinstance(is_active, bool):
            return jsonify({
                "success": False,
                "message": "is_active phải là true hoặc false."
            }), 400

        existing_teachers = (
            db.collection("teachers")
            .where(
                "email",
                "==",
                email
            )
            .limit(1)
            .stream()
        )

        existing_teacher = next(
            existing_teachers,
            None
        )

        if existing_teacher:
            return jsonify({
                "success": False,
                "message": "Email này đã được sử dụng."
            }), 409

        teacher_data = {
            "uid": None,
            "email": email,
            "name": name,
            "phone_number": phone_number,
            "subject": subject,
            "is_active": is_active,
            "auth_provider": "google",
            "auth_status": "pending"
        }

        doc_ref = db.collection(
            "teachers"
        ).document()

        doc_ref.set(
            teacher_data
        )

        return jsonify({
            "success": True,
            "message": "Thêm tài khoản giáo viên thành công.",
            "user": {
                **teacher_data,
                "id": doc_ref.id
            }
        }), 201

    except Exception as error:
        print("Create teacher error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể thêm tài khoản giáo viên."
        }), 500


@admin_bp.route("/api/users/<uid>", methods=["PUT"])
def update_teacher(uid):
    admin_uid, admin_data, error_response = require_admin()

    if error_response:
        return error_response

    try:
        teacher_ref = db.collection(
            "teachers"
        ).document(uid)

        teacher_doc = teacher_ref.get()

        if not teacher_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy tài khoản giáo viên."
            }), 404

        current_teacher = (
            teacher_doc.to_dict() or {}
        )

        data = get_json_body()
        update_data = {}

        if "name" in data:
            name = str(
                data.get("name", "")
            ).strip()

            if not name:
                return jsonify({
                    "success": False,
                    "message": "Họ tên không được để trống."
                }), 400

            update_data["name"] = name

        if "phone_number" in data:
            phone_number = str(
                data.get("phone_number", "")
            ).strip()

            update_data["phone_number"] = phone_number

        if "subject" in data:
            subject = str(
                data.get("subject", "")
            ).strip()

            if not subject:
                return jsonify({
                    "success": False,
                    "message": "Bộ môn không được để trống."
                }), 400

            update_data["subject"] = subject

        if "is_active" in data:
            if not isinstance(
                data.get("is_active"),
                bool
            ):
                return jsonify({
                    "success": False,
                    "message": "is_active phải là true hoặc false."
                }), 400

            update_data["is_active"] = data.get(
                "is_active"
            )

        if not update_data:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu cần cập nhật."
            }), 400

        teacher_ref.update(
            update_data
        )

        updated_teacher = {
            **current_teacher,
            **update_data
        }

        return jsonify({
            "success": True,
            "message": "Cập nhật tài khoản giáo viên thành công.",
            "user": {
                "id": uid,
                "uid": updated_teacher.get(
                    "uid"
                ),
                "email": updated_teacher.get(
                    "email",
                    ""
                ),
                "name": updated_teacher.get(
                    "name",
                    ""
                ),
                "phone_number": updated_teacher.get(
                    "phone_number",
                    ""
                ),
                "is_active": updated_teacher.get(
                    "is_active",
                    True
                ),
                "subject": updated_teacher.get(
                    "subject",
                    ""
                ),
                "auth_provider": updated_teacher.get(
                    "auth_provider",
                    ""
                ),
                "auth_status": updated_teacher.get(
                    "auth_status",
                    ""
                )
            }
        }), 200

    except Exception as error:
        print("Update teacher error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể cập nhật tài khoản giáo viên."
        }), 500


@admin_bp.route("/api/admin/teachers/<uid>", methods=["DELETE"])
def delete_teacher(uid):
    admin_uid, admin_data, error_response = require_admin()

    if error_response:
        return error_response

    try:
        teacher_ref = db.collection(
            "teachers"
        ).document(uid)

        teacher_doc = teacher_ref.get()

        if not teacher_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy tài khoản giáo viên."
            }), 404

        teacher_data = (
            teacher_doc.to_dict() or {}
        )

        firebase_uid = teacher_data.get(
            "uid"
        )

        if firebase_uid:
            try:
                auth.delete_user(
                    firebase_uid
                )
            except auth.UserNotFoundError:
                pass

        teacher_ref.delete()

        return jsonify({
            "success": True,
            "message": "Xóa tài khoản giáo viên thành công.",
            "uid": firebase_uid,
            "id": uid
        }), 200

    except Exception as error:
        print("Delete teacher error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể xóa tài khoản giáo viên."
        }), 500


@admin_bp.route(
    "/api/admin/profile/<uid>",
    methods=["GET"]
)
def get_admin_profile(uid):
    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    current_uid = decoded_token.get(
        "uid"
    )

    if current_uid != uid:
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền xem profile này."
        }), 403

    admin_ref = db.collection(
        "admins"
    ).document(uid)

    admin_doc = admin_ref.get()

    if not admin_doc.exists:
        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản admin."
        }), 404

    admin_data = (
        admin_doc.to_dict() or {}
    )

    if not is_admin_user(admin_data):
        return jsonify({
            "success": False,
            "message": "Tài khoản admin đã bị vô hiệu hóa."
        }), 403

    return jsonify({
        "success": True,
        "user": {
            "uid": uid,
            "email": admin_data.get(
                "email",
                ""
            ),
            "name": admin_data.get(
                "name",
                ""
            ),
            "phone_number": admin_data.get(
                "phone_number",
                ""
            ),
            "school": admin_data.get(
                "school",
                ""
            ),
            "is_active": admin_data.get(
                "is_active",
                True
            )
        }
    }), 200


@admin_bp.route(
    "/api/admin/profile/<uid>",
    methods=["PUT"]
)
def update_admin_profile(uid):
    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    current_uid = decoded_token.get(
        "uid"
    )

    if current_uid != uid:
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền chỉnh sửa profile này."
        }), 403

    admin_ref = db.collection(
        "admins"
    ).document(uid)

    admin_doc = admin_ref.get()

    if not admin_doc.exists:
        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản admin."
        }), 404

    current_admin = (
        admin_doc.to_dict() or {}
    )

    if not is_admin_user(current_admin):
        return jsonify({
            "success": False,
            "message": "Tài khoản admin đã bị vô hiệu hóa."
        }), 403

    data = get_json_body()
    update_data = {}

    if "name" in data:
        name = str(
            data.get("name", "")
        ).strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Họ tên không được để trống."
            }), 400

        update_data["name"] = name

    if "phone_number" in data:
        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        update_data["phone_number"] = phone_number

    if not update_data:
        return jsonify({
            "success": False,
            "message": "Không có dữ liệu cần cập nhật."
        }), 400

    try:
        admin_ref.update(
            update_data
        )

        updated_admin = {
            **current_admin,
            **update_data
        }

        return jsonify({
            "success": True,
            "message": "Cập nhật profile thành công.",
            "user": {
                "uid": uid,
                "email": updated_admin.get(
                    "email",
                    ""
                ),
                "name": updated_admin.get(
                    "name",
                    ""
                ),
                "phone_number": updated_admin.get(
                    "phone_number",
                    ""
                ),
                "school": updated_admin.get(
                    "school",
                    ""
                ),
                "is_active": updated_admin.get(
                    "is_active",
                    True
                )
            }
        }), 200

    except Exception as error:
        print("Update admin profile error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể cập nhật profile."
        }), 500


@admin_bp.route(
    "/api/admin/change-password",
    methods=["POST"]
)
def change_admin_password():
    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    uid = decoded_token.get(
        "uid"
    )

    if not uid:
        return jsonify({
            "success": False,
            "message": "Token không hợp lệ."
        }), 401

    admin_ref = db.collection(
        "admins"
    ).document(uid)

    admin_doc = admin_ref.get()

    if not admin_doc.exists:
        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản admin."
        }), 404

    admin_data = (
        admin_doc.to_dict() or {}
    )

    if not is_admin_user(admin_data):
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền đổi mật khẩu."
        }), 403

    data = get_json_body()

    current_password = data.get(
        "currentPassword",
        ""
    )

    new_password = data.get(
        "newPassword",
        ""
    )

    if not current_password or not new_password:
        return jsonify({
            "success": False,
            "message": (
                "Vui lòng nhập đầy đủ mật khẩu "
                "hiện tại và mật khẩu mới."
            )
        }), 400

    if len(new_password) < 6:
        return jsonify({
            "success": False,
            "message": (
                "Mật khẩu mới phải có ít nhất 6 ký tự."
            )
        }), 400

    if current_password == new_password:
        return jsonify({
            "success": False,
            "message": (
                "Mật khẩu mới phải khác "
                "mật khẩu hiện tại."
            )
        }), 400

    email = admin_data.get(
        "email",
        ""
    )

    if not email:
        return jsonify({
            "success": False,
            "message": "Tài khoản không có email."
        }), 400

    try:
        response = requests.post(
            f"{FIREBASE_SIGN_IN_URL}?key={FIREBASE_API_KEY}",
            json={
                "email": email,
                "password": current_password,
                "returnSecureToken": True
            },
            timeout=10
        )

        firebase_data = response.json()

        if response.status_code != 200:
            error_message = (
                firebase_data
                .get("error", {})
                .get("message", "")
            )

            print(
                "Current password verification error:",
                error_message
            )

            if error_message in {
                "INVALID_LOGIN_CREDENTIALS",
                "INVALID_PASSWORD"
            }:
                return jsonify({
                    "success": False,
                    "message": (
                        "Mật khẩu hiện tại không chính xác."
                    )
                }), 401

            return jsonify({
                "success": False,
                "message": (
                    "Không thể xác minh "
                    "mật khẩu hiện tại."
                )
            }), 401

        auth.update_user(
            uid,
            password=new_password
        )

        return jsonify({
            "success": True,
            "message": "Đổi mật khẩu thành công."
        }), 200

    except requests.RequestException as error:
        print(
            "Firebase password verification error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể kết nối đến Firebase."
        }), 503

    except Exception as error:
        print(
            "Change password error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Không thể đổi mật khẩu."
        }), 500