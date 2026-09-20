from flask import Blueprint, jsonify
from firebase_config import db
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
    get_json_body,
)

class_bp = Blueprint("class_bp", __name__)


def authorize_admin():
    decoded_token = verify_request_token()
    if not decoded_token:
        return None, (
            jsonify({"success": False, "message": "Unauthorized."}),
            401
        )

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return None, (
            jsonify({"success": False, "message": "Tài khoản không tồn tại."}),
            403
        )

    if not is_admin_user(current_user):
        return None, (
            jsonify({"success": False, "message": "Bạn không có quyền truy cập."}),
            403
        )

    return current_user, None


def normalize_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_teacher(teacher_id):
    if not teacher_id:
        return None, None
        
    teacher_ref = db.collection("teachers").document(teacher_id)
    teacher_doc = teacher_ref.get()

    if not teacher_doc.exists:
        return None, None

    teacher_data = teacher_doc.to_dict() or {}
    return teacher_doc, teacher_data


def get_classroom(classroom_id):
    if not classroom_id:
        return None, None
        
    classroom_ref = db.collection("classrooms").document(classroom_id)
    classroom_doc = classroom_ref.get()

    if not classroom_doc.exists:
        return None, None

    classroom_data = classroom_doc.to_dict() or {}
    return classroom_doc, classroom_data


def build_class_data(doc):
    data = doc.to_dict() or {}

    teacher_id = data.get("teacher_id")
    classroom_id = data.get("classroom_id")

    teacher_name = ""
    teacher_email = ""

    if teacher_id:
        _, teacher_data = get_teacher(teacher_id)

        if teacher_data:
            teacher_name = teacher_data.get("name", "")
            teacher_email = (
                teacher_data.get("e-mail")
                or teacher_data.get("email")
                or ""
            )

    classroom_name = ""

    camera = {
        "id": None,
        "name": "",
        "status": "offline",
        "is_configured": False,
        "ip_address": "",
        "rtsp_port": "",
    }

    if classroom_id:
        _, classroom_data = get_classroom(classroom_id)

        if classroom_data:
            classroom_name = (
                classroom_data.get("classroom_name")
                or classroom_data.get("class_name")
                or classroom_data.get("room_name")
                or classroom_data.get("name")
                or ""
            )

            camera_name = classroom_data.get("camera_name", "")
            ip_address = classroom_data.get("ip_address", "")
            rtsp_port = classroom_data.get("rtsp_port", "")
            rtsp_url = classroom_data.get("rtsp_url", "")

            is_configured = all([
                camera_name,
                ip_address,
                rtsp_port,
                rtsp_url,
            ])

            if camera_name or ip_address or rtsp_port or rtsp_url:
                camera = {
                    "id": classroom_id,
                    "name": camera_name,
                    "status": classroom_data.get("status", "offline"),
                    "is_configured": is_configured,
                    "ip_address": ip_address,
                    "rtsp_port": str(rtsp_port) if rtsp_port else "",
                }

    row_number = normalize_int(data.get("row_number"), 0)
    column_number = normalize_int(data.get("column_number"), 0)

    student_count = row_number * column_number

    seat_assignments = data.get("seat_assignments", {})

    if not isinstance(seat_assignments, dict):
        seat_assignments = {}

    return {
        "id": doc.id,
        "class_name": data.get("class_name", ""),
        "teacher_id": teacher_id,
        "teacher_name": teacher_name,
        "teacher_email": teacher_email,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "row_number": row_number,
        "column_number": column_number,
        "student_count": student_count,
        "seat_assignments": seat_assignments,
        "is_active": data.get("is_active", True),
        "camera": camera,
    }


@class_bp.route("/api/admin/classes", methods=["GET"])
def get_classes():
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        classes = []
        docs = db.collection("classes").stream()

        for doc in docs:
            classes.append(build_class_data(doc))

        classes.sort(key=lambda item: item.get("class_name", ""))

        return jsonify({
            "success": True,
            "classes": classes,
            "total": len(classes),
        }), 200

    except Exception as error:
        print("Get classes error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể lấy danh sách lớp học."
        }), 500


