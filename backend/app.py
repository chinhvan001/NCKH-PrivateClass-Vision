from flask import Flask, jsonify, request
from flask_cors import CORS
from firebase_admin import auth
import requests

from firebase_config import db, FIREBASE_API_KEY


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# CONSTANTS
# =========================================================

ADMIN_ROLES = {"admin", "super_admin"}
TEACHER_ROLE = "teacher"

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)


# =========================================================
# COMMON HELPERS
# =========================================================

def verify_request_token():

    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    id_token = authorization.split("Bearer ", 1)[1].strip()

    if not id_token:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token

    except Exception as error:
        print("Token verification error:", error)
        return None


def get_current_user(decoded_token):

    if not decoded_token:
        return None, None

    uid = decoded_token.get("uid")

    if not uid:
        return None, None

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return None, None

    return user_ref, user_doc.to_dict()


def is_admin_user(user_data):

    if not user_data:
        return False

    role = user_data.get("role")
    is_active = user_data.get("is_active", True)

    return (
        role in ADMIN_ROLES
        and is_active is not False
    )


def get_json_body():

    return request.get_json(silent=True) or {}


def normalize_subjects(subjects):

    if subjects is None:
        return []

    if not isinstance(subjects, list):
        return None

    return [
        str(subject).strip()
        for subject in subjects
        if str(subject).strip()
    ]


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "PrivateClass Vision API is running"
    }), 200


# =========================================================
# AUTH - GOOGLE
# =========================================================

@app.route("/api/auth/google", methods=["POST"])
def google_login():

    data = get_json_body()

    id_token = data.get("idToken")

    if not id_token:
        return jsonify({
            "success": False,
            "message": "Thiếu Firebase ID Token."
        }), 400

    try:

        decoded_token = auth.verify_id_token(id_token)

        uid = decoded_token.get("uid")

        if not uid:
            return jsonify({
                "success": False,
                "message": "Firebase Token không hợp lệ."
            }), 401

        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:

            return jsonify({
                "success": False,
                "message": "Tài khoản chưa được cấp quyền truy cập."
            }), 403

        user_data = user_doc.to_dict()

        role = user_data.get("role")
        is_active = user_data.get("is_active", True)

        if role not in ADMIN_ROLES:

            return jsonify({
                "success": False,
                "message": "Tài khoản không có quyền truy cập Admin."
            }), 403

        if is_active is False:

            return jsonify({
                "success": False,
                "message": "Tài khoản đã bị vô hiệu hóa."
            }), 403

        return jsonify({
            "success": True,
            "message": "Đăng nhập Google thành công.",
            "user": {
                "uid": uid,
                "email": user_data.get(
                    "email",
                    decoded_token.get("email", "")
                ),
                "name": user_data.get("name", ""),
                "phone_number": user_data.get("phone_number", ""),
                "role": role,
                "is_active": is_active
            }
        }), 200

    except Exception as error:

        print("Google login error:", error)

        return jsonify({
            "success": False,
            "message": "Firebase Token không hợp lệ hoặc đã hết hạn."
        }), 401


# =========================================================
# AUTH - EMAIL / PASSWORD
# =========================================================

