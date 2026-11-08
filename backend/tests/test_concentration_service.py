import pytest
from unittest.mock import MagicMock
from services.concentration_service import (
    ConcentrationService,
    BEHAVIOR_WEIGHTS,
    DEFAULT_INITIAL_SCORE,
    MIN_SCORE,
    MAX_SCORE,
    MAX_PENALTY_MULTIPLIER,
)


def test_behavior_weights_table():
    """Kiểm tra bảng trọng số hành vi đúng theo yêu cầu kỹ thuật."""
    assert BEHAVIOR_WEIGHTS["attentive"] == 1.0
    assert BEHAVIOR_WEIGHTS["slightly_distracted"] == -1.5
    assert BEHAVIOR_WEIGHTS["looking_down"] == -3.0
    assert BEHAVIOR_WEIGHTS["sleeping"] == -4.5
    assert BEHAVIOR_WEIGHTS["using_phone"] == -6.0
    assert BEHAVIOR_WEIGHTS["away_from_seat"] == -4.0
    assert BEHAVIOR_WEIGHTS["active_participating"] == 4.0


def test_multiplier_calculation_for_violations():
    """
    Kiểm tra hệ số lũy tiến multiplier = min(2.5, 1.0 + (duration / 20.0))
    cho các hành vi bị trừ điểm.
    """
    # Duration = 0 -> multiplier = 1.0
    assert ConcentrationService.calculate_multiplier("using_phone", 0.0) == 1.0

    # Duration = 10 -> multiplier = 1.0 + 10/20 = 1.5
    assert ConcentrationService.calculate_multiplier("sleeping", 10.0) == 1.5

    # Duration = 20 -> multiplier = 1.0 + 20/20 = 2.0
    assert ConcentrationService.calculate_multiplier("looking_down", 20.0) == 2.0

    # Duration = 30 -> multiplier = 1.0 + 30/20 = 2.5
    assert ConcentrationService.calculate_multiplier("away_from_seat", 30.0) == 2.5

    # Duration = 60 -> vượt trần 2.5 -> phải được chặn ở 2.5
    assert ConcentrationService.calculate_multiplier("using_phone", 60.0) == MAX_PENALTY_MULTIPLIER


def test_multiplier_for_positive_behaviors():
    """
    Các hành vi tích cực/cộng điểm không bị tăng phạt mà multiplier = 1.0.
    """
    assert ConcentrationService.calculate_multiplier("attentive", 0.0) == 1.0
    assert ConcentrationService.calculate_multiplier("attentive", 45.0) == 1.0
    assert ConcentrationService.calculate_multiplier("active_participating", 30.0) == 1.0


def test_compute_student_score_deductions():
    """Kiểm tra tính điểm khi bị trừ điểm kèm multiplier."""
    # Điểm ban đầu 100, using_phone (-6.0), duration 20s (multiplier = 2.0)
    # delta = -6.0 * 2.0 = -12.0 -> new_score = 88.0
    new_score, delta, multiplier = ConcentrationService.compute_student_score(
        previous_score=100.0,
        behavior_state="using_phone",
        duration_counter=20.0,
    )
    assert multiplier == 2.0
    assert delta == -12.0
    assert new_score == 88.0


def test_compute_student_score_additions():
    """Kiểm tra tính điểm khi cộng điểm (active_participating +4.0)."""
    new_score, delta, multiplier = ConcentrationService.compute_student_score(
        previous_score=80.0,
        behavior_state="active_participating",
        duration_counter=15.0,
    )
    assert multiplier == 1.0
    assert delta == 4.0
    assert new_score == 84.0


def test_score_clamping_boundaries():
    """Kiểm tra giới hạn điểm số trong khoảng [0.0, 100.0]."""
    # Không vượt quá 100.0 khi cộng điểm
    score_over, _, _ = ConcentrationService.compute_student_score(
        previous_score=98.0,
        behavior_state="active_participating",
        duration_counter=5.0,
    )
    assert score_over == 100.0

    # Không giảm xuống dưới 0.0 khi trừ điểm nặng
    score_under, _, _ = ConcentrationService.compute_student_score(
        previous_score=5.0,
        behavior_state="using_phone",
        duration_counter=30.0,
    )
    assert score_under == 0.0


def test_invalid_behavior_state_raises_error():
    """Kiểm tra ngoại lệ khi behavior_state không nằm trong danh sách định trước."""
    with pytest.raises(ValueError, match="không hợp lệ"):
        ConcentrationService.compute_student_score(
            previous_score=100.0,
            behavior_state="unknown_behavior",
            duration_counter=0.0,
        )


def test_process_camera_ai_payload_end_to_end_mock():
    """Kiểm tra luồng xử lý toàn diện từ Service với Mock Repository."""
    mock_repo = MagicMock()
    # Giả lập học sinh ST_001 đã có điểm 90.0, học sinh ST_002 chưa có (mặc định 100.0)
    mock_repo.get_classroom_live_scores_map.return_value = {
        "ST_001": 90.0
    }
    mock_repo.save_live_scores_batch.return_value = 2

    service = ConcentrationService(repository=mock_repo)

    payload = [
        {
            "student_id": "ST_001",
            "behavior_state": "attentive",
            "duration_counter": 5.0,
            "seat_id": "S01",
        },
        {
            "student_id": "ST_002",
            "behavior_state": "sleeping",
            "duration_counter": 10.0,
            "seat_id": "S02",
        },
    ]

    result = service.process_camera_ai_payload("CLASS_10A", payload)

    assert result["success"] is True
    assert result["classroom_id"] == "CLASS_10A"
    assert result["total_students"] == 2
    assert result["saved_count"] == 2

    # ST_001: 90.0 + 1.0 = 91.0
    res_st1 = next(r for r in result["results"] if r["student_id"] == "ST_001")
    assert res_st1["previous_score"] == 90.0
    assert res_st1["current_score"] == 91.0
    assert res_st1["delta"] == 1.0

    # ST_002: ban đầu mặc định 100.0, sleeping (-4.5), duration 10s (multiplier = 1.5)
    # delta = -4.5 * 1.5 = -6.75 -> current_score = 100.0 - 6.75 = 93.25
    res_st2 = next(r for r in result["results"] if r["student_id"] == "ST_002")
    assert res_st2["previous_score"] == 100.0
    assert res_st2["multiplier"] == 1.5
    assert res_st2["delta"] == -6.75
    assert res_st2["current_score"] == 93.25

    mock_repo.save_live_scores_batch.assert_called_once()
