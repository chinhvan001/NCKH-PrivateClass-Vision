"""Integration: video gia lap -> capture -> pose -> seating -> engagement.

Khong nap YOLO trong CI. PoseProvider deterministic giu test nhanh/khong phu
thuoc GPU, nhung van di qua CameraCapture, hinh hoc pose, seat mapper, monitor,
tracker va schema export an danh thuc te.
"""

import json

import cv2
import numpy as np

from src.capture import CaptureConfig
from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.posture_monitor import PostureThresholds
from src.pipeline import run_pipeline
from src.seating.seat_grid import Seat, SeatGrid


def _person(center_x: float, head_drop: bool, wrist_dx: float | None = None) -> PersonPose:
    """wrist_dx=None: khong co wrist (hand_activity=None). Nguoc lai 2 co tay
    nam tren ban, lech ngang wrist_dx so voi vi tri goc."""
    points = [(0.0, 0.0, 0.0)] * 17
    values = {
        "nose": (center_x, 96.0 if head_drop else 50.0, 0.95),
        "left_shoulder": (center_x - 20.0, 100.0, 0.95),
        "right_shoulder": (center_x + 20.0, 100.0, 0.95),
        "left_hip": (center_x - 20.0, 160.0, 0.95),
        "right_hip": (center_x + 20.0, 160.0, 0.95),
    }
    if wrist_dx is not None:
        values["left_wrist"] = (center_x - 15.0 + wrist_dx, 130.0, 0.95)
        values["right_wrist"] = (center_x + 15.0 + wrist_dx, 130.0, 0.95)
    for name, point in values.items():
        points[COCO_KEYPOINT_NAMES.index(name)] = point
    return PersonPose(points, (center_x - 35.0, 40.0, center_x + 35.0, 180.0), 0.9)


class ReplayPoseProvider:
    """Doc byte dau frame de replay chuoi pose, dong thoi xac nhan capture that su cap frame."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        self.calls += 1
        assert image_bgr.shape == (240, 320, 3)
        # Frame 1-2 ngoi thang, 3-8 cui dau: vuot sustained threshold 1 giay.
        return [_person(90.0, self.calls >= 3), _person(230.0, False)]


class HeadDownReplayProvider:
    """Ca 2 seat cui dau tu frame 3. A1: tay tinh (ngu gat). A2: tay di chuyen
    qua lai 20px moi frame (chep bai) -- 20px = 50% do rong vai, vuot nguong 15%."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        self.calls += 1
        head_drop = self.calls >= 3
        writing_dx = 20.0 if self.calls % 2 else -20.0
        return [_person(90.0, head_drop, wrist_dx=0.0), _person(230.0, head_drop, wrist_dx=writing_dx)]


def _video(path):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 2.0, (320, 240))
    assert writer.isOpened()
    try:
        for index in range(8):
            writer.write(np.full((240, 320, 3), index, dtype=np.uint8))
    finally:
        writer.release()


def test_full_pipeline_from_simulated_video_to_anonymized_engagement(tmp_path):
    video = tmp_path / "pipeline.mp4"
    _video(video)
    provider = ReplayPoseProvider()
    grid = SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)])

    result = run_pipeline(
        CaptureConfig(source=str(video), target_fps=2.0),
        provider,
        grid,
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
    )

    assert result.frames_processed == 8
    assert provider.calls == 8
    assert len(result.records) == 16
    by_seat = {seat_id: [record for record in result.records if record.seat_id == seat_id] for seat_id in ("A1", "A2")}
    assert by_seat["A1"][-1].engagement_score < by_seat["A2"][-1].engagement_score
    assert by_seat["A1"][-1].slumping_events >= 1
    allowed = {"seat_id", "observed_at_sec", "engagement_score", "posture_state", "head_drop_events", "slumping_events"}
    assert all(set(record.to_dict()) == allowed for record in result.records)
    assert all("image" not in json.dumps(record.to_dict()) for record in result.records)


def test_head_down_with_still_hands_is_head_drop_but_writing_is_normal(tmp_path):
    video = tmp_path / "head_down.mp4"
    _video(video)

    result = run_pipeline(
        CaptureConfig(source=str(video), target_fps=2.0),
        HeadDownReplayProvider(),
        SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)]),
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
    )

    still = [record for record in result.records if record.seat_id == "A1"]
    writing = [record for record in result.records if record.seat_id == "A2"]
    # Cui dau tu t=1.0s, vuot sustained 1s tai t=2.0s (frame 5).
    assert still[-1].posture_state == "head_drop"
    assert still[-1].head_drop_events == 1
    assert still[-1].slumping_events == 0
    assert still[-1].engagement_score < 100.0
    assert all(record.posture_state == "normal" for record in writing)
    assert writing[-1].head_drop_events == 0
    assert writing[-1].engagement_score == 100.0
