from flask import Blueprint, jsonify, request
from firebase_admin import auth
import requests

from firebase_config import (
    db,
    FIREBASE_API_KEY,
)

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

from utils.auth import (
    ADMIN_ROLES,
    TEACHER_ROLE,
    get_current_user,
    get_json_body,
    is_admin_user,
    normalize_subjects,
    verify_request_token,
)


admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/api/admin/users", methods=["GET"])
def get_admin_users():

    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Tài khoản không tồn tại."
        }), 403

    if not is_admin_user(current_user):
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền truy cập."
        }), 403

    try:
        users_ref = db.collection("users")
        users = []

        for doc in users_ref.stream():

            user_data = doc.to_dict()

            roles = user_data.get("role", [])

            if isinstance(roles, str):
                roles = [roles]

            if TEACHER_ROLE not in roles:
                continue

            users.append({
                "id": doc.id,

                "uid": user_data.get(
                    "uid",
                    doc.id
                ),

                "email": user_data.get(
                    "email",
                    ""
                ),

                "name": user_data.get(
                    "name",
                    ""
                ),

                "phone_number": user_data.get(
                    "phone_number",
                    ""
                ),

                "role": roles,

                "is_active": user_data.get(
                    "is_active",
                    True
                ),

                "subject": user_data.get(
                    "subject",
                    ""
                ),

                "create_date": user_data.get(
                    "create_date"
                ),

                "active_role": user_data.get(
                    "active_role",
                    ""
                )
            })

        return jsonify({
            "success": True,
            "users": users,
            "total": len(users)
        }), 200

    except Exception as error:

        print("Get admin users error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể lấy danh sách giáo viên."
        }), 500

