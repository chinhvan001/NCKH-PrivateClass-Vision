"""
test_camera_angle_signal.py -- Unit test cho compute_face_visibility_score()
va select_head_down_signal() (src/engagement/posture.py), phan bo sung
Head-Drop-Redesign.docx Giai phap 1 (13/09/2026).
"""

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.posture import (
    compute_face_visibility_score,
    compute_head_drop_ratio,
    select_head_down_signal,
)


def make_person(overrides: dict) -> PersonPose:
    keypoints = [(0.0, 0.0, 0.9)] * 17
    for name, value in overrides.items():
        keypoints[COCO_KEYPOINT_NAMES.index(name)] = value
    return PersonPose(keypoints=keypoints, bbox=(0, 0, 10, 10), confidence=0.9)


class _FakeFace:
    """Gia lap PersonPose chi voi get_keypoint(), de kiem soat chinh xac
    keypoint nao 'khong phat hien duoc' (None) thay vi chi confidence thap."""

    def __init__(self, values: dict):
        self._values = values

    def get_keypoint(self, name):
        return self._values.get(name)


# ----------------------------------------------------------------------
# compute_face_visibility_score
# ----------------------------------------------------------------------


def test_high_confidence_face_gives_high_visibility():
    person = make_person({"nose": (0, 0, 0.9), "left_eye": (0, 0, 0.85), "right_eye": (0, 0, 0.95)})
    result = compute_face_visibility_score(person)
    assert result == pytest.approx(0.9)


def test_low_confidence_face_gives_low_visibility():
    """Mo phong camera top-down: dau cui xuong -> mat quay ra xa ong kinh
    -> confidence cac keypoint mat thap, du van 'phat hien' duoc (khac voi
    hoan toan khong co)."""
    person = make_person({"nose": (0, 0, 0.1), "left_eye": (0, 0, 0.05), "right_eye": (0, 0, 0.15)})
    result = compute_face_visibility_score(person)
    assert result == pytest.approx(0.1)


def test_no_face_keypoints_detected_returns_none():
    person = _FakeFace({"nose": None, "left_eye": None, "right_eye": None})
    assert compute_face_visibility_score(person) is None


def test_partial_face_keypoints_still_computes_from_available_ones():
    """Chi 1/3 keypoint mat phat hien duoc -- van tinh duoc tu phan co,
    khong doi hoi phai co du ca 3."""
    person = _FakeFace({"nose": (0, 0, 0.6), "left_eye": None, "right_eye": None})
    result = compute_face_visibility_score(person)
    assert result == pytest.approx(0.6)


# ----------------------------------------------------------------------
# select_head_down_signal -- dispatch theo camera_angle_type
# ----------------------------------------------------------------------


def test_frontal_dispatches_to_head_drop_ratio():
    person = make_person(
        {
            "nose": (100.0, 40.0, 0.9),
            "left_shoulder": (80.0, 100.0, 0.9),
            "right_shoulder": (120.0, 100.0, 0.9),
        }
    )
    result = select_head_down_signal(person, "frontal")
    assert result == compute_head_drop_ratio(person)
    assert result == pytest.approx(1.5)


def test_top_down_dispatches_to_face_visibility():
    person = make_person(
        {
            "nose": (0, 0, 0.9),
            "left_eye": (0, 0, 0.7),
            "right_eye": (0, 0, 0.8),
        }
    )
    result = select_head_down_signal(person, "top_down")
    assert result == compute_face_visibility_score(person)
    assert result == pytest.approx(0.8)


def test_frontal_and_top_down_give_different_values_for_same_person():
    """Xac nhan 2 nhanh dispatch THUC SU goi 2 cong thuc khac nhau, khong
    vo tinh tra ve cung 1 gia tri (vi du do loi copy-paste)."""
    person = make_person(
        {
            "nose": (100.0, 40.0, 0.9),
            "left_shoulder": (80.0, 100.0, 0.9),
            "right_shoulder": (120.0, 100.0, 0.9),
            "left_eye": (0, 0, 0.7),
            "right_eye": (0, 0, 0.8),
        }
    )
    r_frontal = select_head_down_signal(person, "frontal")
    r_top_down = select_head_down_signal(person, "top_down")
    assert r_frontal != r_top_down


def test_invalid_camera_angle_type_raises_value_error():
    person = make_person({})
    with pytest.raises(ValueError, match="camera_angle_type"):
        select_head_down_signal(person, "sideways")  # type: ignore[arg-type]
