import time
from threading import Lock
import requests
from firebase_config import FIREBASE_API_KEY
from utils.auth import is_admin_user
from repositories.admin_repository import AdminRepository
from repositories.class_repository import ClassRepository

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

class AdminService:
    _teachers_cache = None
    _teachers_cache_expiry = 0
    _admin_profile_cache = {}
    _cache_lock = Lock()
    _CACHE_TTL = 30  # seconds

    @classmethod
    def _invalidate_teachers_cache(cls, teacher_id=None):
        with cls._cache_lock:
            cls._teachers_cache = None
            cls._teachers_cache_expiry = 0
        ClassRepository.invalidate_teacher_cache(teacher_id)

    @classmethod
    def _invalidate_admin_cache(cls, uid=None):
        with cls._cache_lock:
            if uid:
                cls._admin_profile_cache.pop(uid, None)
            else:
                cls._admin_profile_cache.clear()

    @classmethod
    def get_teachers(cls):
        current_time = time.time()
        with cls._cache_lock:
            if cls._teachers_cache is not None and current_time < cls._teachers_cache_expiry:
                return {
                    "success": True,
                    "users": cls._teachers_cache,
                    "total": len(cls._teachers_cache)
                }, 200

        try:
            raw_teachers = AdminRepository.get_all_teachers()
            teachers = []
            for teacher_data in raw_teachers:
                teachers.append({
                    "id": teacher_data.get("id"),
                    "uid": teacher_data.get("uid"),
                    "email": teacher_data.get("email", ""),
                    "name": teacher_data.get("name", ""),
                    "phone_number": teacher_data.get("phone_number", ""),
                    "is_active": teacher_data.get("is_active", True),
                    "subject": teacher_data.get("subject", ""),
                    "create_date": teacher_data.get("create_date"),
                    "auth_provider": teacher_data.get("auth_provider", ""),
                    "auth_status": teacher_data.get("auth_status", "")
                })

            with cls._cache_lock:
                cls._teachers_cache = teachers
                cls._teachers_cache_expiry = current_time + cls._CACHE_TTL

            return {
                "success": True,
                "users": teachers,
                "total": len(teachers)
            }, 200

        except Exception as error:
            print("Get teachers error:", error)
            return {
                "success": False,
                "message": "Không thể lấy danh sách giáo viên."
            }, 500

    @classmethod
    def create_teacher(cls, data):
        try:
            name = str(data.get("name", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            phone_number = str(data.get("phone_number", "")).strip()
            subject = str(data.get("subject", "")).strip()
            is_active = data.get("is_active", True)

            if not name:
                return {
                    "success": False,
                    "message": "Họ và tên không được để trống."
                }, 400

            if not email:
                return {
                    "success": False,
                    "message": "Email không được để trống."
                }, 400

            if not subject:
                return {
                    "success": False,
                    "message": "Bộ môn không được để trống."
                }, 400

            if not isinstance(is_active, bool):
                return {
                    "success": False,
                    "message": "is_active phải là true hoặc false."
                }, 400

            existing = AdminRepository.find_teacher_by_email(email)
            if existing:
                return {
                    "success": False,
                    "message": "Email này đã được sử dụng."
                }, 409

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

            doc_id = AdminRepository.create_teacher(teacher_data)
            cls._invalidate_teachers_cache()

            return {
                "success": True,
                "message": "Thêm tài khoản giáo viên thành công.",
                "user": {
                    **teacher_data,
                    "id": doc_id
                }
            }, 201

        except Exception as error:
            print("Create teacher error:", error)
            return {
                "success": False,
                "message": "Không thể thêm tài khoản giáo viên."
            }, 500

    @classmethod
    def update_teacher(cls, uid, data):
        try:
            ref, current_teacher = AdminRepository.get_teacher_by_id(uid)
            if not current_teacher:
                return {
                    "success": False,
                    "message": "Không tìm thấy tài khoản giáo viên."
                }, 404

            update_data = {}

            if "name" in data:
                name = str(data.get("name", "")).strip()
                if not name:
                    return {
                        "success": False,
                        "message": "Họ tên không được để trống."
                    }, 400
                update_data["name"] = name

            if "phone_number" in data:
                phone_number = str(data.get("phone_number", "")).strip()
                update_data["phone_number"] = phone_number

            if "subject" in data:
                subject = str(data.get("subject", "")).strip()
                if not subject:
                    return {
                        "success": False,
                        "message": "Bộ môn không được để trống."
                    }, 400
                update_data["subject"] = subject

            if "is_active" in data:
                if not isinstance(data.get("is_active"), bool):
                    return {
                        "success": False,
                        "message": "is_active phải là true hoặc false."
                    }, 400
                update_data["is_active"] = data.get("is_active")

            if not update_data:
                return {
                    "success": False,
                    "message": "Không có dữ liệu cần cập nhật."
                }, 400

            AdminRepository.update_teacher(uid, update_data)
            cls._invalidate_teachers_cache(uid)

            updated_teacher = {
                **current_teacher,
                **update_data
            }

            return {
                "success": True,
                "message": "Cập nhật tài khoản giáo viên thành công.",
                "user": {
                    "id": uid,
                    "uid": updated_teacher.get("uid"),
                    "email": updated_teacher.get("email", ""),
                    "name": updated_teacher.get("name", ""),
                    "phone_number": updated_teacher.get("phone_number", ""),
                    "is_active": updated_teacher.get("is_active", True),
                    "subject": updated_teacher.get("subject", ""),
                    "auth_provider": updated_teacher.get("auth_provider", ""),
                    "auth_status": updated_teacher.get("auth_status", "")
                }
            }, 200

        except Exception as error:
            print("Update teacher error:", error)
            return {
                "success": False,
                "message": "Không thể cập nhật tài khoản giáo viên."
            }, 500

    @classmethod
    def delete_teacher(cls, uid):
        try:
            ref, teacher_data = AdminRepository.get_teacher_by_id(uid)
            if not teacher_data:
                return {
                    "success": False,
                    "message": "Không tìm thấy tài khoản giáo viên."
                }, 404

            firebase_uid = teacher_data.get("uid")
            AdminRepository.delete_teacher(uid, firebase_uid)
            cls._invalidate_teachers_cache(uid)

            return {
                "success": True,
                "message": "Xóa tài khoản giáo viên thành công.",
                "uid": firebase_uid,
                "id": uid
            }, 200

        except Exception as error:
            print("Delete teacher error:", error)
            return {
                "success": False,
                "message": "Không thể xóa tài khoản giáo viên."
            }, 500

    @classmethod
    def get_admin_profile(cls, uid):
        current_time = time.time()
        with cls._cache_lock:
            cached = cls._admin_profile_cache.get(uid)
            if cached and current_time < cached[1]:
                return {"success": True, "user": cached[0]}, 200

        ref, admin_data = AdminRepository.get_admin_by_uid(uid)
        if not admin_data:
            return {
                "success": False,
                "message": "Không tìm thấy tài khoản admin."
            }, 404

        if not is_admin_user(admin_data):
            return {
                "success": False,
                "message": "Tài khoản admin đã bị vô hiệu hóa."
            }, 403

        user_info = {
            "uid": uid,
            "email": admin_data.get("email", ""),
            "name": admin_data.get("name", ""),
            "phone_number": admin_data.get("phone_number", ""),
            "school": admin_data.get("school", ""),
            "is_active": admin_data.get("is_active", True)
        }

        with cls._cache_lock:
            cls._admin_profile_cache[uid] = (user_info, current_time + cls._CACHE_TTL)

        return {"success": True, "user": user_info}, 200

    @classmethod
    def update_admin_profile(cls, uid, data):
        ref, current_admin = AdminRepository.get_admin_by_uid(uid)
        if not current_admin:
            return {
                "success": False,
                "message": "Không tìm thấy tài khoản admin."
            }, 404

        if not is_admin_user(current_admin):
            return {
                "success": False,
                "message": "Tài khoản admin đã bị vô hiệu hóa."
            }, 403

        update_data = {}

        if "name" in data:
            name = str(data.get("name", "")).strip()
            if not name:
                return {
                    "success": False,
                    "message": "Họ tên không được để trống."
                }, 400
            update_data["name"] = name

        if "phone_number" in data:
            phone_number = str(data.get("phone_number", "")).strip()
            update_data["phone_number"] = phone_number

        if not update_data:
            return {
                "success": False,
                "message": "Không có dữ liệu cần cập nhật."
            }, 400

        try:
            AdminRepository.update_admin_profile(uid, update_data)
            cls._invalidate_admin_cache(uid)

            updated_admin = {
                **current_admin,
                **update_data
            }

            return {
                "success": True,
                "message": "Cập nhật profile thành công.",
                "user": {
                    "uid": uid,
                    "email": updated_admin.get("email", ""),
                    "name": updated_admin.get("name", ""),
                    "phone_number": updated_admin.get("phone_number", ""),
                    "school": updated_admin.get("school", ""),
                    "is_active": updated_admin.get("is_active", True)
                }
            }, 200

        except Exception as error:
            print("Update admin profile error:", error)
            return {
                "success": False,
                "message": "Không thể cập nhật profile."
            }, 500

    @classmethod
    def change_admin_password(cls, uid, data):
        ref, admin_data = AdminRepository.get_admin_by_uid(uid)
        if not admin_data:
            return {
                "success": False,
                "message": "Không tìm thấy tài khoản admin."
            }, 404

        if not is_admin_user(admin_data):
            return {
                "success": False,
                "message": "Bạn không có quyền đổi mật khẩu."
            }, 403

        current_password = data.get("currentPassword", "")
        new_password = data.get("newPassword", "")

        if not current_password or not new_password:
            return {
                "success": False,
                "message": "Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới."
            }, 400

        if len(new_password) < 6:
            return {
                "success": False,
                "message": "Mật khẩu mới phải có ít nhất 6 ký tự."
            }, 400

        if current_password == new_password:
            return {
                "success": False,
                "message": "Mật khẩu mới phải khác mật khẩu hiện tại."
            }, 400

        email = admin_data.get("email", "")
        if not email:
            return {
                "success": False,
                "message": "Tài khoản không có email."
            }, 400

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
                print("Current password verification error:", error_message)

                if error_message in {"INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD"}:
                    return {
                        "success": False,
                        "message": "Mật khẩu hiện tại không chính xác."
                    }, 401

                return {
                    "success": False,
                    "message": "Không thể xác minh mật khẩu hiện tại."
                }, 401

            AdminRepository.update_admin_password(uid, new_password)

            return {
                "success": True,
                "message": "Đổi mật khẩu thành công."
            }, 200

        except requests.RequestException as error:
            print("Firebase password verification error:", error)
            return {
                "success": False,
                "message": "Không thể kết nối đến Firebase."
            }, 503

        except Exception as error:
            print("Change password error:", error)
            return {
                "success": False,
                "message": "Không thể đổi mật khẩu."
            }, 500
