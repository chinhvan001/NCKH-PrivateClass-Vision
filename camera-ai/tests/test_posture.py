"""
test_posture.py -- Unit test cho posture.py (src/engagement/posture.py)

Chien luoc kiem thu: giong cach da lam voi head_pose.py -- dung toa do BIET
TRUOC (khong phai model that), tinh ket qua ky vong bang tay/cong thuc doc
lap, roi so sanh voi ket qua ham tra ve.
"""

import math

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.posture import (
    MIN_SHOULDER_WIDTH_PIXELS,
    compute_head_drop_ratio,
    compute_shoulder_tilt,
    compute_torso_deviation,
    compute_torso_vector_angle,
)


def make_person(keypoint_overrides: dict, default_conf=0.9) -> PersonPose:
    """Tao PersonPose gia lap, mac dinh moi keypoint o (0,0,0.9) tru khi
    duoc ghi de qua keypoint_overrides (dict ten -> (x, y, conf))."""
    keypoints = [(0.0, 0.0, default_conf)] * 17
    for name, value in keypoint_overrides.items():
        idx = COCO_KEYPOINT_NAMES.index(name)
        keypoints[idx] = value
    return PersonPose(keypoints=keypoints, bbox=(0, 0, 100, 100), confidence=0.9)


# ----------------------------------------------------------------------
# compute_head_drop_ratio
# ----------------------------------------------------------------------


def test_head_drop_ratio_upright_posture():
    """Ngoi thang: mui cao hon duong vai ro ret. Vai rong 40px, mui cach
    duong vai 60px ve phia tren -> ty le ky vong = 60/40 = 1.5"""
    person = make_person({
        "nose": (100.0, 40.0, 0.9),
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    ratio = compute_head_drop_ratio(person)
    assert ratio == pytest.approx(1.5)


def test_head_drop_ratio_nose_exactly_at_shoulder_line():
    """Mui NGANG BANG duong vai (cui rat thap) -> ty le ky vong = 0."""
    person = make_person({
        "nose": (100.0, 100.0, 0.9),
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    ratio = compute_head_drop_ratio(person)
    assert ratio == pytest.approx(0.0)


def test_head_drop_ratio_nose_below_shoulder_line_is_negative():
    person = make_person({
        "nose": (100.0, 120.0, 0.9),  # mui THAP hon duong vai (y lon hon)
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    ratio = compute_head_drop_ratio(person)
    assert ratio == pytest.approx(-0.5)  # (100-120)/40 = -0.5


def test_head_drop_ratio_scale_invariant_with_distance_from_camera():
    """Nguoi o GAN camera (vai rong 80px) va nguoi o XA camera (vai rong
    40px), CUNG mot ty le hinh hoc (cui dau tuong duong) phai cho RA CUNG
    MOT ty le sau chuan hoa -- day la muc dich chinh cua viec chuan hoa
    theo shoulder width."""
    person_close = make_person({
        "nose": (100.0, 20.0, 0.9),
        "left_shoulder": (60.0, 100.0, 0.9),
        "right_shoulder": (140.0, 100.0, 0.9),  # vai rong 80px, mui cach vai 80px
    })
    person_far = make_person({
        "nose": (100.0, 60.0, 0.9),
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),  # vai rong 40px, mui cach vai 40px
    })
    ratio_close = compute_head_drop_ratio(person_close)
    ratio_far = compute_head_drop_ratio(person_far)
    assert ratio_close == pytest.approx(ratio_far)
    assert ratio_close == pytest.approx(1.0)


def test_head_drop_ratio_missing_nose_returns_none():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    # nose mac dinh la (0,0,0.9) -- van "co" nhung khong dai dien cho test nay,
    # nen test rieng truong hop confidence thap thay vi "thieu" hoan toan:
    person_low_conf = make_person({
        "nose": (100.0, 40.0, 0.05),
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    assert compute_head_drop_ratio(person_low_conf) is None


def test_head_drop_ratio_zero_shoulder_width_returns_none():
    person = make_person({
        "nose": (100.0, 40.0, 0.9),
        "left_shoulder": (100.0, 100.0, 0.9),
        "right_shoulder": (100.0, 100.0, 0.9),  # trung voi left -> width = 0
    })
    assert compute_head_drop_ratio(person) is None


def test_head_drop_ratio_tiny_shoulder_width_below_threshold_returns_none():
    quarter = MIN_SHOULDER_WIDTH_PIXELS / 4  # tong khoang cach 2 vai = MIN_SHOULDER_WIDTH_PIXELS/2
    person = make_person({
        "nose": (100.0, 40.0, 0.9),
        "left_shoulder": (100.0 - quarter, 100.0, 0.9),
        "right_shoulder": (100.0 + quarter, 100.0, 0.9),
    })
    assert compute_head_drop_ratio(person) is None


# ----------------------------------------------------------------------
# compute_torso_vector_angle / compute_torso_deviation
# ----------------------------------------------------------------------


def test_torso_angle_perfectly_upright_is_zero():
    """Vai va hong thang hang theo truc doc (cung x) -> goc = 0."""
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
        "left_hip": (80.0, 200.0, 0.9),
        "right_hip": (120.0, 200.0, 0.9),
    })
    angle = compute_torso_vector_angle(person)
    assert angle == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("dx,dy,expected_deg", [
    (0.0, 100.0, 0.0),      # thang dung hoan toan
    (100.0, 100.0, 45.0),   # nghieng 45 do (dx=dy)
    (-100.0, 100.0, -45.0), # nghieng 45 do huong nguoc lai
    (57.735, 100.0, 30.0),  # nghieng 30 do (tan(30)=0.5774)
])
def test_torso_angle_known_values(dx, dy, expected_deg):
    """Round-trip: dung do lech (dx, dy) bang tay tu goc mong muon, kiem tra
    ham tra ve dung goc do."""
    shoulder_mid = (100.0, 100.0)
    hip_mid = (shoulder_mid[0] + dx, shoulder_mid[1] + dy)

    person = make_person({
        "left_shoulder": (shoulder_mid[0] - 20, shoulder_mid[1], 0.9),
        "right_shoulder": (shoulder_mid[0] + 20, shoulder_mid[1], 0.9),
        "left_hip": (hip_mid[0] - 20, hip_mid[1], 0.9),
        "right_hip": (hip_mid[0] + 20, hip_mid[1], 0.9),
    })

    angle = compute_torso_vector_angle(person)
    assert angle == pytest.approx(expected_deg, abs=0.01)


def test_torso_angle_missing_hip_returns_none():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
        "left_hip": (80.0, 200.0, 0.05),  # confidence thap -- mo phong hip bi che khuat
        "right_hip": (120.0, 200.0, 0.05),
    })
    assert compute_torso_vector_angle(person) is None


def test_torso_deviation_matches_difference_from_baseline():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
        "left_hip": (100.0, 200.0, 0.9),
        "right_hip": (140.0, 200.0, 0.9),  # tao ra 1 goc nghieng nhat dinh, khac 0
    })
    current_angle = compute_torso_vector_angle(person)
    baseline = current_angle - 10.0  # gia dinh baseline lech 10 do so voi hien tai

    deviation = compute_torso_deviation(person, baseline)

    assert deviation == pytest.approx(10.0)


def test_torso_deviation_none_when_angle_not_computable():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.05),
        "right_shoulder": (120.0, 100.0, 0.05),
        "left_hip": (80.0, 200.0, 0.9),
        "right_hip": (120.0, 200.0, 0.9),
    })
    assert compute_torso_deviation(person, baseline_angle=0.0) is None