@class_bp.route("/api/admin/classes", methods=["POST"])
def create_class():
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        data = get_json_body()

        class_name = str(data.get("class_name", "")).strip()
        teacher_id = str(data.get("teacher_id", "")).strip()
        classroom_id = str(data.get("classroom_id", "")).strip()
        row_number = normalize_int(data.get("row_number"), 0)
        column_number = normalize_int(data.get("column_number"), 0)
        is_active = data.get("is_active", True)

        if not class_name:
            return jsonify({"success": False, "message": "Tên lớp không được để trống."}), 400
        if not teacher_id:
            return jsonify({"success": False, "message": "Giáo viên chủ nhiệm là bắt buộc."}), 400
        if not classroom_id:
            return jsonify({"success": False, "message": "Vui lòng chọn phòng học."}), 400
        if row_number < 1:
            return jsonify({"success": False, "message": "Số hàng phải lớn hơn hoặc bằng 1."}), 400
        if column_number < 1:
            return jsonify({"success": False, "message": "Số cột phải lớn hơn hoặc bằng 1."}), 400
        if not isinstance(is_active, bool):
            return jsonify({"success": False, "message": "is_active phải là true hoặc false."}), 400

        teacher_doc, teacher_data = get_teacher(teacher_id)
        if not teacher_doc:
            return jsonify({"success": False, "message": "Không tìm thấy giáo viên chủ nhiệm."}), 404
        if teacher_data.get("is_active", True) is False:
            return jsonify({"success": False, "message": "Giáo viên chủ nhiệm đang bị khóa."}), 400

        classroom_doc, _ = get_classroom(classroom_id)
        if not classroom_doc:
            return jsonify({"success": False, "message": "Không tìm thấy phòng học."}), 404

        existing_query = db.collection("classes").where("class_name", "==", class_name).limit(1).stream()

        if next(existing_query, None):
            return jsonify({"success": False, "message": "Tên lớp học này đã tồn tại."}), 409

        student_count = row_number * column_number
        class_data = {
            "class_name": class_name,
            "teacher_id": teacher_id,
            "classroom_id": classroom_id,
            "row_number": row_number,
            "column_number": column_number,
            "student_count": student_count,
            "seat_assignments": {},
            "is_active": is_active,
        }

        doc_ref = db.collection("classes").document()
        doc_ref.set(class_data)

        return jsonify({
            "success": True,
            "message": "Tạo lớp học thành công.",
            "class": build_class_data(doc_ref.get()),
        }), 201

    except Exception as error:
        print("Create class error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể tạo lớp học."
        }), 500


@class_bp.route("/api/admin/classes/<class_id>", methods=["PUT"])
def update_class(class_id):
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        class_ref = db.collection("classes").document(class_id)
        class_doc = class_ref.get()

        if not class_doc.exists:
            return jsonify({"success": False, "message": "Không tìm thấy lớp học."}), 404

        current_data = class_doc.to_dict() or {}
        data = get_json_body()
        current_teacher_id = str(current_data.get("teacher_id", "")).strip()

        if "teacher_id" not in data:
            if not current_teacher_id:
                return jsonify({"success": False, "message": "Giáo viên chủ nhiệm là bắt buộc."}), 400

        update_data = {}

        if "class_name" in data:
            class_name = str(data.get("class_name", "")).strip()
            if not class_name:
                return jsonify({"success": False, "message": "Tên lớp không được để trống."}), 400

            existing_query = db.collection("classes").where("class_name", "==", class_name).limit(10).stream()
            for existing_doc in existing_query:
                if existing_doc.id != class_id:
                    return jsonify({"success": False, "message": "Tên lớp học này đã tồn tại."}), 409

            update_data["class_name"] = class_name

        if "teacher_id" in data:
            teacher_id = str(data.get("teacher_id", "")).strip()
            if not teacher_id:
                return jsonify({"success": False, "message": "Giáo viên chủ nhiệm là bắt buộc."}), 400

            teacher_doc, teacher_data = get_teacher(teacher_id)
            if not teacher_doc:
                return jsonify({"success": False, "message": "Không tìm thấy giáo viên chủ nhiệm."}), 404

            if teacher_data.get("is_active", True) is False:
                return jsonify({"success": False, "message": "Giáo viên chủ nhiệm đang bị khóa."}), 400

            update_data["teacher_id"] = teacher_id

        if "classroom_id" in data:
            classroom_id = str(data.get("classroom_id", "")).strip()
            if not classroom_id:
                return jsonify({"success": False, "message": "Vui lòng chọn phòng học."}), 400

            classroom_doc, _ = get_classroom(classroom_id)
            if not classroom_doc:
                return jsonify({"success": False, "message": "Không tìm thấy phòng học."}), 404

            update_data["classroom_id"] = classroom_id

        if "row_number" in data:
            row_number = normalize_int(data.get("row_number"), 0)
            if row_number < 1:
                return jsonify({"success": False, "message": "Số hàng phải lớn hơn hoặc bằng 1."}), 400
            update_data["row_number"] = row_number

        if "column_number" in data:
            column_number = normalize_int(data.get("column_number"), 0)
            if column_number < 1:
                return jsonify({"success": False, "message": "Số cột phải lớn hơn hoặc bằng 1."}), 400
            update_data["column_number"] = column_number

        if "is_active" in data:
            if not isinstance(data.get("is_active"), bool):
                return jsonify({"success": False, "message": "is_active phải là true hoặc false."}), 400
            update_data["is_active"] = data.get("is_active")

        old_rows = normalize_int(current_data.get("row_number"), 0)
        old_columns = normalize_int(current_data.get("column_number"), 0)
        new_rows = update_data.get("row_number", old_rows)
        new_columns = update_data.get("column_number", old_columns)
        new_student_count = new_rows * new_columns
        
        update_data["student_count"] = new_student_count

        if new_rows != old_rows or new_columns != old_columns:
            current_assignments = current_data.get("seat_assignments", {})
            if not isinstance(current_assignments, dict):
                current_assignments = {}

            valid_assignments = {}
            max_seats = new_rows * new_columns

            for seat_id, student_id in current_assignments.items():
                if not isinstance(seat_id, str) or not seat_id.startswith("S"):
                    continue
                try:
                    seat_number = int(seat_id[1:])
                except ValueError:
                    continue

                if 1 <= seat_number <= max_seats:
                    valid_assignments[seat_id] = student_id

            update_data["seat_assignments"] = valid_assignments

        if not update_data:
            return jsonify({"success": False, "message": "Không có dữ liệu cần cập nhật."}), 400

        class_ref.update(update_data)

        return jsonify({
            "success": True,
            "message": "Cập nhật lớp học thành công.",
            "class": build_class_data(class_ref.get()),
        }), 200

    except Exception as error:
        print("Update class error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể cập nhật lớp học."
        }), 500


