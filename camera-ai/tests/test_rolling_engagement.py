"""
test_rolling_engagement.py -- Unit test cho RollingSeatEngagementTracker
(src/engagement/rolling_engagement.py, task 4.3)
"""

import pytest

from src.engagement import RollingSeatEngagementTracker, SeatEngagementTracker


def run_sequence(tracker, segments, start=0.0):
    """Chay 1 chuoi (duration, is_drop, is_slump) qua tracker, tra ve
    timestamp cuoi cung.

    Luu y: cac ham dung ham nay de test PRUNING/WINDOWING (khong phai test
    rieng cho gap-handling) deu can tracker duoc tao voi max_gap_sec du lon
    (lon hon moi duration su dung), vi run_sequence goi update() MOT LAN cho
    moi ca doan -- neu duration vuot qua max_gap_sec mac dinh (30s), doan do
    se bi hieu nham la mot khoang trong that su (dung y dinh cua
    max_gap_sec, xem cac test rieng ben duoi danh cho no)."""
    t = start
    tracker.update(t, False, False)
    for duration, is_drop, is_slump in segments:
        t += duration
        tracker.update(t, is_drop, is_slump)
    return t


# ----------------------------------------------------------------------
# Hanh vi co ban: window cang nho cang "quen" du lieu cu
# ----------------------------------------------------------------------


def test_old_segments_pruned_outside_window():
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=100.0, max_gap_sec=1000.0)
    run_sequence(tracker, [(200.0, True, False)])  # 200s head_drop, vuot xa window 100s

    result = tracker.compute_score()

    # Chi con toi da 100s gan nhat duoc tinh, khong phai 200s
    assert result.time_total <= 100.0 + 1e-6
    assert result.time_head_drop == pytest.approx(100.0, abs=1e-6)


def test_rolling_score_reflects_recent_behavior_not_whole_session():
    """Day la muc dich chinh cua task 4.3: mo phong 1 buoi hoc dai voi giai
    doan dau tot, giai doan cuoi kem -- diem CUMULATIVE (SeatEngagementTracker)
    van cao (bi pha loang), nhung diem ROLLING (RollingSeatEngagementTracker,
    window nho) phai phan anh dung xu huong GAN DAY (kem)."""
    cumulative = SeatEngagementTracker(seat_id="A1")
    rolling = RollingSeatEngagementTracker(seat_id="A1", window_sec=300.0, max_gap_sec=1000.0)  # 5 phut

    t = 0.0
    cumulative.update(t, False, False)
    rolling.update(t, False, False)

    # 50 phut dau: tap trung tot
    t += 3000.0
    cumulative.update(t, False, False)
    rolling.update(t, False, False)

    # 10 phut cuoi: cui dau lien tuc
    t += 600.0
    cumulative.update(t, True, False)
    rolling.update(t, True, False)

    cumulative_result = cumulative.compute_score()
    rolling_result = rolling.compute_score()

    assert cumulative_result.score > 80, "Diem cumulative van phai cao vi bi pha loang boi 50 phut dau tot"
    assert rolling_result.score < 20, "Diem rolling (5 phut gan nhat) phai phan anh dung xu huong kem gan day"


def test_window_score_matches_cumulative_when_session_shorter_than_window():
    """Neu toan bo session ngan hon window_sec, ket qua rolling va cumulative
    phai GIONG NHAU (khong co gi de 'quen' ca)."""
    cumulative = SeatEngagementTracker(seat_id="A1")
    rolling = RollingSeatEngagementTracker(seat_id="A1", window_sec=600.0, max_gap_sec=1000.0)

    segments = [(100.0, False, False), (50.0, False, True), (30.0, True, False)]
    for tracker in (cumulative, rolling):
        run_sequence(tracker, segments)

    c = cumulative.compute_score()
    r = rolling.compute_score()

    assert r.score == pytest.approx(c.score)
    assert r.time_normal == pytest.approx(c.time_normal)
    assert r.time_slumping == pytest.approx(c.time_slumping)
    assert r.time_head_drop == pytest.approx(c.time_head_drop)


