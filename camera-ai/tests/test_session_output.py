"""Allowlist session_results/session_evaluations: dung field theo schema cua nhom, tu choi gia tri sai."""

from datetime import datetime, timezone

import pytest

from src.privacy import AlertEventError, SeatEvaluation, SeatResult, SessionResult

NOW = datetime(2026, 10, 2, 0, 30, tzinfo=timezone.utc)


def test_session_result_serializes_result_map_per_seat():
    result = SessionResult(
        "s1",
        "Camera 201",
        NOW,
        "running",
        (SeatResult("S1", 82, 0, "focused"), SeatResult("S2", None, 1, "away")),
    )
    assert result.to_dict() == {
        "session_id": "s1",
        "camera_id": "Camera 201",
        "captured_at": NOW,
        "monitoring_status": "running",
        "result_map": {
            "S1": {"concentration": 82, "interaction": 0, "status": "focused"},
            "S2": {"concentration": None, "interaction": 1, "status": "away"},
        },
    }


def test_seat_evaluation_has_exact_allowlisted_fields():
    evaluation = SeatEvaluation("s1", "S1", NOW, 75, 80, 2, 2400)
    assert evaluation.to_dict() == {
        "session_id": "s1",
        "seat_id": "S1",
        "captured_at": NOW,
        "concentration": 75,
        "avg_concentration": 80,
        "distraction": 2,
        "observed_sec": 2400,
    }


@pytest.mark.parametrize(
    "build",
    [
        lambda: SeatResult("S1", 101, 0, "focused"),  # diem ngoai 0-100
        lambda: SeatResult("S1", 80.5, 0, "focused"),  # diem phai la so nguyen
        lambda: SeatResult("S1", 80, 0, "sleeping"),  # status ngoai danh sach
        lambda: SeatResult("a/b", 80, 0, "focused"),  # seat_id thanh duong dan Firestore
        lambda: SessionResult("s1", "Camera 201", NOW, "done", ()),
        lambda: SessionResult("s1", "Camera 201", datetime(2026, 10, 2), "running", ()),  # thieu mui gio
        lambda: SessionResult("s1", "Camera 201", NOW, "running", (SeatResult("S1", 80, 0, "focused"),) * 2),
        lambda: SeatEvaluation("s1", "S1", NOW, 75, 80, -1, 10),
        lambda: SeatEvaluation("lop-10A1/2026-10-05", "S1", NOW, 75, 80, 0, 10),
    ],
)
def test_rejects_values_outside_the_allowlist(build):
    with pytest.raises((ValueError, TypeError, AlertEventError)):
        build()
