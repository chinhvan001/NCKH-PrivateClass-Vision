"""Script đưa dữ liệu về sơ đồ đã chốt (jobs/migrate_schema.py) trên các kiểu dữ liệu cũ thấy ở Firestore thật."""

from datetime import datetime, timezone

from jobs import migrate_schema

SECRET_URL = "rtsp://admin:matkhau@192.168.1.103:554/stream"


def seed(db):
    db.document("classrooms/room-301").set(
        {"classroom_name": "301", "camera_name": "Camera 201", "ip_address": "192.168.1.219", "rtsp_port": "554"}
    )
    db.document("cameras/p302").set({"camera_name": "supernatural\n\n", "room_name": "Phòng 302", "rtsp_url": SECRET_URL})
    db.document("camera_configs/Camera 201").set({"class_id": "c1", "source": SECRET_URL})
    seat_map = {"S01": {"row": 1, "column": 1, "student_id": "an"}}
    db.document("classes2/c1").set(
        {"class_name": "11B2", "row_count": 2, "column_count": 2, "seat_map": seat_map, "seatmap": {"x": {"1": 1}}}
    )
    db.document("classes2/broken").set({"seat_map": seat_map})
    db.document("sessions/old").set({
        "class_id": "c1",
        "status": "completed",
        "session_date": datetime(2026, 10, 14, 17, 0, tzinfo=timezone.utc),  # 15/10 giờ Việt Nam
        "end_time": datetime(2026, 10, 15, 1, 45, tzinfo=timezone.utc),
        "aggregated_evaluation": {"S01": {"concentration": 5}},
        "day_of_week": None,
        "monitored_students": {"S01": {"student_id": "an", "row": 1, "column": 1, "attention_score": 80}},
    })
    db.document("sessions/new").set({"class_id": "c1", "status": "completed", "session_date": "2026-10-20"})
    db.document("session_rosters/new").set({"class_id": "c1", "seats": {"S01": "an"}, "report_count": 1})
    db.document("teachers/t1").set({"name": "Cô Ngân", "nphuongngan311@gmail.com": "x"})
    db.document("parents/p1").set({"name": "Phụ huynh", "e-mail": "ph@example.com", "birthday": "1980-01-01"})
    db.document("students2/an").set({"full_name": "Nguyễn Văn An", "is_active": "true", "gender": "Nam"})
    db.document("enrollments/e1").set({"student_id": "an"})


def test_dry_run_writes_nothing_and_apply_brings_the_data_to_the_agreed_diagram(db, capsys):
    seed(db)
    before = {path: dict(doc) for path, doc in db.docs.items()}
    migrate_schema.main([])
    out = capsys.readouterr().out
    assert db.docs == before
    assert "chưa ghi" in out and "matkhau" not in out and "Nguyễn" not in out  # chỉ ID và tên field

    migrate_schema.main(["--apply"])
    assert db.docs["cameras/Camera 201"] == {
        "camera_name": "Camera 201",
        "room_name": "301",
        "ip_address": "192.168.1.219",
        "rtsp_port": "554",
    }
    assert db.docs["cameras/p302"] == {"camera_name": "supernatural", "room_name": "Phòng 302"}
    assert db.docs["classes2/c1"]["camera_id"] == "Camera 201" and "seatmap" not in db.docs["classes2/c1"]
    assert db.docs["camera_configs/Camera 201"] == {"source": SECRET_URL}
    old = db.docs["sessions/old"]
    assert (old["session_date"], old["end_time"]) == ("2026-10-15", "08:45")
    assert not {"aggregated_evaluation", "day_of_week", "monitored_students"} & set(old)
    assert db.docs["sessions/old/monitored_students/S01"] == {
        "student_id": "an", "row": 1, "column": 1, "attention_score": 80
    }  # fmt: skip
    assert db.docs["sessions/new/monitored_students/S01"] == {"student_id": "an", "row": 1, "column": 1}
    assert db.docs["sessions/new"]["report_count"] == 1 and "session_rosters/new" not in db.docs
    assert db.docs["teachers/t1"] == {"name": "Cô Ngân"}
    assert db.docs["parents/p1"] == {"name": "Phụ huynh", "email": "ph@example.com", "birthday": "1980-01-01"}
    assert db.docs["students2/an"]["is_active"] is True
    assert "classrooms/room-301" in db.docs and "enrollments/e1" in db.docs  # app vẫn đọc: không xóa

    changes, review = migrate_schema.plan()
    assert changes == []  # chạy lại không còn gì để sửa
    assert any("classes2/broken" in item for item in review)
    assert any(item.startswith("parents/p1: có birthday") for item in review)
    assert any(item.startswith("students2: 1 học sinh có gender") for item in review)
    assert any(item.startswith("enrollments: 1 document cũ") for item in review)
