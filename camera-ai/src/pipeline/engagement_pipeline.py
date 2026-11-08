"""Pipeline headless, co the test duoc voi video va pose provider gia lap."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Protocol

from src.capture import CameraCapture, CaptureConfig, Frame
from src.detection.pose_detector import PersonPose
from src.engagement.back_turn import BackTurnDetector, BackTurnEvent
from src.engagement.engagement_score import SeatEngagementTracker, classify_posture_state
from src.engagement.hand_activity import HandActivityMonitor
from src.engagement.posture import CameraAngleType, compute_head_drop_ratio, compute_torso_vector_angle
from src.engagement.posture_monitor import BaselineEstablisher, PostureMonitor, PostureThresholds, RollingSmoother
from src.engagement.rolling_engagement import DEFAULT_MAX_GAP_SEC, RollingSeatEngagementTracker
from src.engagement.side_conversation import SideConversationDetector, SideConversationEvent
from src.pipeline.alert_manager import AlertCandidate, AlertManager
from src.privacy import AlertEvent, AnonymizedEngagementRecord, anonymize_engagement, dispose_frame
from src.seating.seat_grid import SeatGrid
from src.seating.seat_tracker import SeatTracker


CONCENTRATION_WINDOW_SEC = 60.0  # ``concentration`` = diem trong cua so nay
AWAY_AFTER_SEC = 30.0  # khong thay nguoi lau hon -> ghe "away"
BEHAVIOUR_HOLD_SEC = 5.0  # quay lung/noi chuyen rieng vua xay ra trong khoang nay -> "distracted"


class PoseProvider(Protocol):
    """Diem thay the inference trong test; production co the dung PoseDetector."""

    def detect(self, image_bgr) -> List[PersonPose]: ...


@dataclass
class _SeatPipelineState:
    tracker: SeatEngagementTracker
    rolling: RollingSeatEngagementTracker
    baseline: BaselineEstablisher
    monitor: PostureMonitor
    hands: HandActivityMonitor
    head_smoother: RollingSmoother
    deviation_smoother: RollingSmoother
    last_seen: float = 0.0
    seen: bool = False  # last_seen chi co nghia khi da thay nguoi it nhat 1 lan
    posture_state: str = "normal"
    behaviour_at: Optional[float] = None  # lan cuoi quay lung/noi chuyen rieng
    window: Counter = field(default_factory=Counter)  # trang thai tu the -> giay trong window hien tai


@dataclass(frozen=True)
class SeatWindowState:
    """Thoi gian 1 ghe o tung trang thai tu the trong 1 window (``session_windows``)."""

    seat_id: str
    seconds: Dict[str, float]  # normal / slumping / head_drop
    last_seen: float
    last_state: str
    last_behaviour: Optional[float]  # quay lung/noi chuyen rieng gan nhat trong window


@dataclass(frozen=True)
class SeatState:
    """Trang thai 1 ghe cho ``session_results``/``session_evaluations`` (so dem alert do runtime giu)."""

    seat_id: str
    concentration: Optional[int]  # diem CONCENTRATION_WINDOW_SEC gan nhat; None khi ghe "away"
    avg_concentration: Optional[int]  # diem tu dau phien
    observed_sec: int
    status: str


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
        self._window_start = 0.0
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
            state.rolling.update(timestamp, head_event, slump_event, hand_activity)
            posture_state = classify_posture_state(head_event, slump_event, hand_activity)
            # Nhu RollingSeatEngagementTracker: khoang tu lan thay truoc thuoc trang thai vua xac nhan,
            # khoang trong qua dai khong tinh; phan nam truoc window hien tai da gui o window truoc.
            if state.seen and timestamp - state.last_seen <= DEFAULT_MAX_GAP_SEC:
                state.window[posture_state] += max(0.0, timestamp - max(state.last_seen, self._window_start))
            state.last_seen, state.posture_state, state.seen = timestamp, posture_state, True
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
        for candidate in candidates:
            if candidate.type != "head_drop":
                self._states[candidate.seat_id].behaviour_at = timestamp
        return FrameResult(observations, back_turn_events, conversation_events, candidates)

    def take_window(self, now: float) -> List[SeatWindowState]:
        """Cac ghe thay nguoi trong window [lan goi truoc, ``now``], theo seat_id; roi mo window moi tu ``now``."""
        start, self._window_start = self._window_start, now
        windows = []
        for seat_id, state in sorted(self._states.items()):
            if state.seen and state.last_seen >= start:
                recent = state.behaviour_at is not None and state.behaviour_at >= start
                behaviour = state.behaviour_at if recent else None
                seconds = {posture: state.window[posture] for posture in ("normal", "slumping", "head_drop")}
                windows.append(SeatWindowState(seat_id, seconds, state.last_seen, state.posture_state, behaviour))
            state.window.clear()
        return windows

    def seat_states(self, now: float) -> List[SeatState]:
        """Moi ghe da tung thay nguoi, theo seat_id: diem gan day, diem tu dau phien, trang thai luc ``now``."""
        return [self._seat_state(seat_id, state, now) for seat_id, state in sorted(self._states.items())]

    @staticmethod
    def _seat_state(seat_id: str, state: _SeatPipelineState, now: float) -> SeatState:
        if now - state.last_seen > AWAY_AFTER_SEC:
            status = "away"
        elif state.posture_state == "head_drop":
            status = "drowsy"
        elif state.posture_state == "slumping" or (
            state.behaviour_at is not None and now - state.behaviour_at <= BEHAVIOUR_HOLD_SEC
        ):
            status = "distracted"
        else:
            status = "focused"
        recent, total = state.rolling.compute_score(), state.tracker.compute_score()
        return SeatState(
            seat_id=seat_id,
            concentration=None if status == "away" or recent.score is None else round(recent.score),
            avg_concentration=None if total.score is None else round(total.score),
            observed_sec=round(total.time_total),
            status=status,
        )

    def _state_for(self, seat_id: str) -> _SeatPipelineState:
        if seat_id not in self._states:
            self._states[seat_id] = _SeatPipelineState(
                tracker=SeatEngagementTracker(seat_id),
                rolling=RollingSeatEngagementTracker(seat_id, window_sec=CONCENTRATION_WINDOW_SEC),
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


def process_frame(
    frame: Frame,
    timestamp: float,
    pose_provider: PoseProvider,
    engine: EngagementEngine,
    on_record: Callable[[AnonymizedEngagementRecord], None],
    alert_manager: AlertManager | None = None,
    on_alert: Callable[[AlertEvent], None] | None = None,
) -> tuple[int, int]:
    """Inference 1 frame roi day record/alert ra sink; tra ve (so record, so alert).
    Frame LUON duoc dispose, ke ca khi inference hoac sink nem loi."""
    try:
        result = engine.process(timestamp, pose_provider.detect(frame.image))
        for observation in result.observations:
            on_record(observation.record)
        alerts = alert_manager.update(timestamp, result.alert_candidates) if alert_manager is not None else []
        for alert in alerts:
            on_alert(alert)
        return len(result.observations), len(alerts)
    finally:
        dispose_frame(frame)


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
            timestamp = frame.frame_index / capture_config.target_fps
            records, alerts = process_frame(frame, timestamp, pose_provider, engine, on_record, alert_manager, on_alert)
            records_emitted += records
            alerts_emitted += alerts
            frames_processed += 1
            if max_frames is not None and frames_processed >= max_frames:
                break
    return PipelineRunResult(
        frames_processed=frames_processed, records_emitted=records_emitted, alerts_emitted=alerts_emitted
    )
