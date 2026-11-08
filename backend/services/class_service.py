import time
from threading import Lock
from routes.test_helpers import json_value, server_timestamp
from repositories.class_repository import ClassRepository

DEFAULT_ROW_COUNT = 2
DEFAULT_COLUMN_COUNT = 2
ALLOWED_CLASS_STATUS = {"active", "inactive"}

class ClassService:
    _classes_cache = {}
    _cache_lock = Lock()
    _CACHE_TTL = 30  # seconds

    @classmethod
    def _invalidate_classes_cache(cls):
        with cls._cache_lock:
            cls._classes_cache.clear()

    @staticmethod
    def positive_int(value, field_name):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return None, f"{field_name} phải là số nguyên dương."
        return value, None

    @staticmethod
    def get_vietnamese_sort_key(name):
        """Tách tên tiếng Việt để sắp xếp theo tên gọi (First name)."""
        if not name:
            return ""
        parts = str(name).strip().split()
        return parts[-1].lower() if parts else ""

    @staticmethod
    def seat_stats_for_class(seat_map, row_count, column_count):
        capacity = row_count * column_count
        occupied_count = 0

        for seat_id, seat in seat_map.items():
            student_id = seat.get("student_id")
            if student_id and str(student_id).strip() not in ["", "None", "null", "undefined"]:
                occupied_count += 1

        empty_count = max(0, capacity - occupied_count)

        return {
            "seat_capacity": capacity,
            "empty_seat_count": empty_count,
            "occupied_seat_count": occupied_count,
        }

    @classmethod
    def format_class_data(cls, data, class_id=None):
        if not data:
            data = {}
        cid = class_id or data.get("id")

        c_data = dict(data)
        c_data.setdefault("row_count", DEFAULT_ROW_COUNT)
        c_data.setdefault("column_count", DEFAULT_COLUMN_COUNT)

        row_count, row_error = cls.positive_int(c_data.get("row_count"), "row_count")
        column_count, column_error = cls.positive_int(c_data.get("column_count"), "column_count")
        if row_error or column_error:
            row_count = DEFAULT_ROW_COUNT
            column_count = DEFAULT_COLUMN_COUNT

        seat_map = c_data.get("seat_map", {})
        stats = cls.seat_stats_for_class(seat_map, row_count, column_count)

        teacher_id = c_data.get("teacher_id")
        teacher_name = ClassRepository.get_teacher_name(teacher_id)

        return {
            "id": cid,
            **json_value(c_data),
            **stats,
            "teacher_name": teacher_name,
        }

    @staticmethod
    def format_student_data(student_id, student, member):
        birthday = student.get("birthday")
        if birthday and not isinstance(birthday, str):
            birthday = str(birthday)

        return {
            "student_id": student_id,
            "student_code": student.get("student_code", "N/A"),
            "full_name": student.get("full_name", ""),
            "gender": student.get("gender", "Chưa rõ"),
            "parent_phone": student.get("parent_phone", ""),
            "parent_id": student.get("parent_id"),
            "status": member.get("status", "active"),
            "birthday": birthday,
            "note": student.get("note", "")
        }

    @staticmethod
    def format_seat_data(seat_id, seat_info, column_count):
        student_name = ""
        student_id = seat_info.get("student_id")

        row = seat_info.get("row")
        col = seat_info.get("column")

        if not row or not col:
            try:
                num = int(seat_id.replace("S", ""))
                row = (num - 1) // column_count + 1
                col = (num - 1) % column_count + 1
            except Exception:
                row, col = 1, 1

        if student_id:
            student_data = ClassRepository.get_student_by_id(student_id)
            if student_data:
                student_name = student_data.get("full_name", "")

        return {
            "id": seat_id,
            **json_value(seat_info),
            "seat_id": seat_id,
            "row": row,
            "column": col,
            "student_name": student_name,
        }

    @classmethod
    def ensure_class_seats(cls, class_id, data):
        """Đảm bảo lớp học có đầy đủ sơ đồ ghế ngồi. Trả về dict dữ liệu cập nhật."""
        c_data = dict(data)
        row_count = c_data.get("row_count", DEFAULT_ROW_COUNT)
        column_count = c_data.get("column_count", DEFAULT_COLUMN_COUNT)

        row_count, row_error = cls.positive_int(row_count, "row_count")
        column_count, column_error = cls.positive_int(column_count, "column_count")
        if row_error or column_error:
            raise ValueError(row_error or column_error)

        seat_map = dict(c_data.get("seat_map", {}))
        changed = False

        for row in range(1, row_count + 1):
            for column in range(1, column_count + 1):
                seat_id = f"S{(row - 1) * column_count + column:02d}"
                if seat_id not in seat_map:
                    seat_map[seat_id] = {
                        "seat_id": seat_id,
                        "row": row,
                        "column": column,
                        "student_id": None,
                        "status": "empty",
                        "updated_at": server_timestamp(),
                    }
                    changed = True

        if changed:
            c_data["seat_map"] = seat_map
            ClassRepository.update_seat_map(class_id, seat_map)

        return c_data

    @classmethod
    def resize_class_seats(cls, class_id, current_data, new_row_count, new_column_count):
        old_seat_map = current_data.get("seat_map", {})
        old_column_count = current_data.get("column_count", DEFAULT_COLUMN_COUNT)

        coords_to_seat = {}
        for seat_id, seat in old_seat_map.items():
            r, c = seat.get("row"), seat.get("column")
            if not (isinstance(r, int) and isinstance(c, int)):
                try:
                    num = int(str(seat_id).upper().replace("S", ""))
                    r = (num - 1) // old_column_count + 1
                    c = (num - 1) % old_column_count + 1
                except Exception:
                    r, c = None, None

            if r is not None and c is not None:
                coords_to_seat[(r, c)] = seat

        for (r, c), seat in coords_to_seat.items():
            if r > new_row_count or c > new_column_count:
                if seat.get("student_id") or seat.get("status") == "occupied":
                    raise ValueError(
                        f"Không thể thu nhỏ do ghế hàng {r}, cột {c} đang có học sinh."
                    )

        new_seat_map = {}
        for row in range(1, new_row_count + 1):
            for column in range(1, new_column_count + 1):
                seat_id = f"S{(row - 1) * new_column_count + column:02d}"
                old_seat = coords_to_seat.get((row, column))

                if old_seat:
                    old_seat["seat_id"] = seat_id
                    old_seat["row"] = row
                    old_seat["column"] = column
                    new_seat_map[seat_id] = old_seat
                else:
                    new_seat_map[seat_id] = {
                        "seat_id": seat_id,
                        "row": row,
                        "column": column,
                        "student_id": None,
                        "status": "empty",
                        "updated_at": server_timestamp(),
                    }

        ClassRepository.update_seat_map(class_id, new_seat_map)

    @classmethod
    def get_classes(cls, filters):
        cache_key = tuple(sorted((k, str(v)) for k, v in (filters or {}).items() if v))
        current_time = time.time()
        with cls._cache_lock:
            cached = cls._classes_cache.get(cache_key)
            if cached and current_time < cached[1]:
                return {"success": True, "data": cached[0]}, 200

        try:
            raw_classes = ClassRepository.get_classes(filters)
            classes = []
            for doc_id, data in raw_classes:
                updated_data = cls.ensure_class_seats(doc_id, data)
                classes.append(cls.format_class_data(updated_data, doc_id))

            classes.sort(key=lambda item: item.get("class_name", ""))

            with cls._cache_lock:
                cls._classes_cache[cache_key] = (classes, current_time + cls._CACHE_TTL)

            return {"success": True, "data": classes}, 200
        except Exception as exc:
            print("Get classes error:", exc)
            return {"success": False, "message": "Không thể lấy danh sách lớp học."}, 500

    @classmethod
    def create_class(cls, data):
        values = {}
        for field in ("class_name", "teacher_id", "school_year"):
            val = data.get(field)
            if not isinstance(val, str) or not val.strip():
                return {"success": False, "message": f"{field} là bắt buộc."}, 400
            values[field] = val.strip()

        values["subject"] = str(data.get("subject", "")).strip()

        row_count, message = cls.positive_int(data.get("row_count", DEFAULT_ROW_COUNT), "row_count")
        if message:
            return {"success": False, "message": message}, 400

        column_count, message = cls.positive_int(data.get("column_count", DEFAULT_COLUMN_COUNT), "column_count")
        if message:
            return {"success": False, "message": message}, 400

        if not ClassRepository.teacher_exists(values["teacher_id"]):
            return {"success": False, "message": "Không tìm thấy giáo viên."}, 404

        if ClassRepository.find_by_name(values["class_name"]):
            return {"success": False, "message": "Tên lớp học này đã tồn tại."}, 409

        class_payload = {
            **values,
            "row_count": row_count,
            "column_count": column_count,
            "status": "active",
            "seat_map": {},
        }

        class_id, created_data = ClassRepository.create_class(class_payload)
        updated_data = cls.ensure_class_seats(class_id, created_data)
        cls._invalidate_classes_cache()

        return {"success": True, "data": cls.format_class_data(updated_data, class_id)}, 201

    @classmethod
    def get_class_detail(cls, class_id):
        ref, class_data = ClassRepository.get_class_by_id(class_id)
        if not class_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        try:
            updated_data = cls.ensure_class_seats(class_id, class_data)
            return {"success": True, "data": cls.format_class_data(updated_data, class_id)}, 200
        except ValueError as exc:
            return {"success": False, "message": str(exc)}, 409

    @classmethod
    def delete_class(cls, class_id):
        ref, class_data = ClassRepository.get_class_by_id(class_id)
        if not class_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        ClassRepository.soft_delete_class(class_id)
        cls._invalidate_classes_cache()
        return {"success": True, "message": "Vô hiệu hóa lớp học thành công."}, 200

    @classmethod
    def update_class(cls, class_id, data):
        ref, current_data = ClassRepository.get_class_by_id(class_id)
        if not current_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        update_data = {}
        for field in {"class_name", "teacher_id", "school_year", "status"}:
            if field not in data:
                continue
            value = data[field]
            if field == "status":
                if value not in ALLOWED_CLASS_STATUS:
                    return {"success": False, "message": "status không hợp lệ."}, 400
            elif not isinstance(value, str) or not value.strip():
                return {"success": False, "message": f"{field} phải là chuỗi không rỗng."}, 400
            update_data[field] = value.strip() if isinstance(value, str) else value

        old_row_count = current_data.get("row_count", DEFAULT_ROW_COUNT)
        old_column_count = current_data.get("column_count", DEFAULT_COLUMN_COUNT)
        new_row_count = old_row_count
        new_column_count = old_column_count

        if "row_count" in data:
            new_row_count, message = cls.positive_int(data["row_count"], "row_count")
            if message:
                return {"success": False, "message": message}, 400
            update_data["row_count"] = new_row_count

        if "column_count" in data:
            new_column_count, message = cls.positive_int(data["column_count"], "column_count")
            if message:
                return {"success": False, "message": message}, 400
            update_data["column_count"] = new_column_count

        if "teacher_id" in update_data:
            if not ClassRepository.teacher_exists(update_data["teacher_id"]):
                return {"success": False, "message": "Không tìm thấy giáo viên."}, 404

        if not update_data:
            return {"success": False, "message": "Không có dữ liệu cần cập nhật."}, 400

        try:
            dimensions_changed = (
                new_row_count != old_row_count or new_column_count != old_column_count
            )
            if dimensions_changed:
                cls.resize_class_seats(
                    class_id,
                    current_data,
                    new_row_count,
                    new_column_count,
                )

            updated_doc = ClassRepository.update_class(class_id, update_data)
            cls._invalidate_classes_cache()
            return {"success": True, "data": cls.format_class_data(updated_doc, class_id)}, 200
        except ValueError as exc:
            return {"success": False, "message": str(exc)}, 409
        except Exception as exc:
            print("Update class error:", exc)
            return {"success": False, "message": "Không thể cập nhật lớp học."}, 500

    @classmethod
    def get_class_students(cls, class_id):
        ref, class_data = ClassRepository.get_class_by_id(class_id)
        if not class_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        result = []
        student_ids_added = set()

        members = ClassRepository.get_class_members(class_id)
        for member in members:
            if member.get("status") != "active":
                continue
            student_id = member.get("student_id")
            if student_id and str(student_id).strip() not in ["", "None", "null", "undefined"]:
                student = ClassRepository.get_student_by_id(student_id)
                if student:
                    result.append(cls.format_student_data(student_id, student, member))
                    student_ids_added.add(student_id)

        seat_map = class_data.get("seat_map", {})
        for s_id, s_info in seat_map.items():
            student_id = s_info.get("student_id")
            if student_id and str(student_id).strip() not in ["", "None", "null", "undefined"]:
                if student_id not in student_ids_added:
                    student = ClassRepository.get_student_by_id(student_id)
                    if student:
                        mock_member = {"status": "active"}
                        result.append(cls.format_student_data(student_id, student, mock_member))
                        student_ids_added.add(student_id)

        result.sort(key=lambda item: cls.get_vietnamese_sort_key(item.get("full_name", "")))
        return {"success": True, "data": result}, 200

    @classmethod
    def get_class_seats(cls, class_id):
        ref, class_data = ClassRepository.get_class_by_id(class_id)
        if not class_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        try:
            updated_data = cls.ensure_class_seats(class_id, class_data)
            seat_map = updated_data.get("seat_map", {})
            column_count = updated_data.get("column_count", DEFAULT_COLUMN_COUNT)

            seats = [cls.format_seat_data(s_id, s_info, column_count) for s_id, s_info in seat_map.items()]
            seats.sort(key=lambda item: (item.get("row", 0), item.get("column", 0)))

            return {"success": True, "data": seats}, 200
        except ValueError as exc:
            return {"success": False, "message": str(exc)}, 409
        except Exception as exc:
            print("Get class seats error:", exc)
            return {"success": False, "message": "Không thể lấy sơ đồ chỗ ngồi."}, 500

    @classmethod
    def update_seat(cls, class_id, seat_id, student_id):
        ref, class_data = ClassRepository.get_class_by_id(class_id)
        if not class_data:
            return {"success": False, "message": "Không tìm thấy lớp học."}, 404

        seat_map = class_data.get("seat_map", {})
        if seat_id not in seat_map:
            return {"success": False, "message": "Không tìm thấy vị trí ghế ngồi."}, 404

        if student_id:
            for sid, s_info in seat_map.items():
                if s_info.get("student_id") == student_id and sid != seat_id:
                    s_info["student_id"] = None
                    s_info["status"] = "empty"
                    s_info["updated_at"] = server_timestamp()
            status = "occupied"
        else:
            status = "empty"

        seat_map[seat_id]["student_id"] = student_id
        seat_map[seat_id]["status"] = status
        seat_map[seat_id]["updated_at"] = server_timestamp()

        try:
            ClassRepository.update_seat_map(class_id, seat_map)
            cls._invalidate_classes_cache()
            return {"success": True, "message": "Cập nhật chỗ ngồi thành công."}, 200
        except Exception as exc:
            print("Update seat error:", exc)
            return {"success": False, "message": "Không thể cập nhật chỗ ngồi."}, 500