# ----------------------------------------------------------------------
# compute_shoulder_tilt (tin hieu du phong, khong can hip)
# ----------------------------------------------------------------------


def test_shoulder_tilt_level_shoulders_is_zero():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    tilt = compute_shoulder_tilt(person)
    assert tilt == pytest.approx(0.0, abs=1e-6)


def test_shoulder_tilt_known_angle():
    """Vai phai thap hon vai trai 40px, cach nhau 40px theo truc X
    -> goc nghieng ky vong = atan2(40, 40) = 45 do."""
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 140.0, 0.9),
    })
    tilt = compute_shoulder_tilt(person)
    assert tilt == pytest.approx(45.0, abs=0.01)


def test_shoulder_tilt_does_not_need_hip_keypoints():
    """Xac nhan tin hieu du phong nay tinh duoc ke ca khi hip hoan toan
    khong dang tin cay (mo phong dung boi canh lop hoc thuc te)."""
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.9),
        "right_shoulder": (120.0, 100.0, 0.9),
        "left_hip": (0.0, 0.0, 0.0),
        "right_hip": (0.0, 0.0, 0.0),
    })
    assert compute_shoulder_tilt(person) is not None
    assert compute_torso_vector_angle(person) is None  # doi chieu: tin hieu chinh PHAI that bai


def test_shoulder_tilt_missing_shoulder_returns_none():
    person = make_person({
        "left_shoulder": (80.0, 100.0, 0.02),
        "right_shoulder": (120.0, 100.0, 0.9),
    })
    assert compute_shoulder_tilt(person) is None