# ----------------------------------------------------------------------
# Xu ly khoang trong (seat mat du lieu tam thoi -- hoc sinh roi cho/bi che khuat)
# ----------------------------------------------------------------------


def test_gap_larger_than_max_gap_excluded_from_score():
    """Khoang trong LON (vuot max_gap_sec) khong duoc gan cho bat ky trang
    thai nao -- loai hoan toan khoi tu va mau so, khong bi tinh nham la
    binh thuong hay bat ky trang thai nao khac."""
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=1000.0, max_gap_sec=30.0)

    tracker.update(0.0, False, False)
    tracker.update(10.0, False, False)  # 10s binh thuong

    # Khoang trong 200s (hoc sinh roi cho) -- vuot xa max_gap_sec=30
    tracker.update(210.0, True, False)  # xuat hien lai, dang cui dau

    result = tracker.compute_score()

    # Chi co 10s binh thuong duoc tinh -- khoang trong 200s KHONG duoc gan
    # cho head_drop (dung ra neu tinh nham se la 200s head_drop!)
    assert result.time_normal == pytest.approx(10.0)
    assert result.time_head_drop == pytest.approx(0.0)
    assert result.time_total == pytest.approx(10.0)


def test_gap_smaller_than_max_gap_still_counted_normally():
    """Khoang cach BINH THUONG (duoi max_gap_sec) van duoc tinh vao trang
    thai nhu binh thuong, khong bi loai bo oan uong."""
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=1000.0, max_gap_sec=30.0)

    tracker.update(0.0, False, False)
    tracker.update(20.0, True, False)  # khoang cach 20s < max_gap_sec=30 -- van tinh binh thuong

    result = tracker.compute_score()

    assert result.time_head_drop == pytest.approx(20.0)
    assert result.time_total == pytest.approx(20.0)


def test_multiple_gaps_only_large_ones_excluded():
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=1000.0, max_gap_sec=30.0)

    tracker.update(0.0, False, False)
    tracker.update(10.0, False, False)      # +10s normal (gap 10s, binh thuong)
    tracker.update(200.0, True, False)      # gap 190s -- qua lon, loai bo
    tracker.update(210.0, True, False)      # +10s head_drop (gap 10s, binh thuong)

    result = tracker.compute_score()

    assert result.time_normal == pytest.approx(10.0)
    assert result.time_head_drop == pytest.approx(10.0)
    assert result.time_total == pytest.approx(20.0)  # KHONG bao gom 190s gap


# ----------------------------------------------------------------------
# Tan suat (count) duoc dem lai tu segment con trong window
# ----------------------------------------------------------------------


def test_count_only_reflects_episodes_within_window():
    """1 episode head_drop cu (ngoai window) + 1 episode moi (trong window)
    -- count chi duoc tinh cho episode con trong window, khong cong don ca
    episode da bi prune."""
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=50.0, max_gap_sec=1000.0)

    tracker.update(0.0, False, False)
    tracker.update(10.0, True, False)   # episode 1: head_drop (se bi prune sau)
    tracker.update(20.0, False, False)  # het episode 1
    tracker.update(80.0, False, False)  # troi qua nhieu thoi gian -- episode 1 gio ngoai window (cutoff=80-50=30)
    tracker.update(90.0, True, False)   # episode 2: head_drop moi, con trong window

    result = tracker.compute_score()

    assert result.head_drop_count == 1  # chi con episode 2 trong window
    assert result.time_head_drop == pytest.approx(10.0)  # chi tinh phan cua episode 2


# ----------------------------------------------------------------------
# reset()
# ----------------------------------------------------------------------


def test_reset_clears_all_segments():
    tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=100.0, max_gap_sec=1000.0)
    run_sequence(tracker, [(50.0, True, False)])
    assert tracker.compute_score().time_total > 0

    tracker.reset()

    result = tracker.compute_score()
    assert result.time_total == 0.0
    assert result.score is None


def test_no_data_yet_returns_none_score():
    tracker = RollingSeatEngagementTracker(seat_id="A1")
    result = tracker.compute_score()
    assert result.score is None
    assert result.time_total == 0.0