"""Nhập danh sách giáo viên, học sinh từ file Excel (.xlsx) admin tải lên trang quản lý.

Đọc sheet đầu tiên; dòng tiêu đề tìm theo tên cột trong 10 dòng đầu (trên đó có thể là tên trường, tên danh
sách). Có dòng sai thì không thêm ai và trả về lỗi từng dòng; người đã có trong hệ thống được bỏ qua và báo
lại. File chỉ nằm trong RAM của request, không lưu lại.
"""

import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

from flask import Blueprint, jsonify, request
from openpyxl import load_workbook

from repositories.student_repository import StudentRepository
from routes.admin_routes import new_teacher
from routes.test_helpers import admin_only, commit_writes, db
from services.student_service import gender_label

import_bp = admin_only(Blueprint("import_bp", __name__))

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000
HEADER_ROWS = 10
MAX_ERRORS = 20
VN = timezone(timedelta(hours=7))  # Việt Nam không đổi giờ theo mùa
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
SUBJECTS = (  # như SUBJECT_OPTIONS của frontend (AddTeacherForm, AccountManagementPanel)
    "Toán", "Ngữ văn", "Tiếng Anh", "Vật lý", "Hóa học", "Sinh học", "Lịch sử", "Địa lý",
    "Giáo dục kinh tế và pháp luật", "Tin học", "Công nghệ", "Âm nhạc", "Mỹ thuật", "Thể dục",
)

# {field: (tên cột hiện trong thông báo lỗi, các tên khác cũng nhận)}
TEACHER_COLUMNS = {
    "name": ("Họ và tên", "Họ tên", "Tên giáo viên", "Giáo viên"),
    "email": ("Email", "Gmail", "E-mail"),
    "phone_number": ("Số điện thoại", "SĐT", "Điện thoại"),
    "subject": ("Bộ môn", "Môn", "Môn học", "Môn dạy"),
}
STUDENT_COLUMNS = {
    "full_name": ("Họ và tên", "Họ tên", "Họ và tên học sinh", "Họ tên học sinh", "Tên học sinh"),
    "birthday": ("Ngày sinh",),
    "gender": ("Giới tính",),
    "class_name": ("Lớp",),
    "parent_name": ("Họ tên phụ huynh", "Họ và tên phụ huynh", "Tên phụ huynh", "Phụ huynh"),
    "parent_phonenumber": ("Số điện thoại phụ huynh", "SĐT phụ huynh", "Điện thoại phụ huynh", "Số điện thoại", "SĐT"),
}


class ImportFileError(ValueError):
    """File không dùng được; message hiện cho admin."""


