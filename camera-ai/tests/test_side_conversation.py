"""Unit test cho canh bao tuong tac rieng theo cap ghe (khong dung danh tinh)."""

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.side_conversation import SideConversationDetector


def make_person(center_x: float, nose_offset: float) -> PersonPose:
    keypoints = [(0.0, 0.0, 0.0)] * 17
    values = {
        "left_shoulder": (center_x - 20, 100.0, 0.9),
        "right_shoulder": (center_x + 20, 100.0, 0.9),
        "nose": (center_x + nose_offset, 55.0, 0.9),
    }
    for name, value in values.items():
        keypoints[COCO_KEYPOINT_NAMES.index(name)] = value
    return PersonPose(keypoints=keypoints, bbox=(center_x - 30, 30, center_x + 30, 180), confidence=0.9)


def test_alert_after_pair_faces_each_other_for_required_duration():
    detector = SideConversationDetector(max_pair_distance=200, min_duration_sec=3.0)
    # A o ben trai quay phai, B o ben phai quay trai.
    people = {"A1": make_person(100, 10), "A2": make_person(200, -10)}

    assert detector.update(0.0, people) == []
    assert detector.update(2.9, people) == []
    events = detector.update(3.0, people)

    assert len(events) == 1
    assert events[0].first_seat_id == "A1"
    assert events[0].second_seat_id == "A2"
    assert events[0].duration_sec == 3.0


def test_no_alert_when_pair_faces_away_or_is_too_far():
    detector = SideConversationDetector(max_pair_distance=80, min_duration_sec=1.0)
    # Gan ve geometry nhung qua xa threshold; dong thoi A quay sang trai.
    people = {"A1": make_person(100, -10), "A2": make_person(200, -10)}
    assert detector.update(0.0, people) == []
    assert detector.update(3.0, people) == []


def test_short_missing_detection_does_not_reset_but_long_gap_does():
    detector = SideConversationDetector(max_pair_distance=200, min_duration_sec=3.0, max_gap_sec=0.75)
    people = {"A1": make_person(100, 10), "A2": make_person(200, -10)}
    detector.update(0.0, people)
    detector.update(1.0, people)
    detector.update(1.4, {})  # mat 0.4 giay: van cho phep
    detector.update(1.7, people)
    assert detector.update(3.1, people)  # > 3 giay tinh tu luc 0.0
    detector.update(4.0, {})
    assert detector.update(5.0, people) == []  # gap 1 giay: phai tich luy lai
