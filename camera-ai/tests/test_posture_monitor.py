"""
test_posture_monitor.py -- Unit test cho posture_monitor.py

Trong tam: mo phong CHUOI DU LIEU THEO THOI GIAN (khong phai 1 mau don le),
bao gom ca truong hop FPS thap/khong deu (dung phat hien tu benchmark task
3.2) -- xac nhan nguong thoi gian tinh dung theo GIAY THUC, khong phai so
luong frame.
"""

import pytest

from src.engagement.posture_monitor import (
    BaselineEstablisher,
    PostureMonitor,
    PostureThresholds,
    RollingSmoother,
)


# ----------------------------------------------------------------------
# RollingSmoother
# ----------------------------------------------------------------------


def test_rolling_smoother_basic_average():
    smoother = RollingSmoother(window_sec=3.0)
    smoother.add(0.0, 10.0)
    smoother.add(1.0, 20.0)
    result = smoother.add(2.0, 30.0)
    assert result == pytest.approx(20.0)  # trung binh (10+20+30)/3


def test_rolling_smoother_drops_old_samples_outside_window():
    smoother = RollingSmoother(window_sec=3.0)
    smoother.add(0.0, 100.0)  # mau nay se bi loai khoi cua so sau do
    smoother.add(1.0, 10.0)
    result = smoother.add(5.0, 20.0)  # 5.0 - 3.0 = 2.0 -- mau tai t=0.0 va t=1.0 deu qua han
    assert result == pytest.approx(20.0)


def test_rolling_smoother_ignores_none_values():
    smoother = RollingSmoother(window_sec=3.0)
    smoother.add(0.0, 10.0)
    result = smoother.add(1.0, None)  # khong tinh duoc o frame nay -- bo qua, khong lam loang trung binh
    assert result == pytest.approx(10.0)


def test_rolling_smoother_returns_none_when_window_empty():
    smoother = RollingSmoother(window_sec=3.0)
    result = smoother.add(0.0, None)
    assert result is None


def test_rolling_smoother_handles_sparse_low_fps_timestamps():
    """Mo phong FPS rat thap (1-2 FPS, dung ket qua benchmark task 3.2) --
    khoang cach giua cac mau lon (0.5-1s), cua so 3s van phai hoat dong
    dung theo THOI GIAN, khong phai SO LUONG mau co dinh."""
    smoother = RollingSmoother(window_sec=3.0)
    smoother.add(0.0, 1.0)
    smoother.add(1.0, 2.0)
    smoother.add(2.0, 3.0)
    result = smoother.add(3.0, 4.0)
    # Ca 4 mau (t=0,1,2,3) deu trong cua so 3s tinh tu t=3.0 (cutoff=0.0, mau t=0.0 vua du dieu kien >= cutoff)
    assert result == pytest.approx(2.5)


# ----------------------------------------------------------------------
# BaselineEstablisher
# ----------------------------------------------------------------------


def test_baseline_establisher_computes_median_after_duration():
    establisher = BaselineEstablisher(calibration_duration_sec=5.0)
    establisher.add_sample(0.0, 10.0)
    establisher.add_sample(1.0, 12.0)
    establisher.add_sample(2.0, 11.0)
    assert establisher.is_ready is False

    establisher.add_sample(5.0, 13.0)  # vua du 5.0s -- chot baseline

    assert establisher.is_ready is True
    assert establisher.baseline_angle == pytest.approx(11.5)  # median([10,12,11,13])


def test_baseline_establisher_ignores_none_samples():
    establisher = BaselineEstablisher(calibration_duration_sec=3.0)
    establisher.add_sample(0.0, 10.0)
    establisher.add_sample(1.0, None)  # bi che khuat tam thoi trong luc calibrate
    establisher.add_sample(3.0, 10.0)
    assert establisher.baseline_angle == pytest.approx(10.0)


def test_baseline_establisher_fallback_zero_when_no_samples_at_all():
    establisher = BaselineEstablisher(calibration_duration_sec=2.0)
    establisher.add_sample(0.0, None)
    establisher.add_sample(2.0, None)  # het thoi gian calibration ma khong co mau nao
    assert establisher.is_ready is True
    assert establisher.baseline_angle == pytest.approx(0.0)


def test_baseline_establisher_locked_after_ready_ignores_further_samples():
    establisher = BaselineEstablisher(calibration_duration_sec=2.0)
    establisher.add_sample(0.0, 10.0)
    establisher.add_sample(2.0, 10.0)
    assert establisher.baseline_angle == pytest.approx(10.0)

    establisher.add_sample(3.0, 999.0)  # sau khi da chot -- khong duoc anh huong nua
    assert establisher.baseline_angle == pytest.approx(10.0)


# ----------------------------------------------------------------------
# PostureMonitor -- du lieu gia lap dang CHUOI theo thoi gian
# ----------------------------------------------------------------------


def test_normal_upright_sequence_never_triggers():
    """Chuoi mo phong NGOI THANG BINH THUONG suot 20 giay -- khong bao gio
    duoc tinh la head_drop hay slumping."""
    monitor = PostureMonitor()
    for t in range(0, 20):
        head_drop_event, slump_event = monitor.update(
            timestamp=float(t), head_drop_ratio=1.2, torso_deviation_deg=2.0
        )
        assert head_drop_event is False
        assert slump_event is False


