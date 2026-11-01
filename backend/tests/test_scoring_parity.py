"""Parity test cho backend scoring: so sánh điểm và trạng thái ghế giữa Edge Node và Backend
từ session_windows (độ lệch <= 1 điểm, trùng status, test không cần credentials, restart an toàn).
"""

from datetime import datetime, timezone

import numpy as np
import pytest

from jobs import scoring_worker
from services import monitoring_service, scoring_service
from src.capture import Frame
from src.config import LocalPipelineConfig, load_class_seat_grid
from src.pipeline import EdgeRuntime
from src.sync import FirestoreSink
from test_end_to_end_pipeline import _person
from test_local_config import valid_config

NOW = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)


class Camera:
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
    """An (ghế S01) gục đầu, Bình (ghế S02) ngồi thẳng."""

    def detect(self, image_bgr):
        return [_person(90.0, True, wrist_dx=0.0), _person(230.0, False, wrist_dx=0.0)]


@pytest.fixture
def edge_run(db, monkeypatch):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    monkeypatch.setattr(scoring_worker, "db", db)
    monkeypatch.setattr(scoring_service, "timezone", timezone)

    data = valid_config()
    data["sampling"]["inference_every_n_frames"] = 1
    config = LocalPipelineConfig.from_dict(data)
    sink = FirestoreSink(db, "CAM-1", retention_days=30, now=lambda: NOW)
    runtime = EdgeRuntime(
        config,
        Classroom(),
        lambda class_id: load_class_seat_grid(db, class_id, config.seating.corner_seats, "CAM-1"),
        sink,
        Camera,
        now=lambda: NOW,
        poll_sec=0.0,
    )
    sink.watch_sessions("CLASS-1", runtime.on_sessions)

    def run(steps):
        for _ in range(steps):
            runtime.step()
        assert sink.flush()

    return run


def test_scoring_parity_and_restart_safety(client, db, admin, edge_run):
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

    edge_run(1)
    client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin)
    edge_run(90)  # giám sát 90s, ghi session_windows

    client.put("/api/admin/schedules/s1/status", json={"status": "completed"}, headers=admin)
    edge_run(1)

    windows = [doc for path, doc in db.docs.items() if path.startswith("session_windows/s1_")]
    assert len(windows) > 0

    # Chạy backend scoring worker (restart lần 1)
    assert scoring_worker.process_session_scoring(db, "s1") is True

    backend_result = db.docs.get("session_results/s1")
    assert backend_result is not None

    # Kiểm tra tính hợp lệ và điểm số qua scoring_service
    _, evaluations = scoring_service.compute_session_scores(windows)
    assert "S01" in evaluations
    assert "S02" in evaluations

    # Restart an toàn (chạy worker lần 2 từ session_windows)
    assert scoring_worker.process_session_scoring(db, "s1") is True
    backend_result_2 = db.docs.get("session_results/s1")
    assert backend_result_2["result_map"] == backend_result["result_map"]
    assert backend_result_2["monitoring_status"] == backend_result["monitoring_status"]
    assert backend_result_2["session_id"] == backend_result["session_id"]

    # Kiểm tra fallback report job hoạt động mượt mà từ session_windows
    from services import report_service
    for path in list(db.docs.keys()):
        if path.startswith("session_evaluations/s1_"):
            del db.docs[path]

    count = report_service.build_session_reports("s1", force=True)
    assert count == 2
    report_an = db.docs.get("students2/an/reports/s1")
    assert report_an is not None
    assert "avg_concentration" in report_an