def normalize(text):
    """'Số điện thoại (SĐT) *' -> 'so dien thoai': so tên cột, bộ môn, lớp không phân biệt hoa thường và dấu."""
    text = re.sub(r"\(.*?\)", " ", str(text)).lower().replace("đ", "d")
    text = "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def cell_text(value):
    """Giá trị ô -> chuỗi gọn; số Excel lưu dạng 12.0 thành '12'."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return " ".join(str(value).split())


def phone_text(value):
    """Ô số điện thoại để dạng số thì Excel bỏ số 0 đầu (912345678): thêm lại."""
    text = cell_text(value)
    return "0" + text if isinstance(value, (int, float)) and len(text) == 9 else text


def date_text(value):
    """Ngày -> 'YYYY-MM-DD' như form Thêm học sinh, từ ô ngày Excel, chuỗi dd/mm/yyyy hoặc Timestamp đã lưu.

    '' nếu trống, None nếu không đọc được."""
    if isinstance(value, datetime):
        return (value.astimezone(VN) if value.tzinfo else value).date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = cell_text(value)
    if not text:
        return ""
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            pass
    return None


def read_rows(file, columns, required):
    """[(số dòng trong Excel, {field: giá trị ô})] của các dòng có dữ liệu dưới dòng tiêu đề."""
    if file is None or not file.filename:
        raise ImportFileError("Chưa chọn file.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ImportFileError("Chỉ nhận file Excel .xlsx (trong Excel: Lưu thành > Excel Workbook).")
    data = file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ImportFileError("File quá lớn (tối đa 2 MB).")
    try:
        workbook = load_workbook(BytesIO(data), read_only=True, data_only=True)
        try:
            sheet = workbook.worksheets[0]
            sheet.reset_dimensions()  # kích thước ghi trong file có thể sai: đọc theo các ô thật
            return _data_rows(sheet.iter_rows(values_only=True), columns, required)
        finally:
            workbook.close()
    except ImportFileError:
        raise
    except Exception as error:  # không phải file Excel thật, file hỏng
        print("Import file error:", repr(error))
        raise ImportFileError("Không đọc được file Excel.") from error


def _data_rows(rows, columns, required):
    accepted = {field: {normalize(name) for name in names} for field, names in columns.items()}
    header, result = None, []
    for number, row in enumerate(rows, start=1):
        if header is None:
            if number > HEADER_ROWS:
                break
            header = _header(row, accepted, required)
            continue
        values = {field: row[index] if index < len(row) else None for field, index in header.items()}
        if not any(cell_text(value) for value in values.values()):
            continue
        if len(result) == MAX_ROWS:
            raise ImportFileError(f"File quá nhiều dòng (tối đa {MAX_ROWS}).")
        result.append((number, values))
    if header is None:
        names = ", ".join(columns[field][0] for field in required)
        raise ImportFileError(f"Không tìm thấy dòng tiêu đề có các cột: {names}.")
    if not result:
        raise ImportFileError("File không có dòng dữ liệu nào dưới dòng tiêu đề.")
    return result


def _header(row, accepted, required):
    """{field: vị trí cột} nếu dòng có đủ các cột bắt buộc, không thì None."""
    names = [normalize(cell) if cell is not None else "" for cell in row]
    found = {}
    for field, aliases in accepted.items():
        index = next((index for index, name in enumerate(names) if name in aliases), None)
        if index is not None:
            found[field] = index
    return found if all(field in found for field in required) else None


def _invalid(errors):
    if len(errors) > MAX_ERRORS:
        errors = errors[:MAX_ERRORS] + [f"... và {len(errors) - MAX_ERRORS} lỗi khác."]
    return jsonify({
        "success": False,
        "message": "File có dòng không hợp lệ nên chưa thêm ai. Sửa file rồi tải lên lại.",
        "errors": errors,
    }), 400


def _imported(count, duplicates, label):
    message = f"Đã thêm {count} {label}."
    if duplicates:
        message += f" Bỏ qua {len(duplicates)} {label} đã có."
    return jsonify({"success": True, "message": message, "success_count": count, "duplicates": duplicates}), 200


@import_bp.route("/api/import/teachers", methods=["POST"])
def import_teachers():
    """Như nút Thêm giáo viên; email đã có (trong hệ thống hoặc ở dòng trên) thì bỏ qua."""
    try:
        rows = read_rows(request.files.get("file"), TEACHER_COLUMNS, ("name", "email", "subject"))
    except ImportFileError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    subjects = {normalize(subject): subject for subject in SUBJECTS}
    teachers, errors = [], []
    for number, row in rows:
        name, email, subject = cell_text(row["name"]), cell_text(row["email"]).lower(), cell_text(row["subject"])
        if not name:
            errors.append(f"Dòng {number}: thiếu họ và tên.")
        if not email:
            errors.append(f"Dòng {number}: thiếu email.")
        elif not EMAIL_PATTERN.fullmatch(email):
            errors.append(f'Dòng {number}: email "{email}" không hợp lệ.')
        if not subject:
            errors.append(f"Dòng {number}: thiếu bộ môn.")
        elif normalize(subject) not in subjects:
            errors.append(f'Dòng {number}: bộ môn "{subject}" không có trong danh sách bộ môn.')
        teachers.append(new_teacher(name, email, phone_text(row.get("phone_number")), subjects.get(normalize(subject))))
    if errors:
        return _invalid(errors)

    existing = {
        str((doc.to_dict() or {}).get("email", "")).lower()
        for doc in db.collection("teachers").select(["email"]).stream()
    }
    writes, duplicates = [], []
    for teacher in teachers:
        if teacher["email"] in existing:
            duplicates.append(f"{teacher['name']} ({teacher['email']})")
            continue
        existing.add(teacher["email"])
        writes.append((db.collection("teachers").document(), teacher))
    commit_writes(writes)
    return _imported(len(writes), duplicates, "giáo viên")


@import_bp.route("/api/import/students", methods=["POST"])
def import_students():
    """Như nút Thêm học sinh; trùng là cùng họ tên và ngày sinh (kể cả cùng để trống ngày sinh)."""
    try:
        rows = read_rows(request.files.get("file"), STUDENT_COLUMNS, ("full_name",))
    except ImportFileError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    classes = {}
    for item in StudentRepository.get_all_classes():
        classes.setdefault(normalize(item["name"]), []).append(item["id"])
    students, errors = [], []
    for number, row in rows:
        student = {
            "full_name": cell_text(row["full_name"]),
            "birthday": date_text(row.get("birthday")),
            "parent_name": cell_text(row.get("parent_name")),
            "parent_phonenumber": phone_text(row.get("parent_phonenumber")),
        }
        gender, class_name = cell_text(row.get("gender")), cell_text(row.get("class_name"))
        if not student["full_name"]:
            errors.append(f"Dòng {number}: thiếu họ và tên.")
        if student["birthday"] is None:
            errors.append(f'Dòng {number}: ngày sinh "{cell_text(row["birthday"])}" không hợp lệ, ghi theo dd/mm/yyyy.')
        if gender:
            student["gender"] = gender_label(gender)
            if not student["gender"]:
                errors.append(f'Dòng {number}: giới tính "{gender}" phải là Nam hoặc Nữ.')
        if class_name:
            class_ids = classes.get(normalize(class_name), [])
            if len(class_ids) == 1:
                student["class_id"] = class_ids[0]
            elif class_ids:
                errors.append(f'Dòng {number}: có {len(class_ids)} lớp tên "{class_name}", hãy gán lớp trên web.')
            else:
                errors.append(f'Dòng {number}: không có lớp "{class_name}".')
        students.append(student)
    if errors:
        return _invalid(errors)

    existing = set()
    for doc in db.collection("students2").select(["full_name", "birthday"]).stream():
        data = doc.to_dict() or {}
        existing.add((normalize(data.get("full_name") or ""), date_text(data.get("birthday")) or ""))
    writes, duplicates = [], []
    for student in students:
        key = (normalize(student["full_name"]), student["birthday"])
        if key in existing:
            born = "/".join(reversed(student["birthday"].split("-")))
            duplicates.append(f"{student['full_name']} ({born})" if born else student["full_name"])
            continue
        existing.add(key)
        writes += StudentRepository.new_student_writes(student)
    commit_writes(writes)
    return _imported(len(students) - len(duplicates), duplicates, "học sinh")
