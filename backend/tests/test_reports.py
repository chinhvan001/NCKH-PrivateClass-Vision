"""Job báo cáo phụ huynh (jobs/parent_reports.py), xóa tiết cùng dữ liệu camera AI, và đánh dấu tiết bị
gián đoạn trong báo cáo lớp."""

from datetime import datetime, timedelta, timezone

import pytest

from jobs import parent_reports
from services import monitoring_service, report_service

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)


def finished_session(db, session_id, *, monitoring_status="completed", ended_ago=timedelta(minutes=5), **extra):
    """Tiết của lớp c1 (An S01, Bình S02) đã kết thúc, kèm dữ liệu camera AI như edge node ghi."""
    db.document(f"sessions/{session_id}").set({
        "class_id": "c1",
        "teacher_id": "t1",
        "subject": "Toán",
        "session_date": "2026-10-05",
        "start_time": "07:00",
        "end_time": "07:45",
        "status": "completed",
        "started_at": NOW - timedelta(minutes=50),
        "ended_at": NOW - ended_ago,
        **extra,
    })
    db.document(f"session_rosters/{session_id}").set({"class_id": "c1", "seats": {"S01": "an", "S02": "binh"}})
    if monitoring_status is None:
        return  # camera AI không giám sát tiết này
    db.document(f"session_results/{session_id}").set(
        {"session_id": session_id, "camera_id": "CAM-1", "captured_at": NOW, "monitoring_status": monitoring_status}
    )
    for seat, score, observed in (("S01", 90, 2400), ("S02", 55, 40), ("S03", 70, 1800)):
        db.document(f"session_evaluations/{session_id}_{seat}").set({
            "session_id": session_id,
            "seat_id": seat,
            "captured_at": NOW,
            "concentration": score,
            "avg_concentration": score,
            "distraction": 2 if seat == "S01" else 0,
            "observed_sec": observed,
        })
    for index in range(2):  # An cúi đầu 2 lần
        alert = {"session_id": session_id, "seat_id": "S01", "type": "head_drop", "start_sec": 60.0 * index}
        db.document(f"sessions/{session_id}/alerts/{session_id}-a{index}").set({**alert, "duration_sec": 6.0})


@pytest.fixture
def school(db):
    db.document("classes2/c1").set({"class_name": "11B2", "row_count": 2, "column_count": 2, "seat_map": {}})
    for student_id, name in (("an", "Nguyễn Văn An"), ("binh", "Trần Thị Bình")):
        db.document(f"students2/{student_id}").set({"full_name": name, "parent_id": f"parent-{student_id}"})
    return db


def test_the_job_writes_one_report_per_student_with_data_and_only_once(school, capsys):
    finished_session(school, "s1")
    parent_reports.main([])
    assert "1 tiết (1 học sinh)" in capsys.readouterr().out

    report = school.docs["students2/an/reports/s1"]
    assert {key: report[key] for key in report if key != "created_at"} == {
        "session_id": "s1",
        "class_id": "c1",
        "class_name": "11B2",
        "subject": "Toán",
        "session_date": "2026-10-05",
        "start_time": "07:00",
        "end_time": "07:45",
        "avg_concentration": 90,
        "level": "good",
        "observed_min": 40,
        "alerts": {"head_drop": 2, "back_turn": 0, "side_conversation": 0},
        "partial": False,
    }
    assert "seat_id" not in report and "binh" not in str(report)
    assert "students2/binh/reports/s1" not in school.docs  # quan sát 40 s: không đủ để báo cáo
    roster = school.docs["session_rosters/s1"]
    assert roster["report_count"] == 1 and isinstance(roster["reports_at"], datetime)
    assert roster["seats"] == {"S01": "an", "S02": "binh"}

    school.document("session_evaluations/s1_S01").update({"avg_concentration": 10})
    assert report_service.build_pending_reports() == {}  # đã có báo cáo: không tạo lại
    assert school.docs["students2/an/reports/s1"]["avg_concentration"] == 90


