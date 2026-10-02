"""Pipeline headless, co the test duoc voi video va pose provider gia lap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from src.capture import CameraCapture, CaptureConfig
from src.detection.pose_detector import PersonPose
from src.engagement.engagement_score import SeatEngagementTracker, classify_posture_state
from src.engagement.hand_activity import HandActivityMonitor
from src.engagement.posture import compute_head_drop_ratio, compute_torso_vector_angle
from src.engagement.posture_monitor import BaselineEstablisher, PostureMonitor, PostureThresholds
from src.privacy import AnonymizedEngagementRecord, anonymize_engagement, dispose_frame
from src.seating.seat_grid import SeatGrid
from src.seating.seat_mapper import assign_seats


class PoseProvider(Protocol):
    """Diem thay the inference trong test; production co the dung PoseDetector."""

    def detect(self, image_bgr) -> List[PersonPose]: ...


@dataclass
class _SeatPipelineState:
    tracker: SeatEngagementTracker
    baseline: BaselineEstablisher
    monitor: PostureMonitor
    hands: HandActivityMonitor


@dataclass(frozen=True)
class PipelineRunResult:
    frames_processed: int
    records: List[AnonymizedEngagementRecord]


def run_pipeline(
    capture_config: CaptureConfig,
    pose_provider: PoseProvider,
    seat_grid: SeatGrid,
    *,
    max_frames: int | None = None,
    max_seat_distance: float | None = None,
    calibration_duration_sec: float = 5.0,
    posture_thresholds: PostureThresholds | None = None,
) -> PipelineRunResult:
    """Chay pipeline khong GUI va chi tra record engagement an danh.

    Frame chi ton tai trong RAM cho den khi ``pose_provider.detect`` hoan tat;
    no duoc dispose trong ``finally``. ``timestamp`` duoc suy ra tu frame index
    va target FPS de test video co ket qua lap lai, khong phu thuoc toc do CI.
    """
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames phai >= 1 hoac None.")
    if calibration_duration_sec < 0:
        raise ValueError("calibration_duration_sec phai >= 0.")
    states: Dict[str, _SeatPipelineState] = {}
    records: List[AnonymizedEngagementRecord] = []
    frames_processed = 0
    thresholds = posture_thresholds or PostureThresholds()

    with CameraCapture(capture_config) as capture:
        for frame in capture.frames():
            try:
                timestamp = frame.frame_index / capture_config.target_fps
                poses = pose_provider.detect(frame.image)
                assignments = assign_seats(poses, seat_grid, max_distance=max_seat_distance)
                for assignment in assignments:
                    state = states.setdefault(
                        assignment.seat_id,
                        _SeatPipelineState(
                            tracker=SeatEngagementTracker(assignment.seat_id),
                            baseline=BaselineEstablisher(calibration_duration_sec),
                            monitor=PostureMonitor(thresholds),
                            hands=HandActivityMonitor(),
                        ),
                    )
                    head_signal = compute_head_drop_ratio(assignment.person)
                    torso_angle = compute_torso_vector_angle(assignment.person)
                    state.baseline.add_sample(timestamp, torso_angle)
                    deviation = (
                        torso_angle - state.baseline.baseline_angle
                        if state.baseline.is_ready and torso_angle is not None
                        else None
                    )
                    head_event, slump_event = state.monitor.update(timestamp, head_signal, deviation)
                    # Cap nhat moi frame (khong chi khi cui dau) de cua so bien thien co tay
                    # da du mau ngay khi head_event bat dau.
                    hand_activity = state.hands.update(timestamp, assignment.person)
                    state.tracker.update(timestamp, head_event, slump_event, hand_activity)
                    posture_state = classify_posture_state(head_event, slump_event, hand_activity)
                    records.append(anonymize_engagement(state.tracker.compute_score(), timestamp, posture_state))
            finally:
                dispose_frame(frame)
            frames_processed += 1
            if max_frames is not None and frames_processed >= max_frames:
                break
    return PipelineRunResult(frames_processed=frames_processed, records=records)
