"""API giám sát và báo cáo của web admin trên hợp đồng Firestore với edge node
(camera-ai/docs/web_admin_integration.md): bắt đầu, tạm dừng, kết thúc tiết; xem trực tiếp;
xử lý cảnh báo; báo cáo theo học sinh."""

from datetime import datetime, timedelta, timezone

import pytest

from conftest import TOKENS
from services import monitoring_service

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)


def seed(db, *, edge_age_sec=5):
    """Lớp 2x2 có An ngồi S01, tiết s1 đã lên lịch, edge node của lớp gửi heartbeat edge_age_sec giây trước."""
    db.document("classes2/c1").set({
        "class_name": "11B2",
        "camera_id": "CAM-1",
        "row_count": 2,
        "column_count": 2,
        "seat_map": {
            "S01": {"seat_id": "S01", "row": 1, "column": 1, "student_id": "st1", "status": "occupied"},
            "S02": {"seat_id": "S02", "row": 1, "column": 2, "student_id": None, "status": "empty"},
        },
    })
    db.document("students2/st1").set({"full_name": "Nguyễn Văn An", "parent_phone": "0900000000"})
    db.document("sessions/s1").set(
        {"class_id": "c1", "teacher_id": "t1", "subject": "Toán", "end_time": "07:45", "status": "scheduled"}
    )
    if edge_age_sec is not None:
        db.document("edge_nodes/CAM-1").set(
            {"class_id": "c1", "online": True, "status": "idle", "updated_at": NOW - timedelta(seconds=edge_age_sec)}
        )


def set_status(client, headers, status, session_id="s1", **extra):
    return client.put(f"/api/admin/schedules/{session_id}/status", json={"status": status, **extra}, headers=headers)


@pytest.mark.parametrize("method, url", [
    ("get", "/api/admin/dashboard-stats"),
    ("get", "/api/v1/evaluations/classes-overview"),
    ("get", "/api/v1/evaluations/classes/c1/details"),
    ("get", "/api/v1/students"),
    ("delete", "/api/v1/students/st1"),
    ("get", "/api/admin/schedules/s1/monitoring"),
    ("get", "/api/admin/schedules/s1/seats"),
    ("put", "/api/admin/schedules/s1/alerts/a1"),
    ("put", "/api/admin/schedules/s1/status"),
])
def test_monitoring_and_report_endpoints_need_an_admin(client, db, method, url):
    seed(db)
    TOKENS["teacher-token"] = {"uid": "t1"}  # đăng nhập được nhưng không có admins/t1
    assert getattr(client, method)(url).status_code == 401
    assert getattr(client, method)(url, headers={"Authorization": "Bearer teacher-token"}).status_code == 403
    assert client.options(url).status_code == 200  # preflight CORS không cần token
    assert "is_active" not in db.docs["students2/st1"]


def test_a_new_class_gets_the_seat_ids_the_edge_node_uses_on_first_load(client, db, admin):
    db.document("classes2/c9").set({"class_name": "10A1", "row_count": 2, "column_count": 3, "seat_map": {}})
    response = client.get("/api/admin/classes/c9/seats", headers=admin)
    assert response.status_code == 200
    seats = [(seat["seat_id"], seat["row"], seat["column"]) for seat in response.get_json()["data"]]
    assert seats == [
        (monitoring_service.seat_id(row, column, 3), row, column) for row in (1, 2) for column in (1, 2, 3)
    ]
    assert seats[0][0] == "S01" and seats[-1][0] == "S06"