def test_interrupted_sessions_are_marked_partial_and_unfinished_results_are_waited_for(school):
    finished_session(school, "cut", monitoring_status="incomplete")
    finished_session(school, "waiting", monitoring_status="running")  # edge node chưa chốt
    finished_session(school, "dead", monitoring_status="running", ended_ago=timedelta(hours=2))  # edge node đã chết
    finished_session(school, "old", ended_ago=timedelta(days=8))  # ngoài khoảng job quét
    finished_session(school, "nodata", monitoring_status=None)

    assert report_service.build_pending_reports() == {"cut": 1, "dead": 1, "nodata": 0}
    assert school.docs["students2/an/reports/cut"]["partial"] is True
    assert school.docs["students2/an/reports/dead"]["partial"] is True
    assert "students2/an/reports/waiting" not in school.docs
    assert "reports_at" not in school.docs["session_rosters/waiting"]

    assert report_service.build_session_reports("waiting", force=True) == 1  # --session: không chờ nữa
    assert school.docs["students2/an/reports/waiting"]["partial"] is True
    school.document("sessions/live").set({"class_id": "c1", "status": "running"})
    assert report_service.build_session_reports("live", force=True) is None


def test_a_session_without_a_frozen_roster_uses_the_class_seat_map(school):
    finished_session(school, "s1")
    school.document("session_rosters/s1").delete()
    school.document("classes2/c1").update({"seat_map": {"S01": {"row": 1, "column": 1, "student_id": "binh"}}})
    assert report_service.build_session_reports("s1") == 1
    assert school.docs["students2/binh/reports/s1"]["avg_concentration"] == 90
    assert school.docs["session_rosters/s1"]["seats"] == {"S01": "binh"}


def test_class_report_lists_each_session_with_its_data_status(client, school, admin):
    finished_session(school, "full")
    finished_session(school, "cut", monitoring_status="incomplete", session_date="2026-10-06")
    finished_session(school, "waiting", monitoring_status="running", session_date="2026-10-07")
    school.document("sessions/now").set({"class_id": "c1", "status": "running", "session_date": "2026-10-08"})
    school.document("sessions/later").set({"class_id": "c1", "status": "scheduled", "session_date": "2026-10-09"})

    detail = client.get("/api/v1/evaluations/classes/c1/details", headers=admin).get_json()["data"]
    assert [(row["id"], row["data_status"], row["seats"], row["attention"]) for row in detail["sessions"]] == [
        ("now", "live", 0, None),
        ("waiting", "pending", 2, 81.4),  # (90 * 2400 + 70 * 1800) / 4200; S02 quan sát 40 s bị bỏ
        ("cut", "partial", 2, 81.4),
        ("full", "complete", 2, 81.4),
    ]


def owned(path, session_id):
    """Document thuộc về tiết: sessions/{s} và cảnh báo, kết quả, đánh giá, roster, báo cáo của nó."""
    return (
        path.rsplit("/", 1)[-1] == session_id
        or f"/{session_id}/" in path
        or path.startswith(f"session_evaluations/{session_id}_")
    )


def test_deleting_a_session_removes_everything_it_owns(client, school, admin):
    finished_session(school, "s1")
    finished_session(school, "s2")
    report_service.build_pending_reports()
    school.document("sessions/live").set({"class_id": "c1", "status": "paused"})
    # tiết, 2 cảnh báo, kết quả, 3 đánh giá, roster, báo cáo của An
    assert len([path for path in school.docs if owned(path, "s1")]) == 9
    keep = {path for path in school.docs if not owned(path, "s1")}

    assert client.delete("/api/admin/schedules/live", headers=admin).status_code == 409
    assert client.delete("/api/admin/schedules/x", headers=admin).status_code == 404
    assert client.delete("/api/admin/schedules/s1").status_code == 401
    assert client.delete("/api/admin/schedules/s1", headers=admin).status_code == 200

    assert set(school.docs) == keep
