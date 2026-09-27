"""
test_classify_posture_state_hand_activity.py -- Unit test cho hanh vi MOI
cua classify_posture_state() khi ket hop voi hand_activity (Head-Drop-Redesign,
13/09/2026).
"""

from src.engagement import SeatEngagementTracker, classify_posture_state


def test_head_drop_with_active_hands_becomes_normal():
    """head_down_engaged: dang cui dau NHUNG tay hoat dong (chep bai/lat
    trang) -> phai duoc tinh la 'normal', KHONG bi phat diem."""
    result = classify_posture_state(is_head_drop_event=True, is_slumping_event=False, hand_activity=True)
    assert result == "normal"


def test_head_drop_with_still_hands_stays_head_drop():
    """head_down_disengaged: cui dau VA tay tinh keo dai -> giu nguyen muc
    phat toan phan nhu truoc day."""
    result = classify_posture_state(is_head_drop_event=True, is_slumping_event=False, hand_activity=False)
    assert result == "head_drop"


def test_head_drop_with_unknown_hand_activity_becomes_ambiguous_slumping():
    """head_down_ambiguous: cui dau nhung KHONG xac dinh duoc tay (vi du
    wrist bi che khuat) -> tinh chi mot phan (dung chung bucket voi slumping),
    KHONG phat toan phan mot cach vo can cu."""
    result = classify_posture_state(is_head_drop_event=True, is_slumping_event=False, hand_activity=None)
    assert result == "slumping"


def test_head_drop_default_hand_activity_not_provided_is_ambiguous():
    """Neu khong truyen hand_activity (mac dinh None) -- hanh vi MOI (khac
    truoc day): tinh la ambiguous/slumping (tin chi mot phan), khong phai
    head_drop toan phan nhu code cu -- day la thay doi CO CHU DICH, an toan
    hon khi chua tich hop HandActivityMonitor."""
    result = classify_posture_state(is_head_drop_event=True, is_slumping_event=False)
    assert result == "slumping"


def test_hand_activity_ignored_when_no_head_drop():
    """hand_activity chi co tac dung khi is_head_drop_event=True -- khong
    lam thay doi ket qua slumping/normal thong thuong."""
    assert classify_posture_state(False, True, hand_activity=True) == "slumping"
    assert classify_posture_state(False, True, hand_activity=False) == "slumping"
    assert classify_posture_state(False, False, hand_activity=True) == "normal"
    assert classify_posture_state(False, False, hand_activity=False) == "normal"


def test_integration_with_seat_engagement_tracker():
    """Kiem tra tich hop day du: 10s binh thuong, 10s cui dau+tay hoat dong
    (khong bi phat), 10s cui dau+tay tinh (bi phat toan phan). Diem cuoi
    cung phai phan anh dung 20s 'tot' (10 normal + 10 head_down_engaged) va
    10s 'xau' (head_down_disengaged)."""
    tracker = SeatEngagementTracker(seat_id="A1")

    t = 0.0
    tracker.update(t, False, False)  # normal, chua tinh thoi gian (moc khoi dau)

    t += 10.0
    tracker.update(t, False, False, hand_activity=None)  # +10s normal

    t += 10.0
    tracker.update(t, True, False, hand_activity=True)  # +10s head_down_engaged -> tinh la normal

    t += 10.0
    tracker.update(t, True, False, hand_activity=False)  # +10s head_down_disengaged -> tinh la head_drop

    result = tracker.compute_score()

    assert result.time_normal == 20.0  # 10s normal + 10s head_down_engaged
    assert result.time_head_drop == 10.0  # chi phan disengaged that su
    assert result.time_slumping == 0.0
    # score = 100 * (1 - 10/30 - 0) = 100 * (1 - 0.3333) = 66.67
    assert abs(result.score - 66.67) < 0.01