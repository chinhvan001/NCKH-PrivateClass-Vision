"""Nhập giáo viên, học sinh từ file Excel (.xlsx): thêm như nút Thêm, bỏ qua người đã có, file có dòng sai thì
không thêm ai."""

from datetime import datetime
from io import BytesIO

import pytest
from openpyxl import Workbook


def upload(client, url, headers, rows, filename="danh_sach.xlsx"):
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return client.post(url, headers=headers, data={"file": (buffer, filename)}, content_type="multipart/form-data")


def documents(db, collection):
    return {doc.id: doc.to_dict() for doc in db.collection(collection).stream()}


def test_teachers_are_added_like_the_add_button_and_known_emails_skipped(client, db, admin):
    db.document("teachers/t1").set({"email": "ha@school.edu.vn", "name": "Lê Thu Hà"})

    response = upload(client, "/api/import/teachers", admin, [
        ["DANH SÁCH GIÁO VIÊN NĂM HỌC 2026-2027"],
        [],
        ["STT", "Họ và tên *", "Email", "SĐT", "Bộ môn"],
        [1, "Trần Văn Nam", "Nam.Tran@School.edu.vn", 912345678, "toán"],
        [2, "Lê Thu Hà", "HA@school.edu.vn", None, "Ngữ văn"],
        [3, "Trần Văn Nam", "nam.tran@school.edu.vn", None, "Toán"],
        [],
        [4, "Phạm Thị Hoa", "hoa@school.edu.vn", "0987654321", "Hoá học"],
    ])

    body = response.get_json()
    assert response.status_code == 200, body
    assert body["success_count"] == 2
    assert body["duplicates"] == ["Lê Thu Hà (ha@school.edu.vn)", "Trần Văn Nam (nam.tran@school.edu.vn)"]
    added = {teacher["email"]: teacher for key, teacher in documents(db, "teachers").items() if key != "t1"}
    assert added["nam.tran@school.edu.vn"] == {
        "uid": None,
        "email": "nam.tran@school.edu.vn",
        "name": "Trần Văn Nam",
        "phone_number": "0912345678",
        "subject": "Toán",
        "is_active": True,
        "auth_provider": "google",
        "auth_status": "pending",
    }
    assert added["hoa@school.edu.vn"]["subject"] == "Hóa học"


def test_a_file_with_invalid_rows_adds_nobody(client, db, admin):
    response = upload(client, "/api/import/teachers", admin, [
        ["Họ tên", "Email", "Môn"],
        ["Trần Văn Nam", "nam@school.edu.vn", "Toán"],
        [],
        ["Ngô Bình", None, "Văn"],
        [None, "binh@", "Tin học"],
    ])

    assert response.status_code == 400
    assert response.get_json()["errors"] == [  # số dòng như Excel hiện, tính cả dòng trống
        "Dòng 4: thiếu email.",
        'Dòng 4: bộ môn "Văn" không có trong danh sách bộ môn.',
        "Dòng 5: thiếu họ và tên.",
        'Dòng 5: email "binh@" không hợp lệ.',
    ]
    assert documents(db, "teachers") == {}


@pytest.mark.parametrize("url", ["/api/import/teachers", "/api/import/students"])
def test_import_needs_an_admin_and_an_xlsx_file_with_a_header_row(client, db, admin, url):
    rows = [["Họ và tên", "Email", "Bộ môn"], ["An", "an@school.edu.vn", "Toán"]]

    assert upload(client, url, {}, rows).status_code == 401
    assert upload(client, url, admin, rows, "ds.pdf").get_json()["message"].startswith("Chỉ nhận file Excel .xlsx")
    broken = {"file": (BytesIO(b"PK?"), "ds.xlsx")}
    response = client.post(url, headers=admin, data=broken, content_type="multipart/form-data")
    assert response.get_json()["message"] == "Không đọc được file Excel."
    no_header = upload(client, url, admin, [["Tên", "Lớp"], ["An", "12A1"]])
    assert "Không tìm thấy dòng tiêu đề" in no_header.get_json()["message"]
    assert documents(db, "teachers") == documents(db, "students2") == {}


def test_students_are_added_with_their_class_and_known_students_skipped(client, db, admin):
    db.document("classes2/c1").set({"class_name": "12A1"})
    db.document("classes2/c2").set({"class_name": "12A2"})
    db.document("students2/s1").set({"full_name": "Nguyễn Văn An", "birthday": "2008-03-15", "gender": "male"})

    response = upload(client, "/api/import/students", admin, [
        ["Họ và tên", "Ngày sinh", "Giới tính", "Lớp", "Họ tên phụ huynh", "SĐT phụ huynh"],
        ["Trần Thị Bình", datetime(2008, 9, 2), "nữ", "12a1", "Trần Văn Cường", 912345678],
        ["nguyễn văn  an", "15/03/2008", "Nam", "12A2", None, None],
        ["Lê Minh", None, None, None, None, None],
    ])

    body = response.get_json()
    assert response.status_code == 200, body
    assert body["success_count"] == 2
    assert body["duplicates"] == ["nguyễn văn an (15/03/2008)"]
    students = {student["full_name"]: (key, student) for key, student in documents(db, "students2").items()}
    binh_id, binh = students["Trần Thị Bình"]
    assert binh["birthday"] == "2008-09-02" and binh["gender"] == "Nữ" and binh["is_active"] is True
    assert binh["parent_name"] == "Trần Văn Cường" and binh["parent_phonenumber"] == "0912345678"
    assert students["Lê Minh"][1]["birthday"] == "" and "gender" not in students["Lê Minh"][1]
    members = [(member["student_id"], member["class_id"]) for member in documents(db, "class_members").values()]
    assert members == [(binh_id, "c1")]


def test_student_rows_need_a_real_date_and_a_single_known_class(client, db, admin):
    for class_id, name in [("c1", "12A1"), ("c9", "12A1"), ("c2", "12A2")]:
        db.document(f"classes2/{class_id}").set({"class_name": name})

    response = upload(client, "/api/import/students", admin, [
        ["Họ tên học sinh", "Ngày sinh", "Giới tính", "Lớp"],
        ["An", "31/02/2008", "Nam", "12A2"],
        ["Bình", 39522, "Nữ", "12A3"],
        ["Chi", None, "khác", "12A1"],
    ])

    assert response.get_json()["errors"] == [
        'Dòng 2: ngày sinh "31/02/2008" không hợp lệ, ghi theo dd/mm/yyyy.',
        'Dòng 3: ngày sinh "39522" không hợp lệ, ghi theo dd/mm/yyyy.',
        'Dòng 3: không có lớp "12A3".',
        'Dòng 4: giới tính "khác" phải là Nam hoặc Nữ.',
        'Dòng 4: có 2 lớp tên "12A1", hãy gán lớp trên web.',
    ]
    assert documents(db, "students2") == {}


def test_add_student_button_still_writes_the_student_and_class_member(client, db, admin):
    response = client.post("/api/v1/students", headers=admin, json={"full_name": "An", "class_id": "c1"})

    student_id = response.get_json()["id"]
    assert documents(db, "students2")[student_id]["full_name"] == "An"
    assert [(m["student_id"], m["class_id"]) for m in documents(db, "class_members").values()] == [(student_id, "c1")]
