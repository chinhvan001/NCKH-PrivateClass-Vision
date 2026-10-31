"""Unit test cho canh bao mat khong huong camera/nghi quay lung."""

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.back_turn import BackTurnDetector


def make_person(face_confidence: float, shoulder_confidence: float = 0.9) -> PersonPose:
    keypoints = [(0.0, 0.0, 0.0)] * 17
    values = {
        "nose": (100.0, 55.0, face_confidence),
        "left_eye": (95.0, 50.0, face_confidence),
        "right_eye": (105.0, 50.0, face_confidence),
        "left_shoulder": (80.0, 100.0, shoulder_confidence),
        "right_shoulder": (120.0, 100.0, shoulder_confidence),
    }
    for name, value in values.items():
        keypoints[COCO_KEYPOINT_NAMES.index(name)] = value
    return PersonPose(keypoints=keypoints, bbox=(70, 30, 130, 180), confidence=0.9)


def test_alerts_when_face_is_hidden_but_shoulders_remain_visible():
    detector = BackTurnDetector(max_face_visibility=0.2, min_duration_sec=2.0)
    people = {"A1": make_person(0.05)}
    assert detector.update(0.0, people) == []
    events = detector.update(2.0, people)
    assert len(events) == 1
    assert events[0].seat_id == "A1"
    assert events[0].face_visibility == pytest.approx(0.05)


def test_does_not_alert_for_clear_face_or_hidden_shoulders():
    detector = BackTurnDetector(max_face_visibility=0.2, min_duration_sec=1.0)
    assert detector.update(0.0, {"A1": make_person(0.9)}) == []
    assert detector.update(2.0, {"A1": make_person(0.05, shoulder_confidence=0.1)}) == []