@class_bp.route("/api/admin/classes/<class_id>/seats", methods=["GET"])
def get_class_seats(class_id):
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        class_ref = db.collection("classes").document(class_id)
        class_doc = class_ref.get()

        if not class_doc.exists:
            return jsonify({"success": False, "message": "Không tìm thấy lớp học."}), 404

        data = class_doc.to_dict() or {}
        rows = normalize_int(data.get("row_number"), 0)
        columns = normalize_int(data.get("column_number"), 0)
        assignments = data.get("seat_assignments", {})

        if not isinstance(assignments, dict):
            assignments = {}

        seats = []
        for row in range(1, rows + 1):
            for column in range(1, columns + 1):
                seat_number = ((row - 1) * columns) + column
                seat_id = f"S{seat_number}"

                seats.append({
                    "seat_id": seat_id,
                    "row": row,
                    "column": column,
                    "student_id": assignments.get(seat_id)
                })

        return jsonify({
            "success": True,
            "class_id": class_id,
            "row_number": rows,
            "column_number": columns,
            "total_seats": rows * columns,
            "student_count": rows * columns,
            "seats": seats,
        }), 200

    except Exception as error:
        print("Get class seats error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể lấy ma trận lớp học."
        }), 500


@class_bp.route("/api/admin/classes/<class_id>/seats", methods=["PUT"])
def update_class_seats(class_id):
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        class_ref = db.collection("classes").document(class_id)
        class_doc = class_ref.get()

        if not class_doc.exists:
            return jsonify({"success": False, "message": "Không tìm thấy lớp học."}), 404

        data = get_json_body()
        assignments = data.get("seat_assignments")

        if not isinstance(assignments, dict):
            return jsonify({"success": False, "message": "seat_assignments phải là object."}), 400

        class_data = class_doc.to_dict() or {}
        rows = normalize_int(class_data.get("row_number"), 0)
        columns = normalize_int(class_data.get("column_number"), 0)
        max_seats = rows * columns

        valid_assignments = {}

        for seat_id, student_id in assignments.items():
            if not isinstance(seat_id, str) or not seat_id.startswith("S"):
                continue
            try:
                seat_number = int(seat_id[1:])
            except ValueError:
                continue

            if not (1 <= seat_number <= max_seats):
                continue
            if student_id is None:
                continue

            student_id = str(student_id).strip()
            if student_id:
                valid_assignments[seat_id] = student_id

        class_ref.update({"seat_assignments": valid_assignments})

        return jsonify({
            "success": True,
            "message": "Cập nhật sơ đồ chỗ ngồi thành công.",
            "seat_assignments": valid_assignments,
            "student_count": rows * columns,
        }), 200

    except Exception as error:
        print("Update class seats error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể cập nhật sơ đồ chỗ ngồi."
        }), 500


@class_bp.route("/api/admin/classes/<class_id>", methods=["DELETE"])
def delete_class(class_id):
    _, error_response = authorize_admin()
    if error_response:
        return error_response

    try:
        class_ref = db.collection("classes").document(class_id)
        class_doc = class_ref.get()

        if not class_doc.exists:
            return jsonify({"success": False, "message": "Không tìm thấy lớp học."}), 404

        class_ref.delete()

        return jsonify({"success": True, "message": "Xóa lớp học thành công."}), 200

    except Exception as error:
        print("Delete class error:", error)
        return jsonify({
            "success": False,
            "message": "Không thể xóa lớp học."
        }), 500