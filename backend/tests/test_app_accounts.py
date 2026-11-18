"""Dữ liệu web ghi phải đúng dạng app giáo viên/phụ huynh (Flutter, lib/) đọc: tài khoản theo uid Firebase Auth,
map monitored_students trên document tiết kèm có mặt và điểm, session_results cho màn điểm danh."""

from datetime import datetime, timezone

import conftest
from jobs import link_accounts
from services import edge_store, report_service

NOW = datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc)


def test_web_created_teacher_gets_the_firebase_uid_as_document_id(client, db, admin):
    created = client.post("/api/admin/teachers", headers=admin, json={"name": "Lê Thu Hà", "email": "ha@example.com", "subject": "Toán"})
    assert created.status_code == 201, created.get_json()
    uid = conftest.AUTH_USERS["ha@example.com"]
    teacher = db.document(f"teachers/{uid}").get().to_dict()
    assert teacher["uid"] == uid and teacher["name"] == "Lê Thu Hà"  # app: teachers/{uid}.name


def test_parent_email_links_a_parent_account_to_the_student(client, db, admin):
    student = {"full_name": "An", "parent_name": "Mai", "parent_email": "Mai@Gmail.com", "parent_phonenumber": "0901"}
    created = client.post("/api/v1/students", headers=admin, json=student)
    student = db.document(f"students2/{created.get_json()['id']}").get().to_dict()
    uid = conftest.AUTH_USERS["mai@gmail.com"]
    assert student["parent_id"] == uid  # app phụ huynh: students2 where parent_id == uid
    assert db.document(f"parents/{uid}").get().to_dict() == {"name": "Mai", "email": "mai@gmail.com", "phone_number": "0901", "is_active": True}


def test_link_accounts_job_moves_old_teachers_and_links_parents(db):
    db.document("teachers/old-id").set({"name": "Cô Lan", "email": "lan@example.com", "uid": None})
    db.document("classes2/c1").set({"class_name": "11A1", "teacher_id": "old-id"})
    db.document("sessions/s1").set({"class_id": "c1", "teacher_id": "old-id", "status": "scheduled"})
    db.document("students2/st1").set({"full_name": "An", "parent_email": "ph@example.com"})
    assert len(link_accounts.plan()) == 2
    link_accounts.main([])
    assert conftest.AUTH_USERS == {}  # chạy thử không tạo tài khoản Firebase Auth
    link_accounts.main(["--apply"])
    uid = conftest.AUTH_USERS["lan@example.com"]
    assert db.document(f"teachers/{uid}").get().to_dict()["uid"] == uid
    assert not db.document("teachers/old-id").get().exists
    assert db.document("classes2/c1").get().to_dict()["teacher_id"] == uid
    assert db.document("sessions/s1").get().to_dict()["teacher_id"] == uid
    assert db.document("students2/st1").get().to_dict()["parent_id"] == conftest.AUTH_USERS["ph@example.com"]
    assert link_accounts.plan() == []


def test_session_document_carries_the_roster_map_with_scores_for_the_app(client, db, admin, monkeypatch, edge_files):
    from services import monitoring_service

    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    db.document("classes2/c1").set({
        "class_name": "11A1",
        "row_count": 1,
        "column_count": 2,
        "seat_map": {
            "S01": {"seat_id": "S01", "row": 1, "column": 1, "student_id": "an", "status": "occupied"},
            "S02": {"seat_id": "S02", "row": 1, "column": 2, "student_id": "binh", "status": "occupied"},
        },
    })
    db.document("students2/an").set({"full_name": "An"})
    db.document("students2/binh").set({"full_name": "Bình"})
    db.document("sessions/s1").set({"class_id": "c1", "subject": "Toán", "status": "scheduled", "session_date": "2026-11-10", "end_time": "07:45"})
    assert client.put("/api/admin/schedules/s1/status", json={"status": "running", "force": True}, headers=admin).status_code == 200
    roster = db.document("sessions/s1").get().to_dict()["monitored_students"]
    assert roster["S01"] == {"student_id": "an", "row": 1, "column": 1, "is_present": True, "is_attention": True, "attention_score": None, "note": ""}

    assert client.put("/api/admin/schedules/s1/status", json={"status": "completed"}, headers=admin).status_code == 200
    result = {"session_id": "s1", "camera_id": "CAM-1", "captured_at": NOW, "monitoring_status": "completed"}
    edge_store.write_session_file("s1", "result.json", {**result, "result_map": {"S01": {"status": "drowsy"}}})
    edge_store.write_session_file("s1", "evaluations.json", {
        "S01": {"session_id": "s1", "seat_id": "S01", "captured_at": NOW, "concentration": 40, "avg_concentration": 40, "distraction": 1, "observed_sec": 2400},
        "S02": {"session_id": "s1", "seat_id": "S02", "captured_at": NOW, "concentration": 0, "avg_concentration": 0, "distraction": 0, "observed_sec": 0},
    })
    assert report_service.build_session_reports("s1") == 1
    session = db.document("sessions/s1").get().to_dict()
    assert session["monitored_students"]["S01"] == {
        "student_id": "an", "row": 1, "column": 1, "is_present": True, "is_attention": False, "attention_score": 40, "note": "",
    }
    assert session["monitored_students"]["S02"]["is_present"] is False
    assert session["report_count"] == 1
    result = db.document("session_results/s1").get().to_dict()
    assert result["result_map"] == {"S01": {"student_id": "an", "status": "drowsy"}, "S02": {"student_id": "binh", "status": "absent"}}
    assert result["monitoring_status"] == "completed"


def test_admin_seats_a_class_student_from_the_class_page(client, db, admin):
    """Màn Thống kê & Sơ đồ lớp: bấm ghế, chọn học sinh của lớp, lưu (PUT seats). Chuyển ghế thì ghế cũ trống."""
    db.document("teachers/t1").set({"name": "GV"})
    created = client.post("/api/admin/classes", headers=admin, json={"class_name": "11A1", "teacher_id": "t1", "school_year": "2026-2027", "row_count": 1, "column_count": 2})
    class_id = created.get_json()["data"]["id"]
    student_id = client.post("/api/v1/students", headers=admin, json={"full_name": "An", "class_id": class_id}).get_json()["id"]
    students = client.get(f"/api/admin/classes/{class_id}/students", headers=admin).get_json()["data"]
    assert [s["student_id"] for s in students] == [student_id]  # danh sách để chọn trong ô ghế

    assert client.put(f"/api/admin/classes/{class_id}/seats/S01", headers=admin, json={"student_id": student_id}).status_code == 200
    assert client.put(f"/api/admin/classes/{class_id}/seats/S02", headers=admin, json={"student_id": student_id}).status_code == 200
    seat_map = db.document(f"classes2/{class_id}").get().to_dict()["seat_map"]
    assert (seat_map["S01"]["student_id"], seat_map["S01"]["status"]) == (None, "empty")
    assert (seat_map["S02"]["student_id"], seat_map["S02"]["status"]) == (student_id, "occupied")
    assert client.put(f"/api/admin/classes/{class_id}/seats/S02", headers=admin, json={"student_id": None}).status_code == 200
    assert db.document(f"classes2/{class_id}").get().to_dict()["seat_map"]["S02"]["student_id"] is None
