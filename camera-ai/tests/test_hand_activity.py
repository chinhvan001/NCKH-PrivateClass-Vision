"""
test_hand_activity.py -- Unit test cho HandActivityMonitor
(src/engagement/hand_activity.py)
"""

from src.engagement.hand_activity import HandActivityMonitor


class FakePerson:
    """Gia lap toi thieu 1 PersonPose -- chi can .get_keypoint(name)."""

    def __init__(self, keypoints: dict):
        self._kp = keypoints

    def get_keypoint(self, name):
        return self._kp.get(name)


def make_person(wrist_x, wrist_y, left_shoulder, right_shoulder, wrist_conf=0.9):
    return FakePerson(
        {
            "left_wrist": (wrist_x, wrist_y, wrist_conf),
            "right_wrist": (wrist_x + 30, wrist_y, wrist_conf),
            "left_shoulder": left_shoulder,
            "right_shoulder": right_shoulder,
        }
    )


DEFAULT_SHOULDERS = ((60.0, 100.0, 0.9), (140.0, 100.0, 0.9))  # do rong 80px


def test_returns_none_before_enough_samples():
    monitor = HandActivityMonitor(min_samples=3)
    result = monitor.update(0.0, make_person(50, 150, *DEFAULT_SHOULDERS))
    assert result is None


def test_still_hands_return_false():
    monitor = HandActivityMonitor(min_samples=3, movement_threshold_ratio=0.15)
    result = None
    for t in [0.0, 1.0, 2.0, 3.0]:
        result = monitor.update(t, make_person(50, 150, *DEFAULT_SHOULDERS))  # vi tri co dinh
    assert result is False


def test_active_hands_return_true():
    monitor = HandActivityMonitor(min_samples=3, movement_threshold_ratio=0.15)
    result = None
    for t, wx in zip([0.0, 1.0, 2.0, 3.0], [50, 90, 50, 90]):
        result = monitor.update(t, make_person(wx, 150, *DEFAULT_SHOULDERS))
    assert result is True


def test_normalized_by_shoulder_width_regardless_of_camera_distance():
    """Nguoi gan camera (vai rong) va nguoi xa camera (vai hep) voi CUNG ty
    le dao dong hinh hoc phai cho ra CUNG mot ket qua -- day la muc dich
    chinh cua viec chuan hoa theo shoulder_width."""
    monitor_close = HandActivityMonitor(min_samples=3, movement_threshold_ratio=0.15)
    close_shoulders = ((60.0, 100.0, 0.9), (140.0, 100.0, 0.9))  # rong 80px
    result_close = None
    for t, wx in zip([0.0, 1.0, 2.0, 3.0], [50, 90, 50, 90]):  # dao dong 40px
        result_close = monitor_close.update(t, make_person(wx, 150, *close_shoulders))

    monitor_far = HandActivityMonitor(min_samples=3, movement_threshold_ratio=0.15)
    far_shoulders = ((80.0, 100.0, 0.9), (120.0, 100.0, 0.9))  # rong 40px (bang 1/2)
    result_far = None
    for t, wx in zip([0.0, 1.0, 2.0, 3.0], [50, 70, 50, 70]):  # dao dong 20px (bang 1/2 -- cung ty le)
        result_far = monitor_far.update(t, make_person(wx, 150, *far_shoulders))

    assert result_close is True and result_far is True


def test_occluded_wrists_return_none():
    monitor = HandActivityMonitor(min_samples=3)
    result = None
    for t in [0.0, 1.0, 2.0, 3.0]:
        person = FakePerson(
            {
                "left_wrist": None,
                "right_wrist": None,
                "left_shoulder": DEFAULT_SHOULDERS[0],
                "right_shoulder": DEFAULT_SHOULDERS[1],
            }
        )
        result = monitor.update(t, person)
    assert result is None


def test_missing_shoulder_prevents_sample_from_being_added():
    """Khong co shoulder (can de chuan hoa) -- khong them duoc mau, ke ca
    khi wrist phat hien tot."""
    monitor = HandActivityMonitor(min_samples=3)
    result = None
    for t in [0.0, 1.0, 2.0]:
        person = FakePerson(
            {
                "left_wrist": (50.0, 150.0, 0.9),
                "right_wrist": (150.0, 150.0, 0.9),
                "left_shoulder": None,
                "right_shoulder": None,
            }
        )
        result = monitor.update(t, person)
    assert result is None


def test_low_confidence_wrist_treated_as_missing():
    monitor = HandActivityMonitor(min_samples=3)
    result = None
    for t in [0.0, 1.0, 2.0]:
        result = monitor.update(t, make_person(50, 150, *DEFAULT_SHOULDERS, wrist_conf=0.05))
    assert result is None


def test_old_samples_pruned_outside_window():
    """Cua so nho -- mau cu phai bi loai, chi con mau gan day anh huong ket qua."""
    monitor = HandActivityMonitor(window_sec=2.0, min_samples=3, movement_threshold_ratio=0.15)

    # 3 mau dau dao dong manh (se bi prune sau)
    for t, wx in zip([0.0, 0.5, 1.0], [50, 90, 50]):
        monitor.update(t, make_person(wx, 150, *DEFAULT_SHOULDERS))

    # 3 mau sau, TINH, du de vuot cutoff (t - 2.0) va thay the hoan toan cac mau dao dong cu
    result = None
    for t in [5.0, 5.5, 6.0]:
        result = monitor.update(t, make_person(70, 150, *DEFAULT_SHOULDERS))  # vi tri co dinh

    assert result is False, "Mau dao dong cu phai da bi loai khoi cua so, chi con mau tinh gan day"


def test_reset_clears_samples():
    monitor = HandActivityMonitor(min_samples=3)
    for t in [0.0, 1.0, 2.0]:
        monitor.update(t, make_person(50, 150, *DEFAULT_SHOULDERS))

    monitor.reset()

    # Ngay sau reset, chi co 1 mau -- chua du min_samples
    result = monitor.update(10.0, make_person(50, 150, *DEFAULT_SHOULDERS))
    assert result is None
