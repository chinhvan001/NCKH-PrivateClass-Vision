"""Integration: video gia lap -> capture -> pose -> seating -> engagement.

Khong nap YOLO trong CI. PoseProvider deterministic giu test nhanh/khong phu
thuoc GPU, nhung van di qua CameraCapture, hinh hoc pose, seat mapper, monitor,
tracker va schema export an danh thuc te.
"""

import json

import cv2
import numpy as np
import pytest

from src.capture import CaptureConfig
from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.engagement.posture_monitor import PostureThresholds
from src.pipeline import AlertManager, run_pipeline
from src.seating.seat_grid import Seat, SeatGrid


def _person(
    center_x: float,
    head_drop: bool,
    wrist_dx: float | None = None,
    nose_dx: float = 0.0,
    face_conf: float = 0.95,
) -> PersonPose:
    """wrist_dx=None: khong co wrist (hand_activity=None). Nguoc lai 2 co tay
    nam tren ban, lech ngang wrist_dx so voi vi tri goc. nose_dx: quay dau
    sang ngang; face_conf thap: mat khong huong camera."""
    points = [(0.0, 0.0, 0.0)] * 17
    values = {
        "nose": (center_x + nose_dx, 96.0 if head_drop else 50.0, face_conf),
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


def _collect(*args, **kwargs):
    """Chay pipeline voi sink la list -- chi hop le cho video test ngan."""
    records = []
    result = run_pipeline(*args, on_record=records.append, **kwargs)
    assert result.records_emitted == len(records)
    return result, records


def _video(path, frame_count: int = 8):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 2.0, (320, 240))
    assert writer.isOpened()
    try:
        for index in range(frame_count):
            writer.write(np.full((240, 320, 3), index, dtype=np.uint8))
    finally:
        writer.release()


def test_full_pipeline_from_simulated_video_to_anonymized_engagement(tmp_path):
    video = tmp_path / "pipeline.mp4"
    _video(video)
    provider = ReplayPoseProvider()
    grid = SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)])

    result, records = _collect(
        CaptureConfig(source=str(video), target_fps=2.0),
        provider,
        grid,
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=1.0,
    )

    assert result.frames_processed == 8
    assert provider.calls == 8
    assert len(records) == 16
    by_seat = {seat_id: [record for record in records if record.seat_id == seat_id] for seat_id in ("A1", "A2")}
    assert by_seat["A1"][-1].engagement_score < by_seat["A2"][-1].engagement_score
    assert by_seat["A1"][-1].slumping_events >= 1
    allowed = {"seat_id", "observed_at_sec", "engagement_score", "posture_state", "head_drop_events", "slumping_events"}
    assert all(set(record.to_dict()) == allowed for record in records)
    assert all("image" not in json.dumps(record.to_dict()) for record in records)


def test_head_down_with_still_hands_is_head_drop_but_writing_is_normal(tmp_path):
    video = tmp_path / "head_down.mp4"
    _video(video)

    result, records = _collect(
        CaptureConfig(source=str(video), target_fps=2.0),
        HeadDownReplayProvider(),
        SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)]),
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=1.0,
    )

    still = [record for record in records if record.seat_id == "A1"]
    writing = [record for record in records if record.seat_id == "A2"]
    # frame n co t=n/2s. Cui dau tu t=1.5s; trung binh 1s duoi nguong tu t=2.5s,
    # du sustained 1s tai t=3.5s (frame cuoi).
    assert still[-1].posture_state == "head_drop"
    assert still[-1].head_drop_events == 1
    assert still[-1].slumping_events == 0
    assert still[-1].engagement_score < 100.0
    assert all(record.posture_state == "normal" for record in writing)
    assert writing[-1].head_drop_events == 0
    assert writing[-1].engagement_score == 100.0


class GlitchReplayProvider:
    """1 seat cui dau tu frame 3, tay tinh; frame 11 (t=5.5s) keypoint nhieu
    tra ve tu the ngoi thang trong 1 frame duy nhat."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        self.calls += 1
        head_drop = self.calls >= 3 and self.calls != 11
        return [_person(90.0, head_drop, wrist_dx=0.0)]


def _run_glitch(tmp_path, smoothing_window_sec):
    video = tmp_path / f"glitch_{smoothing_window_sec}.mp4"
    _video(video, frame_count=15)
    result, records = _collect(
        CaptureConfig(source=str(video), target_fps=2.0),
        GlitchReplayProvider(),
        SeatGrid([Seat("A1", 90.0, 100.0)]),
        max_frames=15,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=smoothing_window_sec,
    )
    return records[-1]


def test_single_noisy_frame_does_not_split_head_drop_episode(tmp_path):
    # Khong lam muot: frame nhieu reset dem sustained -> bi tach thanh 2 episode.
    assert _run_glitch(tmp_path, smoothing_window_sec=0.0).head_drop_events == 2
    # Lam muot 3s (mac dinh): frame nhieu bi trung binh hoa -> van 1 episode.
    smoothed = _run_glitch(tmp_path, smoothing_window_sec=3.0)
    assert smoothed.head_drop_events == 1
    assert smoothed.posture_state == "head_drop"


class OccludedReplayProvider:
    """A1 chi duoc detect o frame le (frame chan bi che)."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        self.calls += 1
        return [_person(90.0, False, wrist_dx=0.0)] if self.calls % 2 else []


