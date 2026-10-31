"""Allowlist session_windows: dung field cho backend tinh diem, tu choi gia tri sai."""

from datetime import datetime, timezone

import pytest

from src.privacy import AlertEventError, SeatWindow, SessionWindow

NOW = datetime(2026, 10, 2, 0, 30, tzinfo=timezone.utc)


def seat(seat_id="S01", normal=6.04, slumping=1.0, head_drop=2.96, **changes):
    fields = dict(last_seen_sec=19.9, last_state="head_drop", last_behaviour_sec=None, alerts={"head_drop": 1})
    return SeatWindow(seat_id, normal, slumping, head_drop, **{**fields, **changes})


def window(*seats, start=10.0, end=20.0, **changes):
    fields = dict(run="0a1b2c3d", seq=1, captured_at=NOW, monitoring_status="running")
    fields.update(changes)
    return SessionWindow("s1", "Camera 201", start_sec=start, end_sec=end, seats=seats, **fields)


def test_window_serializes_posture_seconds_per_seat_and_nothing_else():
    data = window(seat(), seat("S02", 10.0, 0.0, 0.0, last_state="normal", last_behaviour_sec=15.25, alerts={}))
    assert data.doc_id == "s1_0a1b2c3d_00001"
    assert data.to_dict() == {
        "session_id": "s1",
        "camera_id": "Camera 201",
        "run": "0a1b2c3d",
        "seq": 1,
        "start_sec": 10.0,
        "end_sec": 20.0,
        "captured_at": NOW,
        "monitoring_status": "running",
        "seats": {
            "S01": {
                "normal_sec": 6.0,
                "slumping_sec": 1.0,
                "head_drop_sec": 3.0,
                "last_seen_sec": 19.9,
                "last_state": "head_drop",
                "last_behaviour_sec": None,
                "alerts": {"head_drop": 1},
            },
            "S02": {
                "normal_sec": 10.0,
                "slumping_sec": 0.0,
                "head_drop_sec": 0.0,
                "last_seen_sec": 19.9,
                "last_state": "normal",
                "last_behaviour_sec": 15.2,
                "alerts": {},
            },
        },
    }


@pytest.mark.parametrize(
    "build",
    [
        lambda: seat(last_state="sleeping"),
        lambda: seat(normal=-1.0),
        lambda: seat(normal=float("nan")),
        lambda: seat(alerts={"keypoints": 1}),  # chi cac loai alert
        lambda: seat(alerts={"head_drop": -1}),
        lambda: seat("a/b"),
        lambda: window(seat(), run="Lop10A1!"),
        lambda: window(seat(), seq=-1),
        lambda: window(seat(), start=20.0, end=10.0),
        lambda: window(seat(normal=11.0)),  # 1 ghe khong the o lau hon do dai window
        lambda: window(seat(), seat()),
        lambda: window(seat(), captured_at=datetime(2026, 10, 2)),  # thieu mui gio
        lambda: window(seat(), monitoring_status="done"),
        lambda: SessionWindow("lop-10A1/2026-10-05", "Camera 201", "0a1b2c3d", 0, 0.0, 1.0, NOW, "running", ()),
        lambda: window({"seat_id": "S01", "keypoints": []}),
    ],
)
def test_rejects_values_outside_the_allowlist(build):
    with pytest.raises((ValueError, TypeError, AlertEventError)):
        build()
