import pytest

from src.pipeline import AlertCandidate, AlertManager
from src.privacy import AlertEventError


def drop(seat_id="A1", duration=5.0):
    return AlertCandidate(seat_id, "head_drop", duration)


def run(manager, frames):
    """frames: list (timestamp, [candidate...]) -> tat ca alert theo thu tu."""
    alerts = []
    for timestamp, candidates in frames:
        alerts.extend(manager.update(timestamp, candidates))
    return alerts


def test_one_alert_per_episode_even_if_detector_reports_every_frame():
    manager = AlertManager("sess", cooldown_sec=0.0)
    alerts = run(manager, [(10.0 + i * 0.5, [drop(duration=5.0 + i * 0.5)]) for i in range(20)])

    assert len(alerts) == 1
    assert alerts[0].to_dict() == {
        "session_id": "sess",
        "seat_id": "A1",
        "type": "head_drop",
        "start_sec": 5.0,  # hanh vi bat dau truoc luc alert duration giay
        "duration_sec": 5.0,
    }


def test_short_gap_keeps_episode_long_gap_starts_new_one():
    manager = AlertManager("sess", cooldown_sec=0.0, episode_gap_sec=2.0)
    alerts = run(
        manager,
        [
            (10.0, [drop()]),
            (11.0, []),  # mat 1 frame (che khuat)
            (12.0, [drop()]),  # gap 2s -> van dot cu
            (15.0, [drop()]),  # gap 3s -> dot moi
        ],
    )
    assert [alert.start_sec for alert in alerts] == [5.0, 10.0]


def test_cooldown_groups_new_episodes_then_allows_after_expiry():
    manager = AlertManager("sess", cooldown_sec=60.0, episode_gap_sec=1.0)
    alerts = run(
        manager,
        [
            (10.0, [drop()]),  # alert
            (30.0, [drop()]),  # dot moi, trong cooldown -> gom
            (69.0, [drop()]),  # dot moi, 59s sau alert -> van gom
            (70.0, []),
            (75.0, [drop()]),  # dot moi, 65s sau alert -> alert
        ],
    )
    assert [alert.start_sec for alert in alerts] == [5.0, 70.0]


def test_seats_and_types_are_independent():
    manager = AlertManager("sess")
    alerts = manager.update(
        10.0,
        [drop("A1"), drop("A2"), AlertCandidate("A1", "back_turn", 2.0)],
    )
    assert sorted((alert.seat_id, alert.type) for alert in alerts) == [
        ("A1", "back_turn"),
        ("A1", "head_drop"),
        ("A2", "head_drop"),
    ]


def test_no_alerts_while_paused_and_resume_starts_fresh_episode():
    manager = AlertManager("sess", cooldown_sec=0.0)
    manager.pause()
    assert not manager.active
    assert run(manager, [(10.0, [drop()]), (10.5, [drop()])]) == []

    manager.resume()
    alerts = run(manager, [(11.0, [drop()]), (11.5, [drop()])])
    assert len(alerts) == 1


def test_pause_keeps_cooldown_to_avoid_alert_burst_on_resume():
    manager = AlertManager("sess", cooldown_sec=60.0)
    assert len(manager.update(10.0, [drop()])) == 1
    manager.pause()
    manager.resume()
    assert manager.update(20.0, [drop()]) == []


def test_unknown_alert_type_fails_fast():
    manager = AlertManager("sess")
    with pytest.raises(AlertEventError):
        manager.update(10.0, [AlertCandidate("A1", "slumping", 5.0)])


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        AlertManager("sess", cooldown_sec=-1)


def test_invalid_session_id_rejected_at_construction():
    with pytest.raises(AlertEventError):
        AlertManager("lop 10A1")
