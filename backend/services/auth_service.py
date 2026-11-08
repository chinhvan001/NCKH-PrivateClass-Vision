from firebase_admin import auth
import requests
from firebase_config import FIREBASE_API_KEY
from repositories.auth_repository import AuthRepository

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

class AuthService:
    @staticmethod
    def google_login(id_token):
        if not id_token:
            return {
                "success": False,
                "message": "Thiếu Firebase ID Token."
            }, 400

        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email", "").strip().lower()

            if not uid or not email:
                return {
                    "success": False,
                    "message": "Firebase Token không hợp lệ."
                }, 401

            admin_id, admin_data = AuthRepository.get_admin_by_uid(uid)

            if not admin_data:
                return {
                    "success": False,
                    "message": "Tài khoản chưa được cấp quyền truy cập Admin."
                }, 403

            is_active = admin_data.get("is_active", True)

            if is_active is False:
                return {
                    "success": False,
                    "message": "Tài khoản đã bị vô hiệu hóa."
                }, 403

            return {
                "success": True,
                "message": "Đăng nhập Google thành công.",
                "user": {
                    "uid": uid,
                    "document_id": admin_id,
                    "email": admin_data.get("e-mail", email),
                    "name": admin_data.get("name", ""),
                    "phone_number": admin_data.get("phone_number", ""),
                    "school": admin_data.get("school", ""),
                    "is_active": is_active,
                }
            }, 200

        except Exception as error:
            print("Google login error:", error)
            return {
                "success": False,
                "message": "Firebase Token không hợp lệ hoặc đã hết hạn."
            }, 401

    @staticmethod
    def email_password_login(email, password):
        email = str(email or "").strip().lower()

        if not email or not password:
            return {
                "success": False,
                "message": "Vui lòng nhập email và mật khẩu."
            }, 400

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
                error_message = firebase_data.get("error", {}).get("message", "")
                print("Firebase email login error:", error_message)

                if error_message in {"INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND"}:
                    return {
                        "success": False,
                        "message": "Email hoặc mật khẩu không chính xác."
                    }, 401
                if error_message == "USER_DISABLED":
                    return {
                        "success": False,
                        "message": "Tài khoản đã bị vô hiệu hóa."
                    }, 403

                return {
                    "success": False,
                    "message": "Không thể đăng nhập. Vui lòng thử lại."
                }, 401

            firebase_id_token = firebase_data.get("idToken")

            if not firebase_id_token:
                return {
                    "success": False,
                    "message": "Không nhận được Firebase ID Token."
                }, 401

            decoded_token = auth.verify_id_token(firebase_id_token)
            uid = decoded_token.get("uid")
            firebase_email = decoded_token.get("email", email).strip().lower()

            if not uid or not firebase_email:
                return {
                    "success": False,
                    "message": "Firebase Token không hợp lệ."
                }, 401

            admin_id, admin_data = AuthRepository.get_admin_by_uid(uid)

            if not admin_data:
                return {
                    "success": False,
                    "message": "Tài khoản chưa được cấp quyền truy cập Admin."
                }, 403

            is_active = admin_data.get("is_active", True)

            if is_active is False:
                return {
                    "success": False,
                    "message": "Tài khoản đã bị vô hiệu hóa."
                }, 403

            return {
                "success": True,
                "message": "Đăng nhập thành công.",
                "idToken": firebase_id_token,
                "user": {
                    "uid": uid,
                    "document_id": admin_id,
                    "email": admin_data.get("e-mail", firebase_email),
                    "name": admin_data.get("name", ""),
                    "phone_number": admin_data.get("phone_number", ""),
                    "school": admin_data.get("school", ""),
                    "is_active": is_active,
                }
            }, 200

        except requests.RequestException as error:
            print("Firebase request error:", error)
            return {
                "success": False,
                "message": "Không thể kết nối đến Firebase."
            }, 503
        except Exception as error:
            print("Email/password login error:", error)
            return {
                "success": False,
                "message": "Đăng nhập thất bại."
            }, 500
