"""Pipeline headless, co the test duoc voi video va pose provider gia lap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol

from src.capture import CameraCapture, CaptureConfig
from src.detection.pose_detector import PersonPose
from src.engagement.back_turn import BackTurnDetector, BackTurnEvent
from src.engagement.engagement_score import SeatEngagementTracker, classify_posture_state
from src.engagement.hand_activity import HandActivityMonitor
from src.engagement.posture import CameraAngleType, compute_head_drop_ratio, compute_torso_vector_angle
from src.engagement.posture_monitor import BaselineEstablisher, PostureMonitor, PostureThresholds, RollingSmoother
from src.engagement.side_conversation import SideConversationDetector, SideConversationEvent
from src.pipeline.alert_manager import AlertCandidate, AlertManager
from src.privacy import AlertEvent, AnonymizedEngagementRecord, anonymize_engagement, dispose_frame
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


@dataclass(frozen=True)
class FrameResult:
    """Ket qua 1 frame. ``*_events`` dung de ve trong demo; ``alert_candidates``
    gom moi hanh vi dang duy tri (head_drop, back_turn, side_conversation) de
    dua vao ``AlertManager``."""

    observations: List[SeatObservation]
    back_turn_events: List[BackTurnEvent]
    side_conversation_events: List[SideConversationEvent]
    alert_candidates: List[AlertCandidate]


class EngagementEngine:
    """Logic engagement theo tung frame, dung chung boi ``run_pipeline`` va demo.

    Seat duoc gan bang ``SeatTracker`` (giu seat_id on dinh qua jitter/che
    khuat ngan); chi seat thay nguoi o CHINH frame nay moi duoc cap nhat
    posture. Tin hieu head-drop va do lech than duoc lam muot theo
    ``smoothing_window_sec`` truoc khi so nguong, de 1 frame keypoint nhieu
    khong lam reset dem thoi gian sustained.

    ``back_turn_detector``/``side_conversation_detector`` la tuy chon (None =
    tat); chi dua BackTurnDetector cho camera frontal.
    """

    def __init__(
        self,
        seat_grid: SeatGrid,
        *,
        max_seat_distance: float | None = None,
        calibration_duration_sec: float = 5.0,
        posture_thresholds: PostureThresholds | None = None,
        smoothing_window_sec: float = 3.0,
        back_turn_detector: BackTurnDetector | None = None,
        side_conversation_detector: SideConversationDetector | None = None,
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
        self._back_turn_detector = back_turn_detector
        self._side_conversation_detector = side_conversation_detector

    def process(self, timestamp: float, poses: List[PersonPose]) -> FrameResult:
        """Cap nhat trang thai voi pose cua 1 frame: 1 observation cho moi seat
        thay nguoi o frame nay, cung su kien/alert candidate cua frame."""
        self._seat_tracker.update(poses)
        observations = []
        candidates = []
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
            if posture_state == "head_drop":
                duration = timestamp - state.monitor.head_drop_since
                candidates.append(AlertCandidate(assignment.seat_id, "head_drop", duration))

        people_by_seat = {observation.seat_id: observation.person for observation in observations}
        back_turn_events = (
            self._back_turn_detector.update(timestamp, people_by_seat) if self._back_turn_detector else []
        )
        conversation_events = (
            self._side_conversation_detector.update(timestamp, people_by_seat)
            if self._side_conversation_detector
            else []
        )
        candidates += [AlertCandidate(event.seat_id, "back_turn", event.duration_sec) for event in back_turn_events]
        # Schema alert chi co 1 seat_id: phat 1 candidate cho MOI ghe trong cap.
        candidates += [
            AlertCandidate(seat_id, "side_conversation", event.duration_sec)
            for event in conversation_events
            for seat_id in (event.first_seat_id, event.second_seat_id)
        ]
        return FrameResult(observations, back_turn_events, conversation_events, candidates)

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
    alerts_emitted: int


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
    camera_angle_type: CameraAngleType = "frontal",
    alert_manager: AlertManager | None = None,
    on_alert: Callable[[AlertEvent], None] | None = None,
) -> PipelineRunResult:
    """Chay pipeline khong GUI; moi record engagement an danh duoc day ngay vao
    ``on_record`` (sink: ghi JSONL, day len Firestore, ...) va KHONG giu lai
    trong RAM -- session dai khong lam bo nho tang theo so frame. Sink chay
    dong bo trong vong lap frame nen phai nhanh; sink nem exception se dung
    pipeline (frame hien tai van duoc dispose). Logic engagement: xem
    ``EngagementEngine``.

    Alert: truyen ``alert_manager`` (giu session_id, cooldown, pause/resume)
    va ``on_alert`` cung nhau; moi AlertEvent duoc day vao ``on_alert`` ngay.
    Back-turn chi bat khi ``camera_angle_type == "frontal"``.

    Frame chi ton tai trong RAM cho den khi ``pose_provider.detect`` hoan tat;
    no duoc dispose trong ``finally``. ``timestamp`` duoc suy ra tu frame index
    va target FPS de test video co ket qua lap lai, khong phu thuoc toc do CI.
    """
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames phai >= 1 hoac None.")
    if camera_angle_type not in ("frontal", "top_down"):
        raise ValueError("camera_angle_type chi duoc la frontal hoac top_down.")
    if (alert_manager is None) != (on_alert is None):
        raise ValueError("alert_manager va on_alert phai duoc truyen cung nhau.")
    engine = EngagementEngine(
        seat_grid,
        max_seat_distance=max_seat_distance,
        calibration_duration_sec=calibration_duration_sec,
        posture_thresholds=posture_thresholds,
        smoothing_window_sec=smoothing_window_sec,
        back_turn_detector=BackTurnDetector() if camera_angle_type == "frontal" else None,
        side_conversation_detector=SideConversationDetector(),
    )
    records_emitted = 0
    alerts_emitted = 0
    frames_processed = 0

    with CameraCapture(capture_config) as capture:
        for frame in capture.frames():
            try:
                timestamp = frame.frame_index / capture_config.target_fps
                poses = pose_provider.detect(frame.image)
                result = engine.process(timestamp, poses)
                for observation in result.observations:
                    on_record(observation.record)
                    records_emitted += 1
                if alert_manager is not None:
                    for alert in alert_manager.update(timestamp, result.alert_candidates):
                        on_alert(alert)
                        alerts_emitted += 1
            finally:
                dispose_frame(frame)
            frames_processed += 1
            if max_frames is not None and frames_processed >= max_frames:
                break
    return PipelineRunResult(
        frames_processed=frames_processed, records_emitted=records_emitted, alerts_emitted=alerts_emitted
    )
