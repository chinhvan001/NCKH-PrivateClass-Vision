from flask import Blueprint, jsonify, request

from routes.test_helpers import (
    db,
    get_document,
    get_json_body,
    json_value,
    require_admin,
    required_string,
    server_timestamp,
)

class_bp = Blueprint("class_bp", __name__)
ALLOWED_CLASS_STATUS = {"active", "inactive"}
DEFAULT_ROW_COUNT = 2
DEFAULT_COLUMN_COUNT = 2


def error(message, status=400):
    return jsonify({"success": False, "message": message}), status


def positive_int(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None, f"{field_name} phải là số nguyên dương."
    return value, None


def get_vietnamese_sort_key(name):
    """Tách tên tiếng Việt để sắp xếp theo tên gọi (First name)."""
    if not name:
        return ""
    parts = str(name).strip().split()
    return parts[-1].lower() if parts else ""


def teacher_name(teacher_id):
    if not teacher_id:
        return "Chưa có giáo viên"
    
    # 1. Tra cứu trong collection teachers
    teacher_doc = db.collection("teachers").document(teacher_id).get()
    if teacher_doc.exists:
        teacher = teacher_doc.to_dict() or {}
        return (
            teacher.get("full_name")
            or teacher.get("display_name")
            or teacher.get("name")
            or teacher.get("email")
            or "Chưa có giáo viên"
        )
    
    # 2. Fallback tra cứu trong collection users
    user_doc = db.collection("users").document(teacher_id).get()
    if user_doc.exists:
        user = user_doc.to_dict() or {}
        return (
            user.get("full_name")
            or user.get("display_name")
            or user.get("name")
            or user.get("email")
            or "Chưa có giáo viên"
        )

    return "Chưa có giáo viên"


def teacher_exists_check(teacher_id):
    if not teacher_id:
        return False
    if db.collection("teachers").document(teacher_id).get().exists:
        return True
    if db.collection("users").document(teacher_id).get().exists:
        return True
    return False


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


def class_data(doc_or_dict, doc_id=None):
    if hasattr(doc_or_dict, "to_dict"):
        data = doc_or_dict.to_dict() or {}
        class_id = doc_or_dict.id
    else:
        data = doc_or_dict or {}
        class_id = doc_id

    data.setdefault("row_count", DEFAULT_ROW_COUNT)
    data.setdefault("column_count", DEFAULT_COLUMN_COUNT)

    row_count, row_error = positive_int(data.get("row_count"), "row_count")
    column_count, column_error = positive_int(data.get("column_count"), "column_count")
    if row_error or column_error:
        row_count = DEFAULT_ROW_COUNT
        column_count = DEFAULT_COLUMN_COUNT

    seat_map = data.get("seat_map", {})
    stats = seat_stats_for_class(seat_map, row_count, column_count)

    return {
        "id": class_id,
        **json_value(data),
        **stats,
        "teacher_name": teacher_name(data.get("teacher_id")),
    }


def get_class(class_id):
    return get_document("classes2", class_id)


def student_data(student_id, student, member):
    """Bổ sung thêm Mã HS, Giới tính, SĐT và Ghi chú để lấp đầy bảng chi tiết"""
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


def seat_data(seat_id, seat_info, column_count):
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
        student_doc = db.collection("students2").document(student_id).get()
        if student_doc.exists:
            student_name = (student_doc.to_dict() or {}).get("full_name", "")

    return {
        "id": seat_id,
        **json_value(seat_info),
        "seat_id": seat_id,
        "row": row,
        "column": col,
        "student_name": student_name,
    }


def class_dimensions(class_doc):
    data = class_doc.to_dict() or {}
    row_count = data.get("row_count", DEFAULT_ROW_COUNT)
    column_count = data.get("column_count", DEFAULT_COLUMN_COUNT)
    row_count, row_error = positive_int(row_count, "row_count")
    column_count, column_error = positive_int(column_count, "column_count")
    if row_error or column_error:
        raise ValueError(row_error or column_error)
    return row_count, column_count


def ensure_class_seats(class_id, class_doc):
    """Đảm bảo lớp học có đầy đủ sơ đồ ghế ngồi. Trả về dict dữ liệu cập nhật."""
    data = class_doc.to_dict() or {}
    row_count, column_count = class_dimensions(class_doc)
    seat_map = data.get("seat_map", {})
    
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
        data["seat_map"] = seat_map
        db.collection("classes2").document(class_id).update({"seat_map": seat_map})

    return data


def resize_class_seats(class_id, old_class_doc, new_row_count, new_column_count):
    data = old_class_doc.to_dict() or {}
    old_seat_map = data.get("seat_map", {})
    old_column_count = data.get("column_count", DEFAULT_COLUMN_COUNT)

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

    db.collection("classes2").document(class_id).update({"seat_map": new_seat_map})


@class_bp.route("/api/admin/classes", methods=["GET"])
def get_classes():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error
    try:
        query = db.collection("classes2")
        for field in ("status", "teacher_id", "school_year"):
            value = request.args.get(field)
            if value:
                query = query.where(field, "==", value)
        
        classes = []
        for doc in query.stream():
            updated_data = ensure_class_seats(doc.id, doc)
            classes.append(class_data(updated_data, doc.id))

        classes.sort(key=lambda item: item.get("class_name", ""))
        return jsonify({"success": True, "data": classes}), 200
    except Exception as exc:
        print("Get classes error:", exc)
        return error("Không thể lấy danh sách lớp học.", 500)


@class_bp.route("/api/admin/classes", methods=["POST"])
def create_class():
    _, auth_error = require_admin()
    if auth_error:
        return auth_error

    data = get_json_body()
    values = {}

    for field in ("class_name", "teacher_id", "school_year"):
        value, message = required_string(data, field)
        if message:
            return error(message)
        values[field] = value

    values["subject"] = str(data.get("subject", "")).strip()

    row_count, message = positive_int(data.get("row_count", DEFAULT_ROW_COUNT), "row_count")
    if message:
        return error(message)
        
    column_count, message = positive_int(data.get("column_count", DEFAULT_COLUMN_COUNT), "column_count")
    if message:
        return error(message)

    if not teacher_exists_check(values["teacher_id"]):
        return error("Không tìm thấy giáo viên.", 404)

    duplicate = db.collection("classes2").where("class_name", "==", values["class_name"]).limit(1).stream()
    if next(duplicate, None):
        return error("Tên lớp học này đã tồn tại.", 409)

    class_ref = db.collection("classes2").document()
    class_ref.set(
        {
            **values,
            "row_count": row_count,
            "column_count": column_count,
            "status": "active",
            "seat_map": {},
            "created_at": server_timestamp(),
            "updated_at": server_timestamp(),
        }
    )

    class_doc = class_ref.get()
    updated_data = ensure_class_seats(class_ref.id, class_doc)
    return jsonify({"success": True, "data": class_data(updated_data, class_ref.id)}), 201


@class_bp.route("/api/admin/classes/<class_id>", methods=["GET", "PUT", "DELETE"])
def class_detail(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error

    class_ref, class_doc = get_class(class_id)
    if not class_doc.exists:
        return error("Không tìm thấy lớp học.", 404)

    if request.method == "GET":
        try:
            updated_data = ensure_class_seats(class_id, class_doc)
            return jsonify({"success": True, "data": class_data(updated_data, class_id)}), 200
        except ValueError as exc:
            return error(str(exc), 409)

    if request.method == "DELETE":
        class_ref.update({"status": "inactive", "updated_at": server_timestamp()})
        return jsonify({"success": True, "message": "Vô hiệu hóa lớp học thành công."}), 200

    data = get_json_body()
    update_data = {}

    for field in {"class_name", "teacher_id", "school_year", "status"}:
        if field not in data:
            continue
        value = data[field]
        if field == "status":
            if value not in ALLOWED_CLASS_STATUS:
                return error("status không hợp lệ.")
        elif not isinstance(value, str) or not value.strip():
            return error(f"{field} phải là chuỗi không rỗng.")
        update_data[field] = value.strip() if isinstance(value, str) else value

    current_data = class_doc.to_dict() or {}
    old_row_count = current_data.get("row_count", DEFAULT_ROW_COUNT)
    old_column_count = current_data.get("column_count", DEFAULT_COLUMN_COUNT)
    new_row_count = old_row_count
    new_column_count = old_column_count

    if "row_count" in data:
        new_row_count, message = positive_int(data["row_count"], "row_count")
        if message:
            return error(message)
        update_data["row_count"] = new_row_count

    if "column_count" in data:
        new_column_count, message = positive_int(data["column_count"], "column_count")
        if message:
            return error(message)
        update_data["column_count"] = new_column_count

    if "teacher_id" in update_data:
        if not teacher_exists_check(update_data["teacher_id"]):
            return error("Không tìm thấy giáo viên.", 404)

    if not update_data:
        return error("Không có dữ liệu cần cập nhật.")

    try:
        dimensions_changed = (
            new_row_count != old_row_count or new_column_count != old_column_count
        )
        if dimensions_changed:
            resize_class_seats(
                class_id,
                class_doc,
                new_row_count,
                new_column_count,
            )

        update_data["updated_at"] = server_timestamp()
        class_ref.update(update_data)
        
        updated_doc = class_ref.get()
        return jsonify({"success": True, "data": class_data(updated_doc)}), 200
    except ValueError as exc:
        return error(str(exc), 409)
    except Exception as exc:
        print("Update class error:", exc)
        return error("Không thể cập nhật lớp học.", 500)


@class_bp.route("/api/admin/classes/<class_id>/students", methods=["GET"])
def class_students(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error

    class_ref, class_doc = get_class(class_id)
    if not class_doc.exists:
        return error("Không tìm thấy lớp học.", 404)

    result = []
    student_ids_added = set()

    member_docs = db.collection("class_members").where("class_id", "==", class_id).stream()
    for member_doc in member_docs:
        member = member_doc.to_dict() or {}
        if member.get("status") != "active":
            continue
        student_id = member.get("student_id")
        
        if student_id and str(student_id).strip() not in ["", "None", "null", "undefined"]:
            student_doc = db.collection("students2").document(student_id).get()
            if student_doc.exists:
                result.append(student_data(student_doc.id, student_doc.to_dict() or {}, member))
                student_ids_added.add(student_id)

    class_data_dict = class_doc.to_dict() or {}
    seat_map = class_data_dict.get("seat_map", {})
    for s_id, s_info in seat_map.items():
        student_id = s_info.get("student_id")

        if student_id and str(student_id).strip() not in ["", "None", "null", "undefined"]:
            if student_id not in student_ids_added:
                student_doc = db.collection("students2").document(student_id).get()
                if student_doc.exists:
                    mock_member = {"status": "active"} 
                    result.append(student_data(student_doc.id, student_doc.to_dict() or {}, mock_member))
                    student_ids_added.add(student_id)

    result.sort(key=lambda item: get_vietnamese_sort_key(item.get("full_name", "")))
    return jsonify({"success": True, "data": result}), 200


@class_bp.route("/api/admin/classes/<class_id>/seats", methods=["GET"])
def class_seats(class_id):
    _, auth_error = require_admin()
    if auth_error:
        return auth_error

    class_ref, class_doc = get_class(class_id)
    if not class_doc.exists:
        return error("Không tìm thấy lớp học.", 404)

    try:
        updated_data = ensure_class_seats(class_id, class_doc)
        seat_map = updated_data.get("seat_map", {})
        column_count = updated_data.get("column_count", DEFAULT_COLUMN_COUNT)
        
        seats = [seat_data(s_id, s_info, column_count) for s_id, s_info in seat_map.items()]
        seats.sort(key=lambda item: (item.get("row", 0), item.get("column", 0)))
        
        return jsonify({"success": True, "data": seats}), 200
    except ValueError as exc:
        return error(str(exc), 409)
    except Exception as exc:
        print("Get class seats error:", exc)
        return error("Không thể lấy sơ đồ chỗ ngồi.", 500)


@class_bp.route("/api/admin/classes/<class_id>/seats/<seat_id>", methods=["PUT"])
def update_seat(class_id, seat_id):
    _, auth_error = require_admin() 
    if auth_error:
        return auth_error

    data = get_json_body()
    student_id = data.get("student_id")

    class_ref, class_doc = get_class(class_id)
    if not class_doc.exists:
        return error("Không tìm thấy lớp học.", 404)

    class_data_dict = class_doc.to_dict() or {}
    seat_map = class_data_dict.get("seat_map", {})

    if seat_id not in seat_map:
        return error("Không tìm thấy vị trí ghế ngồi.", 404)
        
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
        class_ref.update({
            "seat_map": seat_map,
            "updated_at": server_timestamp()
        })
        return jsonify({"success": True, "message": "Cập nhật chỗ ngồi thành công."}), 200
    except Exception as exc:
        print("Update seat error:", exc)
        return error("Không thể cập nhật chỗ ngồi.", 500)