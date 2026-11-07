"""Parity test cho backend scoring: so sánh điểm và trạng thái ghế giữa Edge Node và Backend
từ window 10 s camera AI ghi (độ lệch <= 1 điểm, trùng status, test không cần credentials, restart an toàn).
"""

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

import src.main as edge_main
from jobs import scoring_worker
from services import monitoring_service, scoring_service
from src.capture import Frame
from src.config import LocalPipelineConfig
from test_edge_contract import REGIONS
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
def edge_run(db, monkeypatch, edge_files):
    monkeypatch.setattr(monitoring_service, "utc_now", lambda: NOW)
    monkeypatch.setattr(scoring_worker, "db", db)
    monkeypatch.setattr(scoring_service, "timezone", timezone)

    data = valid_config()
    data["sampling"]["inference_every_n_frames"] = 1
    config = LocalPipelineConfig.from_dict(data)
    runtime = edge_main.edge_runtime(edge_files.root, config, Classroom(), Camera, now=lambda: NOW, poll_sec=0.0)
    sessions = edge_main.web_sessions(edge_files.root, "CAM-1")

    def run(steps):
        for _ in range(steps):
            runtime.on_sessions(sessions())
            runtime.step()

    return run


def test_scoring_parity_and_restart_safety(client, db, admin, edge_run, edge_files):
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

    edge_run(1)
    client.put("/api/admin/schedules/s1/status", json={"status": "running"}, headers=admin)
    edge_run(90)  # giám sát 90s, ghi window 10 s

    client.put("/api/admin/schedules/s1/status", json={"status": "completed"}, headers=admin)
    edge_run(1)

    assert len(edge_files.lines("sessions/s1/windows.jsonl")) > 0
    edge_result = edge_files.read("sessions/s1/result.json")
    edge_evaluations = edge_files.read("sessions/s1/evaluations.json")

    # Chạy backend scoring worker (restart lần 1): ghi vào file bóng, không đè kết quả của camera AI
    assert scoring_worker.process_session_scoring("s1") == "completed"
    assert edge_files.read("sessions/s1/result.json") == edge_result
    assert edge_files.read("sessions/s1/evaluations.json") == edge_evaluations
    backend_result = edge_files.read(f"sessions/s1/{scoring_service.RESULTS}")
    backend_evaluations = edge_files.read(f"sessions/s1/{scoring_service.EVALUATIONS}")

    # Parity: điểm backend tính từ window lệch điểm camera AI tối đa 1, trạng thái ghế trùng
    for seat in ("S01", "S02"):
        edge_seat, backend_seat = edge_result["result_map"][seat], backend_result["result_map"][seat]
        assert backend_seat["status"] == edge_seat["status"], seat
        assert abs(backend_seat["concentration"] - edge_seat["concentration"]) <= 1, seat
        backend_avg = backend_evaluations[seat]["avg_concentration"]
        assert abs(backend_avg - edge_evaluations[seat]["avg_concentration"]) <= 1, seat
    assert (backend_result["result_map"]["S01"]["status"], backend_result["result_map"]["S02"]["status"]) == (
        "drowsy",
        "focused",
    )

    # Restart an toàn (chạy worker lần 2 từ window)
    assert scoring_worker.process_session_scoring("s1") == "completed"
    backend_result_2 = edge_files.read(f"sessions/s1/{scoring_service.RESULTS}")
    assert backend_result_2["result_map"] == backend_result["result_map"]
    assert backend_result_2["monitoring_status"] == backend_result["monitoring_status"]
    assert backend_result_2["session_id"] == backend_result["session_id"]

    # Tiết đã chốt (window cuối completed) không bị tính lại ở các lượt sau: lượt đọc không tăng theo số tiết
    since = NOW - timedelta(days=scoring_worker.LOOKBACK_DAYS)
    assert scoring_worker.process_pending_sessions(db, since) == 0
    (edge_files.root / "sessions" / "s1" / scoring_service.RESULTS).unlink()
    assert scoring_worker.process_pending_sessions(db, since) == 1  # chưa chốt: tính lại

    # Kiểm tra fallback report job hoạt động mượt mà từ window
    from services import report_service
    (edge_files.root / "sessions" / "s1" / "evaluations.json").unlink()

    count = report_service.build_session_reports("s1", force=True)
    assert count == 2
    report_an = db.docs.get("students2/an/reports/s1")
    assert report_an is not None
    assert "avg_concentration" in report_an

    # Xóa tiết thì xóa cả điểm backend tính trong file bóng
    assert client.delete("/api/admin/schedules/s1", headers=admin).status_code == 200
    assert not (edge_files.root / "sessions" / "s1").exists()


def test_latest_run_is_the_last_one_written_not_the_largest_id():
    """Camera AI chạy lại giữa tiết sinh run mới với mã ngẫu nhiên: run mới có thể có mã nhỏ hơn run cũ."""

    def window(run, minute, last_state, normal_sec, head_drop_sec):
        seat = {
            "normal_sec": normal_sec,
            "slumping_sec": 0.0,
            "head_drop_sec": head_drop_sec,
            "last_seen_sec": 10.0,
            "last_state": last_state,
            "last_behaviour_sec": None,
            "alerts": {},
        }
        return {
            "session_id": "s1",
            "camera_id": "CAM-1",
            "run": run,
            "seq": 0,
            "start_sec": 0.0,
            "end_sec": 10.0,
            "captured_at": datetime(2026, 10, 5, 2, minute, tzinfo=timezone.utc),
            "monitoring_status": "running",
            "seats": {"S01": seat},
        }

    old_run = window("ffff0000", 0, "head_drop", 0.0, 10.0)  # trước khi camera AI chạy lại: gục đầu
    new_run = window("0000ffff", 5, "normal", 10.0, 0.0)  # sau khi chạy lại: ngồi thẳng
    result, _ = scoring_service.compute_session_scores([old_run, new_run])
    assert result["result_map"]["S01"] == {"concentration": 100, "interaction": 0, "status": "focused"}