@admin_bp.route("/api/admin/teachers", methods=["POST"])
def create_teacher():
    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Tài khoản admin không tồn tại."
        }), 403

    if not is_admin_user(current_user):
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền thêm giáo viên."
        }), 403

    try:
        data = get_json_body()

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        phone_number = str(
            data.get("phone_number", "")
        ).strip()
        subject = str(
            data.get("subject", "")
        ).strip()

        requested_roles = data.get(
            "role",
            [TEACHER_ROLE]
        )

        if isinstance(requested_roles, str):
            requested_roles = [requested_roles]

        # =========================
        # VALIDATE
        # =========================

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

        # =========================
        # ROLE
        # =========================

        roles = [TEACHER_ROLE]

        if "parent" in requested_roles:
            roles.append("parent")

        # =========================
        # STATUS
        # =========================

        is_active = data.get("is_active", True)

        if not isinstance(is_active, bool):
            return jsonify({
                "success": False,
                "message": "is_active phải là true hoặc false."
            }), 400

        existing_users = db.collection("users").where(
            "email",
            "==",
            email
        ).limit(1).stream()

        existing_user = next(existing_users, None)

        if existing_user:
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
            "role": roles,
            "is_active": is_active,
            "active_role": TEACHER_ROLE,
            "auth_provider": "google",
            "auth_status": "pending"
        }

        doc_ref = db.collection("users").document(email)
        doc_ref.set(teacher_data)

        return jsonify({
            "success": True,
            "message": "Thêm tài khoản giáo viên thành công.",
            "user": {
                **teacher_data,
                "id": email
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

    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Tài khoản admin không tồn tại."
        }), 403

    if not is_admin_user(current_user):
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền chỉnh sửa tài khoản."
        }), 403

    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy tài khoản giáo viên."
            }), 404

        current_teacher = user_doc.to_dict()

        roles = current_teacher.get("role", [])

        if isinstance(roles, str):
            roles = [roles]

        if "teacher" not in roles:
            return jsonify({
                "success": False,
                "message": "API này chỉ dùng để cập nhật tài khoản giáo viên."
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

        user_ref.update(update_data)

        updated_user = {
            **current_teacher,
            **update_data,
            "uid": uid,
            "role": roles
        }

        return jsonify({
            "success": True,
            "message": "Cập nhật tài khoản giáo viên thành công.",
            "user": {
                "uid": uid,

                "email": updated_user.get(
                    "email",
                    ""
                ),

                "name": updated_user.get(
                    "name",
                    ""
                ),

                "phone_number": updated_user.get(
                    "phone_number",
                    ""
                ),

                "role": updated_user.get(
                    "role",
                    roles
                ),

                "is_active": updated_user.get(
                    "is_active",
                    True
                ),

                "subject": updated_user.get(
                    "subject",
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
    decoded_token = verify_request_token()

    if not decoded_token:
        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Tài khoản admin không tồn tại."
        }), 403

    if not is_admin_user(current_user):
        return jsonify({
            "success": False,
            "message": "Bạn không có quyền xóa giáo viên."
        }), 403

    try:


        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy tài khoản giáo viên."
            }), 404

        teacher_data = user_doc.to_dict()


        roles = teacher_data.get("role", [])

        if isinstance(roles, str):
            roles = [roles]

        if TEACHER_ROLE not in roles:
            return jsonify({
                "success": False,
                "message": "Tài khoản này không phải giáo viên."
            }), 403


        if "parent" in roles:
            new_roles = [
                role for role in roles
                if role != TEACHER_ROLE
            ]

            user_ref.update({
                "role": new_roles,
                "active_role": "parent"
            })

            return jsonify({
                "success": True,
                "message": (
                    "Đã xóa quyền giáo viên. "
                    "Tài khoản phụ huynh vẫn được giữ lại."
                ),
                "deleted_teacher_role_only": True,
                "uid": uid
            }), 200

        try:
            auth.delete_user(uid)
        except auth.UserNotFoundError:
            pass

        user_ref.delete()

        return jsonify({
            "success": True,
            "message": "Xóa tài khoản giáo viên thành công.",
            "deleted_teacher_role_only": False,
            "uid": uid
        }), 200

    except Exception as error:
        print("Delete teacher error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể xóa tài khoản giáo viên."
        }), 500

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

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:

        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản."
        }), 404

    user_data = user_doc.to_dict()

    if user_data.get("role") not in ADMIN_ROLES:

        return jsonify({
            "success": False,
            "message": "Tài khoản không phải admin."
        }), 403

    return jsonify({
        "success": True,
        "user": {
            "uid": uid,
            "email": user_data.get(
                "email",
                ""
            ),
            "name": user_data.get(
                "name",
                ""
            ),
            "phone_number": user_data.get(
                "phone_number",
                ""
            ),
            "role": user_data.get(
                "role",
                "admin"
            ),
            "is_active": user_data.get(
                "is_active",
                True
            )
        }
    }), 200

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

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:

        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản."
        }), 404

    current_user = user_doc.to_dict()

    if not is_admin_user(current_user):

        return jsonify({
            "success": False,
            "message": "Tài khoản không có quyền admin."
        }), 403

    data = get_json_body()

    update_data = {}

    if "name" in data:

        name = str(data.get("name", "")).strip()

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

        user_ref.update(update_data)

        updated_user = {
            **current_user,
            **update_data
        }

        return jsonify({
            "success": True,
            "message": "Cập nhật profile thành công.",
            "user": {
                "uid": uid,
                "email": updated_user.get(
                    "email",
                    ""
                ),
                "name": updated_user.get(
                    "name",
                    ""
                ),
                "phone_number": updated_user.get(
                    "phone_number",
                    ""
                ),
                "role": updated_user.get(
                    "role",
                    "admin"
                ),
                "is_active": updated_user.get(
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

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:

        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản."
        }), 404

    user_data = user_doc.to_dict()

    if not is_admin_user(user_data):

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
            "message": "Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới."
        }), 400

    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "message": "Mật khẩu mới phải có ít nhất 6 ký tự."
        }), 400

    if current_password == new_password:

        return jsonify({
            "success": False,
            "message": "Mật khẩu mới phải khác mật khẩu hiện tại."
        }), 400

    email = user_data.get("email")

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
                    "message": "Mật khẩu hiện tại không chính xác."
                }), 401

            return jsonify({
                "success": False,
                "message": "Không thể xác minh mật khẩu hiện tại."
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

