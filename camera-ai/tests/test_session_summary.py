import pytest

from src.engagement.engagement_score import EngagementScore
from src.privacy import AlertEventError, make_session_summary


def _score(seat_id, score, observed_sec, head_drops=0):
    return EngagementScore(seat_id, score, observed_sec, 0.0, 0.0, head_drops, 0)


def test_summary_is_allowlisted_and_class_average_weights_by_observed_time():
    summary = make_session_summary(
        "s1",
        "completed",
        [
            _score("B1", 0.0, 2.0),  # nguoi di ngang 2s
            _score("A2", 50.0, 600.0, head_drops=3),
            _score("A1", 100.0, 600.0),
            _score("C1", None, 0.0),  # thay 1 frame, chua co diem
        ],
    )
    data = summary.to_dict()

    assert set(data) == {"session_id", "status", "class_average", "seats"}
    assert data["class_average"] == round((100 * 600 + 50 * 600) / 1202, 2)  # trung binh thuong la 50
    assert [seat["seat_id"] for seat in data["seats"]] == ["A1", "A2", "B1", "C1"]
    assert data["seats"][1] == {
        "seat_id": "A2",
        "engagement_score": 50.0,
        "observed_sec": 600,
        "head_drop_events": 3,
        "slumping_events": 0,
    }
    assert data["seats"][3]["engagement_score"] is None


def test_summary_without_scores_has_no_class_average():
    assert make_session_summary("s1", "running", []).to_dict() == {
        "session_id": "s1",
        "status": "running",
        "class_average": None,
        "seats": [],
    }


def test_summary_rejects_unknown_status_and_unsafe_session_id():
    with pytest.raises(ValueError, match="status"):
        make_session_summary("s1", "done", [])
    with pytest.raises(AlertEventError):
        make_session_summary("lop-10A1/2026-10-05", "completed", [])
