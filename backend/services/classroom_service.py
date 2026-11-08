import time
from threading import Lock
from repositories.classroom_repository import ClassroomRepository

class ClassroomService:
    _cache = None
    _cache_expiry = 0
    _cache_lock = Lock()
    _CACHE_TTL = 30  # seconds

    @classmethod
    def _invalidate_cache(cls):
        with cls._cache_lock:
            cls._cache = None
            cls._cache_expiry = 0

    @staticmethod
    def normalize_int(value, field_name, default=None):
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} phải là số nguyên")

    @staticmethod
    def format_classroom_data(data):
        return {
            "id": data.get("id", ""),
            "classroom_name": data.get("classroom_name", ""),
            "camera_name": data.get("camera_name", ""),
            "ip_address": data.get("ip_address", ""),
            "rtsp_port": data.get("rtsp_port", ""),
            "rtsp_url": data.get("rtsp_url", ""),
            "row_number": data.get("row_number", 0),
            "column_number": data.get("column_number", 0),
            "status": data.get("status", "offline"),
        }

    @classmethod
    def get_all_classrooms(cls):
        current_time = time.time()
        with cls._cache_lock:
            if cls._cache is not None and current_time < cls._cache_expiry:
                return {
                    "success": True,
                    "classrooms": cls._cache,
                    "total": len(cls._cache),
                }, 200

        try:
            raw_classrooms = ClassroomRepository.get_all_classrooms()
            classroom_list = [cls.format_classroom_data(c) for c in raw_classrooms]
            classroom_list.sort(key=lambda item: item.get("classroom_name", ""))

            with cls._cache_lock:
                cls._cache = classroom_list
                cls._cache_expiry = current_time + cls._CACHE_TTL

            return {
                "success": True,
                "classrooms": classroom_list,
                "total": len(classroom_list),
            }, 200
        except Exception as e:
            return {
                "success": False,
                "message": f"Không thể lấy danh sách phòng học: {str(e)}"
            }, 500

    @classmethod
    def create_classroom(cls, data):
        try:
            classroom_name = str(data.get("classroom_name", "")).strip()
            if not classroom_name:
                return {
                    "success": False,
                    "message": "Tên phòng học là bắt buộc"
                }, 400

            existing = ClassroomRepository.find_by_name(classroom_name)
            if existing:
                return {
                    "success": False,
                    "message": "Phòng học đã tồn tại"
                }, 409

            camera_name = str(data.get("camera_name", "")).strip()
            ip_address = str(data.get("ip_address", "")).strip()
            rtsp_port = str(data.get("rtsp_port", "")).strip()
            rtsp_url = str(data.get("rtsp_url", "")).strip()
            status = str(data.get("status", "offline")).strip().lower()

            if status not in ["online", "offline"]:
                status = "offline"

            try:
                row_number = cls.normalize_int(data.get("row_number"), "row_number", 0)
                column_number = cls.normalize_int(data.get("column_number"), "column_number", 0)
            except ValueError as e:
                return {
                    "success": False,
                    "message": str(e)
                }, 400

            if row_number < 0 or column_number < 0:
                return {
                    "success": False,
                    "message": "Số hàng và số cột không được nhỏ hơn 0"
                }, 400

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

            classroom_id = str(data.get("id", "")).strip()
            if classroom_id:
                if ClassroomRepository.check_id_exists(classroom_id):
                    return {
                        "success": False,
                        "message": "ID phòng học đã tồn tại"
                    }, 409
                new_room = ClassroomRepository.create_classroom(classroom_data, classroom_id=classroom_id)
            else:
                new_room = ClassroomRepository.create_classroom(classroom_data)

            cls._invalidate_cache()

            return {
                "success": True,
                "message": "Tạo phòng học thành công",
                "classroom": cls.format_classroom_data(new_room),
            }, 201

        except Exception as e:
            return {
                "success": False,
                "message": f"Không thể tạo phòng học: {str(e)}"
            }, 500

    @classmethod
    def update_classroom(cls, classroom_id, data):
        try:
            current_data = ClassroomRepository.get_classroom_by_id(classroom_id)
            if not current_data:
                return {
                    "success": False,
                    "message": "Không tìm thấy phòng học"
                }, 404

            classroom_name = str(data.get("classroom_name", current_data.get("classroom_name", ""))).strip()
            if not classroom_name:
                return {
                    "success": False,
                    "message": "Tên phòng học là bắt buộc"
                }, 400

            if classroom_name != current_data.get("classroom_name", ""):
                existing = ClassroomRepository.find_by_name(classroom_name)
                for item in existing:
                    if item.get("id") != classroom_id:
                        return {
                            "success": False,
                            "message": "Phòng học đã tồn tại"
                        }, 409

            try:
                row_number = cls.normalize_int(
                    data.get("row_number", current_data.get("row_number", 0)),
                    "row_number",
                    0
                )
                column_number = cls.normalize_int(
                    data.get("column_number", current_data.get("column_number", 0)),
                    "column_number",
                    0
                )
            except ValueError as e:
                return {
                    "success": False,
                    "message": str(e)
                }, 400

            if row_number < 0 or column_number < 0:
                return {
                    "success": False,
                    "message": "Số hàng và số cột không được nhỏ hơn 0"
                }, 400

            status = str(data.get("status", current_data.get("status", "offline"))).strip().lower()
            if status not in ["online", "offline"]:
                status = "offline"

            updated_data = {
                "classroom_name": classroom_name,
                "camera_name": str(data.get("camera_name", current_data.get("camera_name", ""))).strip(),
                "ip_address": str(data.get("ip_address", current_data.get("ip_address", ""))).strip(),
                "rtsp_port": str(data.get("rtsp_port", current_data.get("rtsp_port", ""))).strip(),
                "rtsp_url": str(data.get("rtsp_url", current_data.get("rtsp_url", ""))).strip(),
                "row_number": row_number,
                "column_number": column_number,
                "status": status,
            }

            saved_room = ClassroomRepository.update_classroom(classroom_id, updated_data)
            cls._invalidate_cache()

            return {
                "success": True,
                "message": "Cập nhật phòng học thành công",
                "classroom": cls.format_classroom_data(saved_room),
            }, 200

        except Exception as e:
            return {
                "success": False,
                "message": f"Không thể xử lý phòng học: {str(e)}"
            }, 500

    @classmethod
    def delete_classroom(cls, classroom_id):
        try:
            current_data = ClassroomRepository.get_classroom_by_id(classroom_id)
            if not current_data:
                return {
                    "success": False,
                    "message": "Không tìm thấy phòng học"
                }, 404

            if ClassroomRepository.is_classroom_linked(classroom_id):
                return {
                    "success": False,
                    "message": "Không thể xóa phòng học đang được sử dụng bởi lớp học"
                }, 409

            ClassroomRepository.delete_classroom(classroom_id)
            cls._invalidate_cache()

            return {
                "success": True,
                "message": "Xóa phòng học thành công"
            }, 200

        except Exception as e:
            return {
                "success": False,
                "message": f"Không thể xử lý phòng học: {str(e)}"
            }, 500
