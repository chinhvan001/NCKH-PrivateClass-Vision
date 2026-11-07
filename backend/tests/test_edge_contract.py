"""Hợp đồng web admin <-> edge node chạy thật trên cùng một thư mục edge-data/, như khi cả hai chạy trên một máy.

Backend đổi status của tiết qua API và giao tiết cho camera (file camera_sessions/); EdgeRuntime của camera-ai,
nối như src/main.py nối, phản ứng và ghi kết quả; backend đọc lại đúng các file đó. Lệch tên file, field, mã ghế
hay giá trị status giữa hai bên thì test này hỏng.
"""

from datetime import datetime, timezone

import numpy as np
import pytest

import src.main as edge_main
from services import monitoring_service, report_service
from src.capture import Frame
from src.config import EdgeSettings, LocalPipelineConfig
from src.sync import camera_source
from test_end_to_end_pipeline import _person
from test_local_config import valid_config

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)  # thứ Hai 09:00 Asia/Ho_Chi_Minh, trong lịch của valid_config
# Ảnh chụp cùng cỡ khung camera 320x240: S01 quanh An (x=90), S02 quanh Bình (x=230)
REGIONS = {
    "class_id": "CLASS-1",
    "image_width": 320,
    "image_height": 240,
    "seats": {"S01": [60, 70, 120, 130], "S02": [200, 70, 260, 130]},
}


class Camera:
    """CaptureWorker giả: mỗi lần đọc trả 1 frame mới, cách nhau 1 giây."""

    def __init__(self):
        self.buffer, self.is_alive, self.index = self, False, 0

    def start(self):
        self.is_alive = True

    def stop(self):
        self.is_alive = False

    def get(self, timeout=None):
        self.index += 1
        return Frame(np.full((240, 320, 3), 128, np.uint8), 1000.0 + self.index, self.index)


class Classroom:
    """An (ghế S01) gục đầu suốt tiết, Bình (ghế S02) ngồi thẳng."""

    def detect(self, image_bgr):
        return [_person(90.0, True, wrist_dx=0.0), _person(230.0, False, wrist_dx=0.0)]


@pytest.fixture
def edge(db, monkeypatch, edge_files):
    """Edge node của camera CAM-1 trên thư mục chung; mỗi bước đọc lại tiết camera được giao, như run()."""
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    data = valid_config()  # camera CAM-1
    data["sampling"]["inference_every_n_frames"] = 1
    config = LocalPipelineConfig.from_dict(data)
    runtime = edge_main.edge_runtime(edge_files.root, config, Classroom(), Camera, now=lambda: NOW, poll_sec=0.0)
    sessions = edge_main.web_sessions(edge_files.root, "CAM-1")

    def run(steps):
        for _ in range(steps):
            runtime.on_sessions(sessions())
            runtime.step()

    return run