def test_start_freezes_the_seat_plan_and_completion_keeps_the_timetable(client, db, admin):
    seed(db)
    response = set_status(client, admin, "running")
    assert response.status_code == 200, response.get_json()
    session = db.docs["sessions/s1"]
    assert session["status"] == "running" and isinstance(session["started_at"], datetime)
    assert session["camera_id"] == "CAM-1"  # camera của lớp lúc bắt đầu, theo sơ đồ đã chốt
    # monitored_student của sơ đồ đã chốt: subcollection, để edge node nghe document tiết không thấy mã học sinh
    assert db.docs["sessions/s1/monitored_students/S01"] == {"student_id": "st1", "row": 1, "column": 1}
    assert [path for path in db.docs if "/monitored_students/" in path] == ["sessions/s1/monitored_students/S01"]
    assert "student" not in str(session)

    # Đổi chỗ sau khi tiết bắt đầu: sơ đồ của tiết vẫn theo bản chốt
    seat_map = db.docs["classes2/c1"]["seat_map"]
    db.document("classes2/c1").update({"seat_map": {**seat_map, "S01": {**seat_map["S01"], "student_id": None}}})
    plan = client.get("/api/admin/schedules/s1/seats", headers=admin).get_json()["data"]
    assert (plan["row_count"], plan["column_count"]) == (2, 2)
    assert [(s["seat_id"], s["row"], s["column"], s["student_name"]) for s in plan["seats"]] == [
        ("S01", 1, 1, "Nguyễn Văn An"),
        ("S02", 1, 2, ""),
        ("S03", 2, 1, ""),
        ("S04", 2, 2, ""),
    ]

    assert set_status(client, admin, "paused").status_code == 200
    assert set_status(client, admin, "running").status_code == 200  # tiếp tục: không kiểm tra lại
    assert db.docs["sessions/s1"]["started_at"] == session["started_at"]
    assert set_status(client, admin, "completed").status_code == 200
    session = db.docs["sessions/s1"]
    assert session["status"] == "completed" and isinstance(session["ended_at"], datetime)
    assert session["end_time"] == "07:45"
    assert set_status(client, admin, "running").status_code == 409


@pytest.mark.parametrize("change, code", [
    (lambda db: db.document("classes2/c1").update({"row_count": 0}), "no_seat_plan"),
    (lambda db: db.document("classes2/c1").update({"column_count": 51}), "no_seat_plan"),
    (lambda db: db.document("classes2/c1").delete(), "no_seat_plan"),
    (lambda db: db.document("edge_nodes/CAM-1").update({"updated_at": NOW - timedelta(seconds=31)}), "edge_offline"),
    (lambda db: db.document("edge_nodes/CAM-1").update({"online": False}), "edge_offline"),
    (lambda db: db.document("edge_nodes/CAM-1").delete(), "edge_offline"),
    (lambda db: db.document("sessions/s0").set({"class_id": "c1", "status": "paused"}), "class_busy"),
])
def test_start_is_refused_with_a_reason(client, db, admin, change, code):
    seed(db)
    change(db)
    response = set_status(client, admin, "running")
    assert response.status_code == 409
    assert response.get_json()["code"] == code
    assert db.docs["sessions/s1"]["status"] == "scheduled"
    assert not any("/monitored_students/" in path for path in db.docs)


def test_force_starts_without_an_online_edge_node_but_never_without_a_seat_plan(client, db, admin):
    seed(db, edge_age_sec=None)
    assert set_status(client, admin, "running", force=True).status_code == 200
    db.document("sessions/s2").set({"class_id": "c2", "status": "scheduled"})
    assert set_status(client, admin, "running", session_id="s2", force=True).get_json()["code"] == "no_seat_plan"