def test_prolonged_head_drop_sequence_triggers_after_5s():
    """Chuoi mo phong CUI DAU KEO DAI: ngoi thang 2s dau, sau do cui dau lien
    tuc -- phai chi duoc bao la 'head drop event' SAU KHI da cui du 5 giay,
    KHONG PHAI ngay lap tuc khi vua cui."""
    thresholds = PostureThresholds(sustained_duration_sec=5.0)
    monitor = PostureMonitor(thresholds)

    # 2 giay dau: ngoi thang binh thuong
    for t in [0.0, 1.0, 2.0]:
        event, _ = monitor.update(t, head_drop_ratio=1.2, torso_deviation_deg=0.0)
        assert event is False

    # Bat dau cui dau tu t=2.5
    for t in [2.5, 3.5, 4.5, 5.5, 6.5]:  # chi moi duoc (6.5 - 2.5) = 4.0s -- CHUA du 5s
        event, _ = monitor.update(t, head_drop_ratio=0.1, torso_deviation_deg=0.0)
        assert event is False, f"Khong duoc trigger som tai t={t} (chi moi cui {t - 2.5:.1f}s)"

    # Tai t=7.6, da cui duoc (7.6 - 2.5) = 5.1s -- VUOT qua 5.0s -- PHAI trigger
    event, _ = monitor.update(7.6, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    assert event is True


def test_brief_recovery_resets_the_timer():
    """Cui dau 3s, ngoi thang lai 1 khung hinh (xac nhan RO RANG khong con
    cui), roi cui tiep 3s nua -- KHONG duoc cong don thanh 6s, vi da co 1
    lan xac nhan dieu kien SAI o giua -- phai reset ve dau."""
    monitor = PostureMonitor(PostureThresholds(sustained_duration_sec=5.0))

    monitor.update(0.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    event = monitor.update(3.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)[0]
    assert event is False  # moi 3s, chua du 5s

    # Ngoi thang lai ro rang tai t=3.5 -- xac nhan het cui
    monitor.update(3.5, head_drop_ratio=1.2, torso_deviation_deg=0.0)

    # Cui tiep tu t=4.0 -- neu KHONG bi reset, den t=6.0 se la (6.0-0.0)=6s > 5s
    # nhung vi da reset o t=3.5, thoi diem bat dau moi la t=4.0, nen t=6.0
    # moi chi (6.0-4.0)=2s -- CHUA du 5s.
    event = monitor.update(6.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)[0]
    assert event is False, "Khong duoc cong don qua lan xac nhan da het cui o giua"


def test_missing_data_does_not_reset_progress():
    """1-2 khung hinh KHONG tinh duoc head_drop_ratio (None, vi du confidence
    thap tam thoi) giua chuoi dang cui dau -- KHONG duoc reset tien trinh,
    khac voi truong hop xac nhan RO RANG da het cui (test tren)."""
    monitor = PostureMonitor(PostureThresholds(sustained_duration_sec=5.0))

    monitor.update(0.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    monitor.update(2.0, head_drop_ratio=None, torso_deviation_deg=None)  # mat du lieu tam thoi
    monitor.update(4.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    event = monitor.update(5.5, head_drop_ratio=0.1, torso_deviation_deg=0.0)[0]

    assert event is True, "Du lieu thieu tam thoi khong duoc lam reset tien trinh dang tich luy"


def test_slumping_detected_independently_of_head_drop():
    """Slumping va head_drop la 2 dieu kien doc lap -- chi slump, khong cui
    dau, van phai bao dung is_slumping_event=True va is_head_drop_event=False."""
    monitor = PostureMonitor(PostureThresholds(sustained_duration_sec=5.0, torso_deviation_threshold_deg=15.0))

    for t in [0.0, 2.0, 4.0]:
        head_event, slump_event = monitor.update(t, head_drop_ratio=1.2, torso_deviation_deg=20.0)
        assert head_event is False

    head_event, slump_event = monitor.update(5.5, head_drop_ratio=1.2, torso_deviation_deg=20.0)
    assert head_event is False
    assert slump_event is True


def test_low_and_irregular_fps_sequence_still_correct_in_wall_clock_time():
    """Mo phong FPS thap va KHONG DEU (1-2 FPS, dung ket qua benchmark task
    3.2) -- xac nhan nguong 5s van dung theo THOI GIAN THUC, du so luong
    frame it hon nhieu so voi gia dinh 15-30fps cua huong facial cu."""
    monitor = PostureMonitor(PostureThresholds(sustained_duration_sec=5.0))

    # Chi 6 frame trong 6 giay (~1 FPS, khoang cach khong deu) -- so luong
    # frame RAT IT so voi neu gia dinh 15fps (se la 75-90 frame cho 5-6s).
    timestamps = [0.0, 1.2, 2.5, 3.9, 4.8, 6.1]
    events = []
    for t in timestamps:
        event, _ = monitor.update(t, head_drop_ratio=0.1, torso_deviation_deg=0.0)
        events.append(event)

    # Tai t=4.8 (4.8s da troi qua) -- chua du 5s
    assert events[4] is False
    # Tai t=6.1 (6.1s da troi qua) -- vuot 5s -- du chi co 6 frame ca thay
    assert events[5] is True


def test_reset_clears_state():
    monitor = PostureMonitor(PostureThresholds(sustained_duration_sec=5.0))
    monitor.update(0.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    monitor.update(3.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)

    monitor.reset()

    # Sau reset, phai bat dau dem lai tu dau -- t=4.0 chi moi la lan dau tien
    event, _ = monitor.update(4.0, head_drop_ratio=0.1, torso_deviation_deg=0.0)
    assert event is False