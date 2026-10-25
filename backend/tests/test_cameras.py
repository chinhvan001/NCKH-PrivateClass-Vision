"""Trang camera: địa chỉ RTSP (có mật khẩu) không bao giờ nằm trong Firestore, tình trạng camera lấy từ
heartbeat của camera AI (edge_nodes/{camera_id})."""

from datetime import datetime, timedelta, timezone

import pytest

from services import monitoring_service

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)
SECRET_URL = "rtsp://admin:matkhau@192.168.1.103:554/stream"


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)


def heartbeat(db, camera_id, *, age_sec, class_id="c1"):
    db.document(f"edge_nodes/{camera_id}").set({
        "class_id": class_id,
        "online": True,
        "status": "monitoring",
        "session_id": "s1",
        "fps": 4.8,
        "camera_ok": True,
        "last_frame_at": NOW,
        "updated_at": NOW - timedelta(seconds=age_sec),
    })


def test_cameras_never_store_or_return_an_rtsp_url(client, db, admin):
    db.document("classrooms/p201").set({"classroom_name": "P201", "status": "offline"})
    db.document("classrooms/p202").set({  # dữ liệu cũ, trước khi bỏ rtsp_url
        "classroom_name": "P202",
        "camera_name": "Camera 202",
        "ip_address": "192.168.1.104",
        "rtsp_port": "554",
        "rtsp_url": SECRET_URL,
    })
    created = client.post(
        "/api/admin/cameras",
        json={"room_id": "p201", "camera_name": "Camera 201", "ip_address": "192.168.1.103", "rtsp_port": 554,
              "rtsp_url": SECRET_URL},
        headers=admin,
    )
    assert created.status_code == 201

    listed = client.get("/api/admin/cameras", headers=admin)
    assert listed.status_code == 200
    assert "matkhau" not in listed.get_data(as_text=True)
    assert all("rtsp_url" not in doc for path, doc in db.docs.items() if path.startswith("classrooms/"))
    assert db.docs["classrooms/p201"]["camera_name"] == "Camera 201"

    for url in ("/api/admin/cameras/test-connection", "/api/admin/cameras/p201/configure"):
        assert client.post(url, json={"rtsp_url": "file:///etc/passwd"}, headers=admin).status_code in (404, 405)
        assert client.put(url, json={}, headers=admin).status_code in (404, 405)


def test_camera_status_comes_from_the_edge_heartbeat(client, db, admin):
    db.document("classes2/c1").set({"class_name": "11B2", "seat_map": {"S01": {"student_id": "an"}}})
    for room in ("201", "202", "203"):
        db.document(f"classrooms/p{room}").set({"classroom_name": f"P{room}", "camera_name": f"Camera {room}"})
    heartbeat(db, "Camera 201", age_sec=5)
    heartbeat(db, "Camera 202", age_sec=31)  # quá 30 s không gửi: offline
    heartbeat(db, "Camera 9", age_sec=1, class_id="c9")  # camera AI chưa khai báo trong phòng nào

    response = client.get("/api/admin/cameras", headers=admin)
    cameras = {camera["name"]: camera for camera in response.get_json()["cameras"]}
    assert cameras["Camera 201"]["status"] == "online"
    assert cameras["Camera 201"]["edge"]["class_name"] == "11B2"
    assert cameras["Camera 201"]["edge"]["status"] == "monitoring"
    assert (cameras["Camera 202"]["status"], cameras["Camera 202"]["edge"]["online"]) == ("offline", False)
    assert (cameras["Camera 203"]["status"], cameras["Camera 203"]["edge"]) == ("offline", None)
    assert (cameras["Camera 9"]["room_id"], cameras["Camera 9"]["status"]) == (None, "online")
    assert "an" not in str(cameras)  # sơ đồ ghế không đi kèm


def test_classroom_routes_drop_rtsp_urls(client, db, admin):
    created = client.post(
        "/api/admin/classrooms", json={"classroom_name": "P301", "rtsp_url": SECRET_URL}, headers=admin
    ).get_json()["classroom"]
    assert "rtsp_url" not in created and "rtsp_url" not in db.docs[f"classrooms/{created['id']}"]

    db.document("classrooms/p302").set({"classroom_name": "P302", "rtsp_url": SECRET_URL})
    updated = client.put("/api/admin/classrooms/p302", json={"camera_name": "Camera 302"}, headers=admin)
    assert updated.status_code == 200
    assert "rtsp_url" not in updated.get_json()["classroom"]
    assert "rtsp_url" not in db.docs["classrooms/p302"]


def test_admin_draws_seat_regions_for_a_camera(client, db, admin):
    db.document("classes2/c1").set({"class_name": "11B2", "row_count": 2, "column_count": 3})
    body = {
        "class_id": "c1",
        "image_width": 1280,
        "image_height": 720,
        "seats": {"S01": [10, 20, 110.04, 220], "S06": [900, 400, 1000, 600]},
    }
    assert client.get("/api/admin/seat-regions/CAM-1", headers=admin).get_json()["seat_regions"] is None
    saved = client.put("/api/admin/seat-regions/CAM-1", json=body, headers=admin)
    assert saved.status_code == 200, saved.get_json()
    stored = db.docs["seat_regions/CAM-1"]
    assert stored["seats"] == {"S01": [10.0, 20.0, 110.0, 220.0], "S06": [900.0, 400.0, 1000.0, 600.0]}
    assert (stored["class_id"], stored["image_width"], stored["updated_by"]) == ("c1", 1280, "admin-1")
    assert client.get("/api/admin/seat-regions/CAM-1", headers=admin).get_json()["seat_regions"]["seats"] == stored[
        "seats"
    ]

    for bad in (
        {**body, "seats": {"S07": [0, 0, 10, 10]}},  # lớp 2x3 không có S07
        {**body, "seats": {"S01": [110, 20, 10, 220]}},  # x1 > x2
        {**body, "seats": {"S01": [0, 0, 1300, 10]}},  # ra ngoài ảnh
        {**body, "seats": {"S01": [0, 0, True, 10]}},
        {**body, "image_width": 0},
        {**body, "class_id": "missing"},
    ):
        assert client.put("/api/admin/seat-regions/CAM-1", json=bad, headers=admin).status_code == 400
    assert db.docs["seat_regions/CAM-1"]["seats"] == stored["seats"]

    # Xóa hết ô: camera AI quay về 4 ghế góc trong cấu hình của nó
    assert client.put("/api/admin/seat-regions/CAM-1", json={**body, "seats": {}}, headers=admin).status_code == 200
    assert "seat_regions/CAM-1" not in db.docs
    assert client.get("/api/admin/seat-regions/CAM-1").status_code == 401
