"""
test_engagement_score.py -- Unit test cho SeatEngagementTracker
(src/engagement/engagement_score.py)

Chien luoc kiem thu: mo phong chuoi (timestamp, is_head_drop, is_slumping)
theo thoi gian, doi chieu ket qua compute_score() voi 4 vi du BANG SO da
tinh tay san trong tai lieu thiet ke (Engagement-Scoring-Formula-Task4.1.docx,
Muc 4) -- dam bao code khop DUNG voi cong thuc da cong bo, khong lech.
"""

import pytest

from src.engagement.engagement_score import EngagementScore, SeatEngagementTracker


def run_sequence(tracker: SeatEngagementTracker, segments):
    """Chay 1 chuoi segment, moi segment la (duration_sec, is_head_drop, is_slumping).
    Tu dong cong don timestamp qua tung segment va goi tracker.update()."""
    t = 0.0
    tracker.update(t, False, False)  # mau khoi tao tai t=0, chua tich luy gi
    for duration, is_drop, is_slump in segments:
        t += duration
        tracker.update(t, is_drop, is_slump)


# ----------------------------------------------------------------------
# Doi chieu voi 4 vi du trong tai lieu thiet ke task 4.1
# ----------------------------------------------------------------------


def test_example_1_full_focus_scores_100():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [(1800.0, False, False)])

    result = tracker.compute_score()

    assert result.time_normal == pytest.approx(1800.0)
    assert result.score == pytest.approx(100.0)


def test_example_2_slump_10_percent_scores_95():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [
        (1620.0, False, False),
        (180.0, False, True),
    ])

    result = tracker.compute_score()

    assert result.time_normal == pytest.approx(1620.0)
    assert result.time_slumping == pytest.approx(180.0)
    assert result.score == pytest.approx(95.0)


def test_example_3_head_drop_10_percent_scores_90():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [
        (1620.0, False, False),
        (180.0, True, False),
    ])

    result = tracker.compute_score()

    assert result.time_head_drop == pytest.approx(180.0)
    assert result.score == pytest.approx(90.0)


def test_example_4_mixed_slump_and_head_drop_scores_80():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [
        (1260.0, False, False),
        (360.0, False, True),
        (180.0, True, False),
    ])

    result = tracker.compute_score()

    assert result.time_normal == pytest.approx(1260.0)
    assert result.time_slumping == pytest.approx(360.0)
    assert result.time_head_drop == pytest.approx(180.0)
    assert result.score == pytest.approx(80.0)


# ----------------------------------------------------------------------
# Loai tru lan nhau: head_drop uu tien hon slumping khi ca hai cung True
# ----------------------------------------------------------------------


def test_both_true_simultaneously_counts_as_head_drop_only():
    """Neu is_head_drop_event VA is_slumping_event cung True, thoi gian do
    PHAI duoc tinh vao head_drop (khong duoc cong don ca 2, tranh double-count)."""
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [(100.0, True, True)])

    result = tracker.compute_score()

    assert result.time_head_drop == pytest.approx(100.0)
    assert result.time_slumping == pytest.approx(0.0)


# ----------------------------------------------------------------------
# Xu ly time_total = 0 -- khong duoc ZeroDivisionError
# ----------------------------------------------------------------------


def test_no_data_yet_returns_none_score_not_zero():
    """Seat chua tung co du lieu (chi 1 mau khoi tao, chua co elapsed nao)
    -- score phai la None, KHONG PHAI 0 (0 nghia la co du lieu va engagement
    kem, None nghia la khong co thong tin gi)."""
    tracker = SeatEngagementTracker(seat_id="A1")
    tracker.update(0.0, False, False)  # chi 1 mau duy nhat, chua co elapsed

    result = tracker.compute_score()

    assert result.score is None
    assert result.time_total == 0.0


def test_never_updated_returns_none_score():
    tracker = SeatEngagementTracker(seat_id="A1")
    result = tracker.compute_score()
    assert result.score is None


# ----------------------------------------------------------------------
# head_drop_count / slumping_count -- dem SO CHUOI SU KIEN, khong phai so frame
# ----------------------------------------------------------------------


def test_count_increments_once_per_episode_not_per_update_call():
    """3 lan update() lien tiep VAN o trong 1 chuoi head_drop -- count chi
    tang 1 lan (luc bat dau chuoi), khong tang moi lan goi update()."""
    tracker = SeatEngagementTracker(seat_id="A1")
    t = 0.0
    tracker.update(t, False, False)
    for _ in range(3):
        t += 1.0
        tracker.update(t, True, False)  # van dang trong CUNG 1 chuoi head_drop

    result = tracker.compute_score()
    assert result.head_drop_count == 1


def test_count_increments_again_after_returning_to_normal():
    """Head drop -> tro ve normal -> head drop lan nua = 2 chuoi rieng biet
    -- count phai la 2."""
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [
        (2.0, True, False),   # chuoi head_drop #1
        (2.0, False, False),  # tro ve normal
        (2.0, True, False),   # chuoi head_drop #2
    ])

    result = tracker.compute_score()
    assert result.head_drop_count == 2


def test_slumping_count_independent_of_head_drop_count():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [
        (2.0, False, True),   # slumping #1
        (2.0, True, False),   # head_drop #1 (cung la chuyen trang thai)
        (2.0, False, True),   # slumping #2
    ])

    result = tracker.compute_score()
    assert result.slumping_count == 2
    assert result.head_drop_count == 1


# ----------------------------------------------------------------------
# Cau hinh slump_credit khac mac dinh
# ----------------------------------------------------------------------


def test_custom_slump_credit_changes_score():
    """slump_credit=0.0 (khong tin chi gi ca cho slumping) phai cho diem
    THAP HON so voi slump_credit=0.5 mac dinh, voi cung du lieu dau vao."""
    tracker_default = SeatEngagementTracker(seat_id="A1", slump_credit=0.5)
    tracker_strict = SeatEngagementTracker(seat_id="A1", slump_credit=0.0)

    segments = [(1620.0, False, False), (180.0, False, True)]
    run_sequence(tracker_default, segments)
    run_sequence(tracker_strict, segments)

    score_default = tracker_default.compute_score().score
    score_strict = tracker_strict.compute_score().score

    assert score_default == pytest.approx(95.0)
    assert score_strict == pytest.approx(90.0)  # slumping bi phat toan phan nhu head_drop
    assert score_strict < score_default


# ----------------------------------------------------------------------
# reset()
# ----------------------------------------------------------------------


def test_reset_clears_accumulated_state():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [(100.0, True, False)])
    assert tracker.compute_score().time_head_drop > 0

    tracker.reset()

    result = tracker.compute_score()
    assert result.score is None
    assert result.time_total == 0.0
    assert result.head_drop_count == 0


# ----------------------------------------------------------------------
# Score luon trong khoang [0, 100]
# ----------------------------------------------------------------------


def test_score_never_exceeds_bounds():
    tracker = SeatEngagementTracker(seat_id="A1")
    run_sequence(tracker, [(100.0, True, False), (100.0, False, True)])

    result = tracker.compute_score()

    assert 0.0 <= result.score <= 100.0


def test_seat_id_preserved_in_result():
    tracker = SeatEngagementTracker(seat_id="R3C7")
    tracker.update(0.0, False, False)
    result = tracker.compute_score()
    assert result.seat_id == "R3C7"
    assert isinstance(result, EngagementScore)