def test_occluded_frames_do_not_replay_last_pose(tmp_path):
    video = tmp_path / "occluded.mp4"
    _video(video)
    result, records = _collect(
        CaptureConfig(source=str(video), target_fps=2.0),
        OccludedReplayProvider(),
        SeatGrid([Seat("A1", 90.0, 100.0)]),
        max_frames=8,
        calibration_duration_sec=0.0,
    )
    # SeatTracker giu seat A1 qua frame bi che, nhung pipeline chi xu ly
    # quan sat moi: 4 frame le -> 4 record, khong phai 8.
    assert [record.observed_at_sec for record in records] == [0.5, 1.5, 2.5, 3.5]


def test_records_are_streamed_to_sink_during_run_not_buffered(tmp_path):
    video = tmp_path / "stream.mp4"
    _video(video)
    provider = ReplayPoseProvider()
    detect_calls_at_emit = []

    result = run_pipeline(
        CaptureConfig(source=str(video), target_fps=2.0),
        provider,
        SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)]),
        on_record=lambda record: detect_calls_at_emit.append(provider.calls),
        max_frames=8,
        calibration_duration_sec=0.0,
    )

    # Moi frame day 2 record (2 seat) NGAY sau khi detect frame do, truoc frame sau.
    assert detect_calls_at_emit == [call for call in range(1, 9) for _ in range(2)]
    assert result.records_emitted == 16
    assert not hasattr(result, "records")


class AlertScenarioProvider:
    """A1: cui dau + tay tinh tu frame 3. A2: vai ro nhung mat khong huong
    camera. A3/A4: quay mat ve nhau (cach 140px). Moi hanh vi duy tri nhieu frame."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        self.calls += 1
        return [
            _person(90.0, self.calls >= 3, wrist_dx=0.0),
            _person(230.0, False, face_conf=0.05),
            _person(370.0, False, nose_dx=10.0),
            _person(510.0, False, nose_dx=-10.0),
        ]


def _run_alert_scenario(tmp_path, camera_angle_type):
    video = tmp_path / f"alerts_{camera_angle_type}.mp4"
    _video(video)
    alerts = []
    result, _ = _collect(
        CaptureConfig(source=str(video), target_fps=2.0),
        AlertScenarioProvider(),
        SeatGrid(
            [Seat(seat_id, x, 100.0) for seat_id, x in (("A1", 90.0), ("A2", 230.0), ("A3", 370.0), ("A4", 510.0))]
        ),
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=1.0,
        camera_angle_type=camera_angle_type,
        alert_manager=AlertManager("sess_test", cooldown_sec=60.0),
        on_alert=alerts.append,
    )
    assert result.alerts_emitted == len(alerts)
    return sorted((a.seat_id, a.type, a.start_sec, a.duration_sec) for a in alerts)


def test_each_behaviour_alerts_once_per_episode_on_frontal_camera(tmp_path):
    # frame n co t=n/2s. back_turn (>=2s) tu t=0.5 -> alert t=2.5; side_conversation
    # (>=3s) tu t=0.5 -> alert t=3.5 cho CA 2 ghe; head_drop cui tu t=2.5 (sau lam muot),
    # du sustained 1s tai t=3.5. Hanh vi con keo dai nhung khong phat lai.
    assert _run_alert_scenario(tmp_path, "frontal") == [
        ("A1", "head_drop", 2.5, 1.0),
        ("A2", "back_turn", 0.5, 2.0),
        ("A3", "side_conversation", 0.5, 3.0),
        ("A4", "side_conversation", 0.5, 3.0),
    ]


def test_back_turn_is_disabled_for_top_down_camera(tmp_path):
    alerts = _run_alert_scenario(tmp_path, "top_down")
    assert [alert[1] for alert in alerts] == ["head_drop", "side_conversation", "side_conversation"]


def test_alert_sink_requires_alert_manager_and_valid_camera_angle(tmp_path):
    grid = SeatGrid([Seat("A1", 90.0, 100.0)])
    with pytest.raises(ValueError, match="cung nhau"):
        run_pipeline(CaptureConfig(source="unused"), None, grid, on_record=print, on_alert=print)
    with pytest.raises(ValueError, match="camera_angle_type"):
        run_pipeline(CaptureConfig(source="unused"), None, grid, on_record=print, camera_angle_type="side")