def test_live_view_and_dashboard_show_the_edge_output_and_alerts_can_be_handled(client, db, admin):
    seed(db)
    set_status(client, admin, "running")
    # Các document edge node ghi (camera-ai/src/privacy/session_output.py, alert_event.py, sync/firestore_sink.py)
    db.document("edge_nodes/CAM-1").update({"status": "monitoring", "session_id": "s1", "fps": 4.5, "camera_ok": True})
    db.document("session_results/s1").set({
        "session_id": "s1",
        "camera_id": "CAM-1",
        "captured_at": NOW,
        "monitoring_status": "running",
        "result_map": {"S01": {"concentration": 40, "interaction": 0, "status": "drowsy"}},
        "expire_at": NOW + timedelta(days=30),
    })
    for i in range(25):
        db.document(f"sessions/s1/alerts/a{i}").set(
            {"session_id": "s1", "seat_id": "S01", "type": "head_drop", "start_sec": i * 10.0, "duration_sec": 8.0}
        )

    data = client.get("/api/admin/schedules/s1/monitoring", headers=admin).get_json()["data"]
    assert data["session"]["status"] == "running"
    assert (data["edge"]["camera_id"], data["edge"]["online"], data["edge"]["status"]) == ("CAM-1", True, "monitoring")
    assert data["result"]["result_map"]["S01"] == {"concentration": 40, "interaction": 0, "status": "drowsy"}
    assert data["result"]["captured_at"] == NOW.isoformat()
    assert [alert["id"] for alert in data["alerts"]] == [f"a{i}" for i in range(24, 4, -1)]  # 20 cảnh báo mới nhất

    def handle(alert_id, status):
        return client.put(f"/api/admin/schedules/s1/alerts/{alert_id}", json={"status": status}, headers=admin)

    assert handle("a24", "acknowledged").status_code == 200
    alert = db.docs["sessions/s1/alerts/a24"]
    assert (alert["status"], alert["handled_by"], alert["type"]) == ("acknowledged", "admin-1", "head_drop")
    assert isinstance(alert["handled_at"], datetime)
    assert handle("a24", "open").status_code == 400
    assert handle("x", "dismissed").status_code == 404
    assert client.get("/api/admin/schedules/x/monitoring", headers=admin).status_code == 404

    dashboard = client.get("/api/admin/dashboard-stats", headers=admin).get_json()
    assert dashboard["active_sessions"] == [
        {"id": "s1", "class_name": "11B2", "teacher": "Giáo viên", "students": 1, "status": "Đang giám sát"}
    ]
    assert [(a["title"], a["description"], a["handled"]) for a in dashboard["alerts"][:2]] == [
        ("Cúi đầu kéo dài", "11B2 · ghế S01 · phút 5", True),
        ("Cúi đầu kéo dài", "11B2 · ghế S01 · phút 4", False),
    ]
    assert dashboard["system_status"]["monitoring"] == "1/1 camera AI trực tuyến"
    assert [a["title"] for a in dashboard["activities"]] == ["Bắt đầu giám sát"]


def test_reports_weight_by_observed_time_and_follow_each_sessions_roster(client, db, admin):
    seed(db)
    db.document("students2/st2").set({"full_name": "Trần Thị Bình"})
    # s1: An ở S01. s2: chốt khi Bình ngồi S01 và An chuyển sang S02.
    db.document("sessions/s1").update({"status": "completed"})
    db.document("sessions/s1/monitored_students/S01").set({"student_id": "st1", "row": 1, "column": 1})
    db.document("sessions/s2").set({"class_id": "c1", "subject": "Toán", "status": "completed"})
    db.document("sessions/s2/monitored_students/S01").set({"student_id": "st2", "row": 1, "column": 1})
    db.document("sessions/s2/monitored_students/S02").set({"student_id": "st1", "row": 1, "column": 2})

    def evaluation(session_id, seat_id, score, observed_sec):
        db.document(f"session_evaluations/{session_id}_{seat_id}").set({
            "session_id": session_id,
            "seat_id": seat_id,
            "captured_at": NOW,
            "concentration": score,
            "avg_concentration": score,
            "distraction": 0,
            "observed_sec": observed_sec,
        })

    evaluation("s1", "S01", 90, 2400)  # An, 40 phút
    evaluation("s1", "S03", 20, 30)  # người đi ngang qua: không tính
    evaluation("s2", "S01", 60, 2400)  # Bình
    evaluation("s2", "S02", 60, 1200)  # An, 20 phút
    evaluation("s2", "S04", 75, 600)  # ghế chưa xếp học sinh

    detail = client.get("/api/v1/evaluations/classes/c1/details", headers=admin).get_json()["data"]
    assert (detail["class_name"], detail["subject"]) == ("11B2", "Toán")
    assert [(s["name"], s["attention_score"], s["status"]) for s in detail["students"]] == [
        ("Nguyễn Văn An", 80.0, "good"),  # (90 * 2400 + 60 * 1200) / 3600
        ("Trần Thị Bình", 60.0, "attention"),
        ("Ghế S04 (chưa xếp học sinh)", 75.0, "stable"),
    ]
    assert client.get("/api/v1/evaluations/classes/x/details", headers=admin).status_code == 404

    overview = client.get("/api/v1/evaluations/classes-overview", headers=admin).get_json()["data"]
    assert [(c["id"], c["name"], c["students"], c["attention"], c["status"]) for c in overview] == [
        ("c1", "11B2", 3, 71.7, "stable")
    ]

    concentration = client.get("/api/admin/dashboard-stats", headers=admin).get_json()["concentration"]
    assert concentration == {"high": 25.0, "medium": 25.0, "low": 50.0, "avg_score": 72.3, "has_data": True}
