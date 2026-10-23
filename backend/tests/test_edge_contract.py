"""Hợp đồng web admin <-> edge node chạy thật trên cùng một FakeFirestore.

Backend đổi status của tiết qua API; EdgeRuntime của camera-ai (listener, sơ đồ lớp, FirestoreSink)
phản ứng và ghi kết quả; backend đọc lại đúng các document đó. Lệch tên collection, field, mã ghế
hay giá trị status giữa hai bên thì test này hỏng.
"""

from datetime import datetime, timezone

import numpy as np
import pytest

from services import monitoring_service, report_service
from src.capture import Frame
from src.config import LocalPipelineConfig, load_class_seat_grid
from src.pipeline import EdgeRuntime
from src.sync import FirestoreSink
from test_end_to_end_pipeline import _person
from test_local_config import valid_config

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)  # thứ Hai 09:00 Asia/Ho_Chi_Minh, trong lịch của valid_config


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
def edge(db, monkeypatch):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    data = valid_config()  # camera CAM-1 của lớp CLASS-1, 4 ghế góc (90,100) (230,100) (230,300) (90,300)
    data["sampling"]["inference_every_n_frames"] = 1
    config = LocalPipelineConfig.from_dict(data)
    sink = FirestoreSink(db, "CLASS-1", "CAM-1", retention_days=30, now=lambda: NOW)
    runtime = EdgeRuntime(
        config,
        Classroom(),
        lambda: load_class_seat_grid(db, "CLASS-1", config.seating.corner_seats),
        sink,
        Camera,
        now=lambda: NOW,
        poll_sec=0.0,
    )
    sink.watch_sessions(runtime.on_sessions)

    def run(steps):
        for _ in range(steps):
            runtime.step()
        assert sink.flush()

    return run


def test_admin_starts_and_ends_a_session_that_the_edge_node_monitors(client, db, admin, edge):
    db.document("classes2/CLASS-1").set({
        "class_name": "11B2",
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

    edge(1)  # heartbeat đầu tiên: edge node idle, trực tuyến
    status = client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin)
    assert status.status_code == 200, status.get_json()

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
    assert db.docs["edge_nodes/CAM-1"]["status"] == "paused"
    assert client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin).status_code == 200
    assert client.put("/api/admin/schedules/s1/status", json={"status": "completed"}, headers=admin).status_code == 200
    edge(1)
    assert db.docs["session_results/s1"]["monitoring_status"] == "completed"
    assert db.docs["edge_nodes/CAM-1"]["status"] == "idle"
    assert db.docs[f"sessions/s1/alerts/{alert_id}"]["status"] == "acknowledged"

    report = client.get("/api/v1/evaluations/classes/CLASS-1/details", headers=admin).get_json()["data"]["students"]
    scores = {student["name"]: (student["attention_score"], student["status"]) for student in report}
    assert scores["Trần Thị Bình"] == (100.0, "good")
    assert scores["Nguyễn Văn An"][0] < 70.0 and scores["Nguyễn Văn An"][1] == "attention"
    assert set(scores) == {"Nguyễn Văn An", "Trần Thị Bình"}
    sessions = client.get("/api/v1/evaluations/classes/CLASS-1/details", headers=admin).get_json()["data"]["sessions"]
    assert [(row["id"], row["data_status"], row["seats"]) for row in sessions] == [("s1", "complete", 2)]

    # Job báo cáo phụ huynh, rồi xóa tiết: không còn document nào của tiết, kể cả do edge node ghi
    assert report_service.build_pending_reports() == {"s1": 2}
    binh = db.docs["students2/binh/reports/s1"]
    assert (binh["avg_concentration"], binh["level"], binh["partial"]) == (100, "good", False)
    assert db.docs["students2/an/reports/s1"]["alerts"]["head_drop"] == 1
    assert client.delete("/api/admin/schedules/s1", headers=admin).status_code == 200
    edge(1)
    assert [path for path in db.docs if any(part == "s1" or part.startswith("s1_") for part in path.split("/"))] == []
    assert db.docs["edge_nodes/CAM-1"]["status"] == "idle"
