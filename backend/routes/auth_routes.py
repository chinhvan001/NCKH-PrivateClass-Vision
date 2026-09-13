from flask import Blueprint, jsonify, request
from firebase_admin import auth
import requests

from firebase_config import db, FIREBASE_API_KEY
from utils.auth import ADMIN_ROLES, get_json_body

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/api/auth/google", methods=["POST"])
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

@auth_bp.route("/api/auth/email-password", methods=["POST"])
def email_password_login():

    data = get_json_body()

    email = str(data.get("email", "")).strip()
    password = data.get("password", "")

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Vui lòng nhập email và mật khẩu."
        }), 400

    try:

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

        decoded_token = auth.verify_id_token(firebase_id_token)

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