def test_admin_starts_and_ends_a_session_that_the_edge_node_monitors(client, db, admin, edge, edge_files):
    db.document("classes2/CLASS-1").set({
        "class_name": "11B2",
        "camera_id": "CAM-1",
        "row_count": 2,
        "column_count": 2,
        "seat_map": {
            "S01": {"seat_id": "S01", "row": 1, "column": 1, "student_id": "an", "status": "occupied"},
            "S02": {"seat_id": "S02", "row": 1, "column": 2, "student_id": "binh", "status": "occupied"},
        },
    })
    db.document("students2/an").set({"full_name": "Nguyễn Văn An"})
    db.document("students2/binh").set({"full_name": "Trần Thị Bình"})
    db.document("sessions/s1").set({"class_id": "CLASS-1", "subject": "Toán", "status": "scheduled"})
    assert client.put("/api/admin/seat-regions/CAM-1", json=REGIONS, headers=admin).status_code == 200

    edge(1)  # heartbeat đầu tiên: edge node idle, trực tuyến
    status = client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin)
    assert status.status_code == 200, status.get_json()
    # Tiết giao cho camera: sơ đồ và ô ghế, không bao giờ seat_map (ghế -> học sinh)
    order = edge_files.read("camera_sessions/CAM-1.json")
    assert set(order) == {"session_id", "status", "class_id", "row_count", "column_count", "seat_regions"}

    edge(90)  # 90 giây giám sát
    live = client.get("/api/admin/schedules/s1/monitoring", headers=admin).get_json()["data"]
    assert (live["edge"]["online"], live["edge"]["status"], live["edge"]["session_id"]) == (True, "monitoring", "s1")
    assert live["result"]["monitoring_status"] == "running"
    assert live["result"]["result_map"]["S01"]["status"] == "drowsy"
    assert live["result"]["result_map"]["S02"] == {"concentration": 100, "interaction": 0, "status": "focused"}
    assert [(a["seat_id"], a["type"]) for a in live["alerts"]] == [("S01", "head_drop")]
    seats = client.get("/api/admin/schedules/s1/seats", headers=admin).get_json()["data"]["seats"]
    assert {s["seat_id"]: s["student_name"] for s in seats if s["student_name"]} == {
        "S01": "Nguyễn Văn An",
        "S02": "Trần Thị Bình",
    }
    assert set(live["result"]["result_map"]) <= {s["seat_id"] for s in seats}

    alert_id = live["alerts"][0]["id"]
    handled = client.put(f"/api/admin/schedules/s1/alerts/{alert_id}", json={"status": "acknowledged"}, headers=admin)
    assert handled.status_code == 200

    assert client.put("/api/admin/schedules/s1/status", json={"status": "paused"}, headers=admin).status_code == 200
    edge(1)
    assert edge_files.read("edge_nodes/CAM-1.json")["status"] == "paused"
    assert client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin).status_code == 200
    assert client.put("/api/admin/schedules/s1/status", json={"status": "completed"}, headers=admin).status_code == 200
    edge(1)
    assert edge_files.read("sessions/s1/result.json")["monitoring_status"] == "completed"
    assert edge_files.read("edge_nodes/CAM-1.json")["status"] == "idle"
    live = client.get("/api/admin/schedules/s1/monitoring", headers=admin).get_json()["data"]
    assert [(a["id"], a["status"]) for a in live["alerts"]] == [(alert_id, "acknowledged")]
    # Window 10 s cho backend tính điểm (gói A): window cuối mang trạng thái kết thúc của tiết
    windows = [window["monitoring_status"] for window in edge_files.lines("sessions/s1/windows.jsonl")]
    assert windows[-1] == "completed" and set(windows[:-1]) == {"running"}

    report = client.get("/api/v1/evaluations/classes/CLASS-1/details", headers=admin).get_json()["data"]["students"]
    scores = {student["name"]: (student["attention_score"], student["status"]) for student in report}
    assert scores["Trần Thị Bình"] == (100.0, "good")
    assert scores["Nguyễn Văn An"][0] < 70.0 and scores["Nguyễn Văn An"][1] == "attention"
    assert set(scores) == {"Nguyễn Văn An", "Trần Thị Bình"}
    sessions = client.get("/api/v1/evaluations/classes/CLASS-1/details", headers=admin).get_json()["data"]["sessions"]
    assert [(row["id"], row["data_status"], row["seats"]) for row in sessions] == [("s1", "complete", 2)]

    # Job báo cáo phụ huynh, rồi xóa tiết: không còn dữ liệu nào của tiết, kể cả do edge node ghi
    assert report_service.build_pending_reports() == {"s1": 2}
    binh = db.docs["students2/binh/reports/s1"]
    assert (binh["avg_concentration"], binh["level"], binh["partial"]) == (100, "good", False)
    assert db.docs["students2/an/reports/s1"]["alerts"]["head_drop"] == 1
    assert client.delete("/api/admin/schedules/s1", headers=admin).status_code == 200
    edge(1)
    assert [path for path in db.docs if "s1" in path.split("/")] == []
    assert not (edge_files.root / "sessions" / "s1").exists()
    assert edge_files.read("edge_nodes/CAM-1.json")["status"] == "idle"
    # Firestore chỉ còn dữ liệu của web và app: không có collection nào camera AI từng ghi
    edge_collections = ("session_results", "session_evaluations", "session_windows", "edge_nodes", "camera_configs")
    assert not [path for path in db.docs if path.startswith(edge_collections) or "/alerts/" in path]