@app.route("/api/auth/email-password", methods=["POST"])
def email_password_login():

    data = get_json_body()

    email = str(data.get("email", "")).strip()
    password = data.get("password", "")

    # -----------------------------------------
    # Validate input
    # -----------------------------------------

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Vui lòng nhập email và mật khẩu."
        }), 400

    try:

        # -----------------------------------------
        # Verify Email / Password với Firebase
        # -----------------------------------------

        response = requests.post(
            f"{FIREBASE_SIGN_IN_URL}?key={FIREBASE_API_KEY}",
            json={
                "email": email,
                "password": password,
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

            print("Firebase email login error:", error_message)

            if error_message in {
                "INVALID_LOGIN_CREDENTIALS",
                "INVALID_PASSWORD",
                "EMAIL_NOT_FOUND"
            }:
                return jsonify({
                    "success": False,
                    "message": "Email hoặc mật khẩu không chính xác."
                }), 401

            if error_message == "USER_DISABLED":
                return jsonify({
                    "success": False,
                    "message": "Tài khoản đã bị vô hiệu hóa."
                }), 403

            return jsonify({
                "success": False,
                "message": "Không thể đăng nhập. Vui lòng thử lại."
            }), 401

        firebase_id_token = firebase_data.get("idToken")

        if not firebase_id_token:

            return jsonify({
                "success": False,
                "message": "Không nhận được Firebase ID Token."
            }), 401

        # -----------------------------------------
        # Verify token vừa nhận
        # -----------------------------------------

        decoded_token = auth.verify_id_token(firebase_id_token)

        uid = decoded_token.get("uid")

        if not uid:

            return jsonify({
                "success": False,
                "message": "Firebase Token không hợp lệ."
            }), 401

        # -----------------------------------------
        # Kiểm tra user trong Firestore
        # -----------------------------------------

        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:

            return jsonify({
                "success": False,
                "message": "Tài khoản chưa được cấp quyền truy cập."
            }), 403

        user_data = user_doc.to_dict()

        role = user_data.get("role")
        is_active = user_data.get("is_active", True)

        # -----------------------------------------
        # Kiểm tra quyền Admin
        # -----------------------------------------

        if role not in ADMIN_ROLES:

            return jsonify({
                "success": False,
                "message": "Tài khoản không có quyền truy cập Admin."
            }), 403

        # -----------------------------------------
        # Kiểm tra trạng thái
        # -----------------------------------------

        if is_active is False:

            return jsonify({
                "success": False,
                "message": "Tài khoản đã bị vô hiệu hóa."
            }), 403

        return jsonify({
            "success": True,
            "message": "Đăng nhập thành công.",
            "idToken": firebase_id_token,
            "user": {
                "uid": uid,
                "email": user_data.get("email", email),
                "name": user_data.get("name", ""),
                "phone_number": user_data.get(
                    "phone_number",
                    ""
                ),
                "role": role,
                "is_active": is_active
            }
        }), 200

    except requests.RequestException as error:

        print("Firebase request error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể kết nối đến Firebase."
        }), 503

    except Exception as error:

        print("Email/password login error:", error)

        return jsonify({
            "success": False,
            "message": "Đăng nhập thất bại."
        }), 500


# =========================================================
# ADMIN - GET TEACHERS
# =========================================================

@app.route("/api/admin/users", methods=["GET"])
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

    # Chỉ admin / super_admin
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

            # Chỉ lấy giáo viên
            if user_data.get("role") != TEACHER_ROLE:
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
                "role": user_data.get(
                    "role",
                    TEACHER_ROLE
                ),
                "is_active": user_data.get(
                    "is_active",
                    True
                ),
                "subject": normalize_subjects(
                    user_data.get("subject", [])
                ) or []
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


# =========================================================
# ADMIN - UPDATE TEACHER
# =========================================================

@app.route("/api/users/<uid>", methods=["PUT"])
def update_teacher(uid):

    # -----------------------------------------
    # Verify requester
    # -----------------------------------------

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

    # -----------------------------------------
    # Chỉ admin được sửa giáo viên
    # -----------------------------------------

    if not is_admin_user(current_user):

        return jsonify({
            "success": False,
            "message": "Bạn không có quyền chỉnh sửa tài khoản."
        }), 403

    # -----------------------------------------
    # Target user
    # -----------------------------------------

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:

        return jsonify({
            "success": False,
            "message": "Không tìm thấy tài khoản giáo viên."
        }), 404

    current_teacher = user_doc.to_dict()

    # Không cho admin dùng API này sửa admin khác
    if current_teacher.get("role") != TEACHER_ROLE:

        return jsonify({
            "success": False,
            "message": "API này chỉ dùng để cập nhật tài khoản giáo viên."
        }), 403

    # -----------------------------------------
    # Request body
    # -----------------------------------------

    data = get_json_body()

    update_data = {}

    # -----------------------------------------
    # Name
    # -----------------------------------------

    if "name" in data:

        name = str(data.get("name", "")).strip()

        if not name:

            return jsonify({
                "success": False,
                "message": "Họ tên không được để trống."
            }), 400

        update_data["name"] = name

    # -----------------------------------------
    # Phone number
    # -----------------------------------------

    if "phone_number" in data:

        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        update_data["phone_number"] = phone_number

    # -----------------------------------------
    # Subject
    # -----------------------------------------

    if "subject" in data:

        subjects = normalize_subjects(
            data.get("subject")
        )

        if subjects is None:

            return jsonify({
                "success": False,
                "message": "Bộ môn phải là một danh sách."
            }), 400

        update_data["subject"] = subjects

    # -----------------------------------------
    # Active status
    # -----------------------------------------

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

    # Không có field nào để update
    if not update_data:

        return jsonify({
            "success": False,
            "message": "Không có dữ liệu cần cập nhật."
        }), 400

    try:

        user_ref.update(update_data)

        updated_user = {
            **current_teacher,
            **update_data,
            "uid": uid
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
                    TEACHER_ROLE
                ),
                "is_active": updated_user.get(
                    "is_active",
                    True
                ),
                "subject": updated_user.get(
                    "subject",
                    []
                )
            }
        }), 200

    except Exception as error:

        print("Update teacher error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể cập nhật tài khoản giáo viên."
        }), 500


# =========================================================
# ADMIN - GET PROFILE
# =========================================================

@app.route("/api/admin/profile/<uid>", methods=["GET"])
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


# =========================================================
# ADMIN - UPDATE PROFILE
# =========================================================

@app.route("/api/admin/profile/<uid>", methods=["PUT"])
def update_admin_profile(uid):

    decoded_token = verify_request_token()

    if not decoded_token:

        return jsonify({
            "success": False,
            "message": "Unauthorized."
        }), 401

    current_uid = decoded_token.get("uid")

    # Chỉ sửa profile của chính mình
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

    # -----------------------------------------
    # Name
    # -----------------------------------------

    if "name" in data:

        name = str(data.get("name", "")).strip()

        if not name:

            return jsonify({
                "success": False,
                "message": "Họ tên không được để trống."
            }), 400

        update_data["name"] = name

    # -----------------------------------------
    # Phone
    # -----------------------------------------

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


# =========================================================
# ADMIN - CHANGE PASSWORD
# =========================================================

@app.route("/api/admin/change-password", methods=["POST"])
def change_admin_password():

    # -----------------------------------------
    # Verify token
    # -----------------------------------------

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

    # -----------------------------------------
    # Get current admin
    # -----------------------------------------

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

    # -----------------------------------------
    # Request data
    # -----------------------------------------

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

    # -----------------------------------------
    # Validate new password
    # -----------------------------------------

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

        # -----------------------------------------
        # Verify CURRENT password
        # -----------------------------------------

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

        # -----------------------------------------
        # Update password in Firebase Auth
        # -----------------------------------------

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


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "API endpoint không tồn tại."
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({
        "success": False,
        "message": "HTTP method không được hỗ trợ."
    }), 405


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error."
    }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )