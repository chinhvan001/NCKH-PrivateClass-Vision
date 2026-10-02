"""Pipeline headless, co the test duoc voi video va pose provider gia lap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol

from src.capture import CameraCapture, CaptureConfig
from src.detection.pose_detector import PersonPose
from src.engagement.engagement_score import SeatEngagementTracker, classify_posture_state
from src.engagement.hand_activity import HandActivityMonitor
from src.engagement.posture import compute_head_drop_ratio, compute_torso_vector_angle
from src.engagement.posture_monitor import BaselineEstablisher, PostureMonitor, PostureThresholds, RollingSmoother
from src.privacy import AnonymizedEngagementRecord, anonymize_engagement, dispose_frame
from src.seating.seat_grid import SeatGrid
from src.seating.seat_tracker import SeatTracker


class PoseProvider(Protocol):
    """Diem thay the inference trong test; production co the dung PoseDetector."""

    def detect(self, image_bgr) -> List[PersonPose]: ...


@dataclass
class _SeatPipelineState:
    tracker: SeatEngagementTracker
    baseline: BaselineEstablisher
    monitor: PostureMonitor
    hands: HandActivityMonitor
    head_smoother: RollingSmoother
    deviation_smoother: RollingSmoother


@dataclass(frozen=True)
class SeatObservation:
    """Ket qua cua 1 seat trong 1 frame.

    ``person`` (keypoint/bbox) va ``head_drop_ratio`` chi dung NOI BO (vd ve
    preview da an danh trong demo); chi ``record`` duoc phep roi pipeline.
    """

    seat_id: str
    person: PersonPose
    head_drop_ratio: Optional[float]  # da lam muot
    record: AnonymizedEngagementRecord


class EngagementEngine:
    """Logic engagement theo tung frame, dung chung boi ``run_pipeline`` va demo.

    Seat duoc gan bang ``SeatTracker`` (giu seat_id on dinh qua jitter/che
    khuat ngan); chi seat thay nguoi o CHINH frame nay moi duoc cap nhat
    posture. Tin hieu head-drop va do lech than duoc lam muot theo
    ``smoothing_window_sec`` truoc khi so nguong, de 1 frame keypoint nhieu
    khong lam reset dem thoi gian sustained.
    """

    def __init__(
        self,
        seat_grid: SeatGrid,
        *,
        max_seat_distance: float | None = None,
        calibration_duration_sec: float = 5.0,
        posture_thresholds: PostureThresholds | None = None,
        smoothing_window_sec: float = 3.0,
    ) -> None:
        if calibration_duration_sec < 0:
            raise ValueError("calibration_duration_sec phai >= 0.")
        if smoothing_window_sec < 0:
            raise ValueError("smoothing_window_sec phai >= 0.")
        self._calibration_duration_sec = calibration_duration_sec
        self._thresholds = posture_thresholds or PostureThresholds()
        self._smoothing_window_sec = smoothing_window_sec
        self._seat_tracker = SeatTracker(seat_grid, max_distance=max_seat_distance)
        self._states: Dict[str, _SeatPipelineState] = {}

    def process(self, timestamp: float, poses: List[PersonPose]) -> List[SeatObservation]:
        """Cap nhat trang thai voi pose cua 1 frame, tra ve 1 observation cho
        moi seat thay nguoi o frame nay."""
        self._seat_tracker.update(poses)
        observations = []
        for assignment in self._seat_tracker.fresh_assignments.values():
            state = self._state_for(assignment.seat_id)
            head_signal = state.head_smoother.add(timestamp, compute_head_drop_ratio(assignment.person))
            torso_angle = compute_torso_vector_angle(assignment.person)
            state.baseline.add_sample(timestamp, torso_angle)
            deviation = state.deviation_smoother.add(
                timestamp,
                (
                    torso_angle - state.baseline.baseline_angle
                    if state.baseline.is_ready and torso_angle is not None
                    else None
                ),
            )
            head_event, slump_event = state.monitor.update(timestamp, head_signal, deviation)
            # Cap nhat moi frame (khong chi khi cui dau) de cua so bien thien co tay
            # da du mau ngay khi head_event bat dau.
            hand_activity = state.hands.update(timestamp, assignment.person)
            state.tracker.update(timestamp, head_event, slump_event, hand_activity)
            posture_state = classify_posture_state(head_event, slump_event, hand_activity)
            record = anonymize_engagement(state.tracker.compute_score(), timestamp, posture_state)
            observations.append(SeatObservation(assignment.seat_id, assignment.person, head_signal, record))
        return observations

    def _state_for(self, seat_id: str) -> _SeatPipelineState:
        if seat_id not in self._states:
            self._states[seat_id] = _SeatPipelineState(
                tracker=SeatEngagementTracker(seat_id),
                baseline=BaselineEstablisher(self._calibration_duration_sec),
                monitor=PostureMonitor(self._thresholds),
                hands=HandActivityMonitor(),
                head_smoother=RollingSmoother(self._smoothing_window_sec),
                deviation_smoother=RollingSmoother(self._smoothing_window_sec),
            )
        return self._states[seat_id]


@dataclass(frozen=True)
class PipelineRunResult:
    frames_processed: int
    records_emitted: int


def run_pipeline(
    capture_config: CaptureConfig,
    pose_provider: PoseProvider,
    seat_grid: SeatGrid,
    *,
    on_record: Callable[[AnonymizedEngagementRecord], None],
    max_frames: int | None = None,
    max_seat_distance: float | None = None,
    calibration_duration_sec: float = 5.0,
    posture_thresholds: PostureThresholds | None = None,
    smoothing_window_sec: float = 3.0,
) -> PipelineRunResult:
    """Chay pipeline khong GUI; moi record engagement an danh duoc day ngay vao
    ``on_record`` (sink: ghi JSONL, day len Firestore, ...) va KHONG giu lai
    trong RAM -- session dai khong lam bo nho tang theo so frame. Sink chay
    dong bo trong vong lap frame nen phai nhanh; sink nem exception se dung
    pipeline (frame hien tai van duoc dispose). Logic engagement: xem
    ``EngagementEngine``.

    Frame chi ton tai trong RAM cho den khi ``pose_provider.detect`` hoan tat;
    no duoc dispose trong ``finally``. ``timestamp`` duoc suy ra tu frame index
    va target FPS de test video co ket qua lap lai, khong phu thuoc toc do CI.
    """
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames phai >= 1 hoac None.")
    engine = EngagementEngine(
        seat_grid,
        max_seat_distance=max_seat_distance,
        calibration_duration_sec=calibration_duration_sec,
        posture_thresholds=posture_thresholds,
        smoothing_window_sec=smoothing_window_sec,
    )
    records_emitted = 0
    frames_processed = 0

    with CameraCapture(capture_config) as capture:
        for frame in capture.frames():
            try:
                timestamp = frame.frame_index / capture_config.target_fps
                poses = pose_provider.detect(frame.image)
                for observation in engine.process(timestamp, poses):
                    on_record(observation.record)
                    records_emitted += 1
            finally:
                dispose_frame(frame)
            frames_processed += 1
            if max_frames is not None and frames_processed >= max_frames:
                break
    return PipelineRunResult(frames_processed=frames_processed, records_emitted=records_emitted)
