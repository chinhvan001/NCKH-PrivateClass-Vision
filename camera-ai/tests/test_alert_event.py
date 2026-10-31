import dataclasses

import pytest

from src.privacy import AlertEventError, make_alert_event


def test_alert_event_has_exact_allowlisted_fields():
    alert = make_alert_event("sess_01", " A1 ", "head_drop", 12.345, 6.04).to_dict()
    assert set(alert) == {"session_id", "seat_id", "type", "start_sec", "duration_sec"}
    assert alert == {
        "session_id": "sess_01",
        "seat_id": "A1",
        "type": "head_drop",
        "start_sec": 12.3,
        "duration_sec": 6.0,
    }


def test_alert_event_is_immutable():
    alert = make_alert_event("sess_01", "A1", "back_turn", 0, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        alert.seat_id = "B2"


@pytest.mark.parametrize(
    "args",
    [
        ("", "A1", "head_drop", 0, 1),  # session_id rong
        ("lop 10A1/co Lan", "A1", "head_drop", 0, 1),  # session_id khong phai ma opaque
        ("s" * 65, "A1", "head_drop", 0, 1),
        ("sess", " ", "head_drop", 0, 1),  # seat_id rong
        ("sess", "A1", "sleeping", 0, 1),  # type ngoai allowlist
        ("sess", "A1", "slumping", 0, 1),  # slumping chi tinh diem, khong phai alert
        ("sess", "A1", "head_drop", -1, 1),
        ("sess", "A1", "head_drop", 0, float("nan")),
        ("sess", "A1", "head_drop", "abc", 1),
    ],
)
def test_alert_event_rejects_invalid_input(args):
    with pytest.raises(AlertEventError):
        make_alert_event(*args)