def test_seat_regions_drawn_on_the_camera_page_decide_who_sits_where(client, db, admin, edge, edge_files):
    db.document("classes2/CLASS-1").set({"class_name": "11B2", "camera_id": "CAM-1", "row_count": 2, "column_count": 2})
    db.document("sessions/s1").set({"class_id": "CLASS-1", "subject": "Toán", "status": "scheduled"})
    # Ảnh chụp 1280x960, gấp 4 khung hình 320x240 của camera. Ô S01 vẽ quanh Bình (x=230), S02 quanh An (x=90):
    # kết quả chỉ đúng khi edge node dùng ô vẽ trên web và co chúng về khung hình.
    regions = {
        "class_id": "CLASS-1",
        "image_width": 1280,
        "image_height": 960,
        "seats": {"S01": [800, 280, 1040, 520], "S02": [240, 280, 480, 520]},
    }
    saved = client.put("/api/admin/seat-regions/CAM-1", json=regions, headers=admin)
    assert saved.status_code == 200, saved.get_json()

    edge(1)
    assert client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin).status_code == 200
    # Vẽ lại ô ghế giữa tiết: tiết đang chạy giữ ô ghế lúc bắt đầu
    assert client.put("/api/admin/seat-regions/CAM-1", json=REGIONS, headers=admin).status_code == 200
    edge(90)
    result = edge_files.read("sessions/s1/result.json")["result_map"]
    assert (set(result), result["S01"]["status"], result["S02"]["status"]) == ({"S01", "S02"}, "focused", "drowsy")


def test_camera_added_on_the_web_admin_gives_the_edge_node_everything_it_needs(
    client, db, admin, monkeypatch, edge_files
):
    """Như src/main.py: edge node của camera không có config riêng; camera, địa chỉ, tiết và ô ghế lấy từ web."""
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    root = edge_files.root
    db.document("classes2/CLASS-1").set({"class_name": "11B2", "row_count": 2, "column_count": 2})
    db.document("sessions/s1").set({"class_id": "CLASS-1", "subject": "Toán", "status": "scheduled"})
    assert edge_main.list_cameras(root) == {}  # chưa có camera nào: camera AI chưa chạy edge node nào

    added = client.post("/api/admin/cameras", headers=admin, json={
        "room_name": "P201",
        "camera_name": "CAM-1",
        "class_id": "CLASS-1",
        "angle_type": "top_down",
        "ip_address": "192.168.1.103",
        "rtsp_port": "554",
        "stream_path": "/cam/realmonitor?channel=1&subtype=0",
        "username": "admin",
        "password": "p@ss",
    })
    assert added.status_code == 201, added.get_json()
    assert edge_main.list_cameras(root) == {"CAM-1": "top_down"}  # supervisor bật edge node cho camera

    config = EdgeSettings.default().for_camera("CAM-1", "top_down")
    opened, clock = [], [0.0]

    def camera():  # như src/main.py camera_node: địa chỉ đọc lại trên web mỗi lần mở camera
        opened.append(config.to_capture_config(camera_source(root, "CAM-1")).source)
        return Camera()

    runtime = edge_main.edge_runtime(
        root, config, Classroom(), camera, now=lambda: NOW, monotonic=lambda: clock[0], poll_sec=0.0
    )

    def start():
        return client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin)

    def scenario():
        yield  # heartbeat đầu tiên: idle
        assert edge_files.read("edge_nodes/CAM-1.json")["status"] == "idle"
        assert start().get_json()["code"] == "no_seat_regions"  # chưa vẽ ô ghế: camera AI không biết ai ngồi đâu
        assert client.put("/api/admin/seat-regions/CAM-1", json=REGIONS, headers=admin).status_code == 200
        started = start()
        assert started.status_code == 200, started.get_json()  # heartbeat của camera: qua kiểm tra edge_offline
        for _ in range(60):
            clock[0] += 1.0  # run() đọc lại tiết của camera mỗi giây
            yield

    steps = scenario()
    runtime.run(edge_main.web_sessions(root, "CAM-1"), lambda: next(steps, True) is True)
    assert opened == ["rtsp://admin:p%40ss@192.168.1.103:554/cam/realmonitor?channel=1&subtype=0"]
    result = edge_files.read("sessions/s1/result.json")
    assert (result["camera_id"], result["monitoring_status"]) == ("CAM-1", "incomplete")  # run() thoát giữa tiết
    assert (result["result_map"]["S01"]["status"], result["result_map"]["S02"]["status"]) == ("drowsy", "focused")
