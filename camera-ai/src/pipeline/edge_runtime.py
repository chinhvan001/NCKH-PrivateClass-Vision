"""Vong doi edge node theo phien giam sat (UC02, UC04), chay boi ``python -m src.main``.

Listener Firestore chi luu ``{session_id: state}`` (``on_sessions``). Moi quyet
dinh nam trong ``step()`` tren thread chinh: bat/tat CaptureWorker theo trang
thai phien va lich trong config, xu ly frame, heartbeat, ket qua phien.
Camera chi mo khi phien ``active`` va dang trong cua so lich.

Ket qua theo dong ho phien (giay da giam sat): ``session_results`` va 1 document
``session_windows`` (thoi gian moi ghe o tung trang thai tu the, de backend web tinh diem)
moi ``RESULT_INTERVAL_SEC``, ``session_evaluations`` moi ``EVALUATION_INTERVAL_SEC``
va lan cuoi khi het phien; record tung ghe khong roi edge.

Config de ``class_id`` null: lop la lop admin gan cho camera tren trang Quan ly camera,
doc lai khi khong co phien; doi lop thi ``run()`` nghe phien cua lop moi.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from src.capture import CameraOpenError, CaptureWorker, Frame
from src.config import ClassLayoutError, LocalPipelineConfig
from src.engagement.back_turn import BackTurnDetector
from src.engagement.side_conversation import SideConversationDetector
from src.pipeline.alert_manager import AlertManager
from src.pipeline.engagement_pipeline import EngagementEngine, PoseProvider, process_frame
from src.privacy import (
    AlertEvent,
    SeatEvaluation,
    SeatResult,
    SeatWindow,
    SessionResult,
    SessionWindow,
    dispose_frame,
)
from src.seating import SeatGrid, SeatGridError
from src.sync import EdgeHeartbeat, FirestoreSink

logger = logging.getLogger("camera_ai.runtime")

LIVE_STATES = ("active", "paused")
MAX_FRAME_GAP_SEC = 5.0  # pause/mat camera chi lam dong ho phien tien toi da chung nay
CAMERA_TIMEOUT_SEC = 5.0  # khong co frame lau hon -> camera tam khong kha dung
CAMERA_RETRY_SEC = 10.0
LAYOUT_RETRY_SEC = 10.0  # chua nap duoc so do lop -> thu lai sau
RESUBSCRIBE_SEC = 30.0
RESULT_INTERVAL_SEC = 10.0
EVALUATION_INTERVAL_SEC = 300.0
# ponytail: hoi lai lop tren web theo chu ky khi ranh (<= 1440 lan doc/ngay); listener document
# camera_configs/{camera_id} neu so edge node lam vuot quota doc.
CLASS_CHECK_SEC = 60.0
UNCONFIGURED_CHECK_SEC = 15.0  # camera chua duoc them tren web: hoi nhanh hon de admin khoi doi


@dataclass
class _Session:
    session_id: str
    grid: SeatGrid
    engine: EngagementEngine
    alerts: AlertManager
    resumed: bool  # phien da co ket qua tu lan chay truoc -> so lieu chi la mot phan
    clock_sec: float = 0.0  # giay da giam sat; pause va mat camera khong tinh (MAX_FRAME_GAP_SEC)
    last_frame_ts: float | None = None
    result_at: float = 0.0  # clock_sec lan ghi session_results gan nhat
    evaluation_at: float = 0.0
    distraction: Counter = field(default_factory=Counter)  # seat_id -> so alert
    interaction: Counter = field(default_factory=Counter)  # seat_id -> so alert side_conversation
    run: str = field(default_factory=lambda: uuid.uuid4().hex[:8])  # dong ho phien chay lai tu 0 moi run
    window_seq: int = 0
    window_alerts: defaultdict = field(default_factory=lambda: defaultdict(Counter))  # seat_id -> loai -> so


class _NoWatch:
    """Camera chua co lop: khong nghe phien nao."""

    is_active = True

    def unsubscribe(self) -> None:
        pass


class EdgeRuntime:
    """``seat_grid(class_id)`` nap so do ghe cua lop (``config.load_class_seat_grid``), goi luc
    bat dau phien va chot cho ca phien. ``capture_factory`` tao CaptureWorker moi moi lan bat
    camera; nem ``CameraOpenError`` thi camera tam khong kha dung. ``web_class`` (khi config de
    ``class_id`` null) doc lop admin gan cho camera tren web. ``now``/``monotonic`` duoc thay
    trong test."""

    def __init__(
        self,
        config: LocalPipelineConfig,
        pose_provider: PoseProvider,
        seat_grid: Callable[[str], SeatGrid],
        sink: FirestoreSink,
        capture_factory: Callable[[], CaptureWorker],
        *,
        web_class: Callable[[], str | None] | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        monotonic: Callable[[], float] = time.monotonic,
        heartbeat_interval_sec: float = 10.0,
        poll_sec: float = 0.5,
    ) -> None:
        self._config = config
        self._pose = pose_provider
        self._seat_grid = seat_grid
        self._sink = sink
        self._capture_factory = capture_factory
        self._now = now
        self._mono = monotonic
        self._heartbeat_interval_sec = heartbeat_interval_sec
        self._poll_sec = poll_sec
        self._states: dict[str, Any] = {}
        self._changed = threading.Event()
        self._session: _Session | None = None
        self._worker: CaptureWorker | None = None
        self._in_schedule = False
        self._camera_ok: bool | None = None
        self._camera_retry_at = 0.0
        self._last_frame_mono = 0.0
        self._last_frame_at: datetime | None = None
        self._frames_seen = 0
        self._frames_processed = 0  # tu heartbeat truoc, de tinh fps
        self._heartbeat_status: str | None = None
        self._heartbeat_mono = monotonic()
        self._layout_failed = False  # co phien song nhung chua nap duoc so do lop
        self._layout_retry_at = 0.0
        self._class_id = config.camera.class_id
        self._web_class = web_class
        self._class_check_at = 0.0

    def on_sessions(self, states: dict[str, Any]) -> None:
        """Callback cua listener (thread khac): chi thay snapshot ``{session_id: state}``."""
        self._states = dict(states)
        self._changed.set()

    def step(self) -> None:
        """1 vong: lop tren web -> dong bo phien -> bat/tat camera -> xu ly toi da 1 frame -> heartbeat."""
        self._check_web_class()
        states = self._states
        if self._session and states.get(self._session.session_id) not in LIVE_STATES:
            # "ended": giao vien ket thuc. Document bi xoa/trang thai la: phien dut ngang (UC04).
            self._end_session("completed" if states.get(self._session.session_id) == "ended" else "incomplete")
        if self._session is None:
            live = sorted(session_id for session_id, state in states.items() if state in LIVE_STATES)
            if not live:
                self._layout_failed = False
            elif self._mono() >= self._layout_retry_at:
                # ponytail: nhieu phien song trong 1 lop la loi phia app; lay id nho nhat cho on dinh
                self._start_session(live[0])

        self._in_schedule = self._config.schedule.allows(self._now())
        capture = self._session is not None and states.get(self._session.session_id) == "active" and self._in_schedule
        if self._worker is not None and not (capture and self._worker.is_alive):
            if capture:  # thread capture chet bat thuong: tat roi thu lai sau
                self._camera_ok, self._camera_retry_at = False, self._mono() + CAMERA_RETRY_SEC
            self._stop_capture()
        if capture and self._worker is None and self._mono() >= self._camera_retry_at:
            self._start_capture()
        if self._session is not None and self._session.alerts.active != capture:
            (self._session.alerts.resume if capture else self._session.alerts.pause)()

        if self._worker is None:
            self._changed.wait(self._poll_sec)
            self._changed.clear()
        else:
            frame = self._worker.buffer.get(timeout=self._poll_sec)
            if frame is not None:
                self._on_frame(frame)
            self._camera_ok = self._mono() - self._last_frame_mono < CAMERA_TIMEOUT_SEC
        self._heartbeat()

    def run(
        self,
        subscribe: Callable[[str, Callable[[dict[str, Any]], None]], Any],
        should_stop: Callable[[], bool] = lambda: False,
    ) -> None:
        """Vong lap chinh. ``subscribe(class_id, on_sessions)`` tra ve watch co ``unsubscribe()``;
        lop tren web doi thi huy watch cu va nghe lop moi.

        Watch Firestore chet han (``is_active`` False) khi loi quyen, va ca khi mat
        mang: google-api-core mo lai ket noi de quy toi RecursionError roi thread
        listener thoat. Chi dang ky lai khi sink vua ghi duoc (da co mang), neu
        khong moi lan thu se in hang nghin dong traceback. Trong luc do edge giu
        trang thai phien cuoi cung biet duoc."""
        watch, watched = self._subscribe(subscribe), self._class_id
        resubscribe_at = 0.0
        try:
            while not should_stop():
                self.step()
                if self._class_id != watched:
                    watch.unsubscribe()
                    watch, watched = self._subscribe(subscribe), self._class_id
                elif (
                    not getattr(watch, "is_active", True)
                    and self._sink.failures == 0
                    and self._mono() >= resubscribe_at
                ):
                    logger.warning("Listener phien Firestore da dung, dang ky lai.")
                    watch.unsubscribe()
                    watch, resubscribe_at = self._subscribe(subscribe), self._mono() + RESUBSCRIBE_SEC
        finally:
            watch.unsubscribe()
            self.close()

    def _subscribe(self, subscribe: Callable[[str, Callable[[dict[str, Any]], None]], Any]) -> Any:
        class_id = self._class_id
        if class_id is None:
            return _NoWatch()

        def on_sessions(states: dict[str, Any]) -> None:
            if class_id == self._class_id:  # bo snapshot den tre cua listener lop cu
                self.on_sessions(states)

        return subscribe(class_id, on_sessions)

    def _check_web_class(self) -> None:
        """Lop admin gan cho camera tren web, chi doc lai khi khong co phien."""
        if self._web_class is None or self._session is not None or self._mono() < self._class_check_at:
            return
        self._class_check_at = self._mono() + (CLASS_CHECK_SEC if self._class_id else UNCONFIGURED_CHECK_SEC)
        try:
            class_id = self._web_class()
        except ClassLayoutError as error:  # Firestore loi: giu lop dang nghe
            logger.warning("%s Giu lop hien tai.", error)
            return
        if class_id != self._class_id:
            logger.info("Lop cua camera tren web doi: %s -> %s.", self._class_id, class_id)
            self._class_id, self._states, self._layout_failed = class_id, {}, False
            self._heartbeat_status = None  # gui heartbeat ngay: web kiem tra truoc tiet theo lop trong heartbeat

    def close(self) -> None:
        """Tat edge node: phien dang chay bi danh dau incomplete, heartbeat bao offline."""
        if self._session is not None:
            self._end_session("incomplete")
        self._heartbeat(online=False)

    def _start_session(self, session_id: str) -> None:
        try:
            grid = self._seat_grid(self._class_id)
        except (ClassLayoutError, SeatGridError) as error:  # message khong chua du lieu lop
            self._layout_failed, self._layout_retry_at = True, self._mono() + LAYOUT_RETRY_SEC
            logger.warning(
                "Chua nap duoc so do lop cho phien %s: %s Thu lai sau %.0fs.", session_id, error, LAYOUT_RETRY_SEC
            )
            return
        self._layout_failed = False
        thresholds = self._config.thresholds
        engine = EngagementEngine(
            grid,
            back_turn_detector=(
                BackTurnDetector(
                    max_face_visibility=thresholds.back_turn_max_face_visibility,
                    min_duration_sec=thresholds.back_turn_duration_sec,
                )
                if self._config.camera.angle_type == "frontal"
                else None
            ),
            side_conversation_detector=SideConversationDetector(
                max_pair_distance=thresholds.conversation_max_distance_px,
                min_duration_sec=thresholds.conversation_duration_sec,
            ),
        )
        resumed = self._sink.result_exists(session_id)
        self._session = _Session(session_id, grid, engine, AlertManager(session_id), resumed)
        self._publish_result(self._session, "running")
        logger.info("Bat dau phien %s%s.", session_id, " (tiep tuc sau gian doan)" if resumed else "")

    def _end_session(self, status: str) -> None:
        session, self._session = self._session, None
        if self._worker is not None:
            self._stop_capture()
        if session.resumed:
            status = "incomplete"
        self._publish_window(session, status)
        self._publish_evaluations(session)
        self._publish_result(session, status)
        logger.info("Ket thuc phien %s: %s.", session.session_id, status)

    def _publish_result(self, session: _Session, monitoring_status: str) -> None:
        seats = tuple(
            SeatResult(state.seat_id, state.concentration, session.interaction[state.seat_id], state.status)
            for state in session.engine.seat_states(session.clock_sec)
        )
        self._sink.set_result(
            SessionResult(session.session_id, self._config.camera.camera_id, self._now(), monitoring_status, seats)
        )
        session.result_at = session.clock_sec

    def _publish_evaluations(self, session: _Session) -> None:
        now = self._now()
        self._sink.set_evaluations(
            SeatEvaluation(
                session.session_id,
                state.seat_id,
                now,
                state.concentration,
                state.avg_concentration,
                session.distraction[state.seat_id],
                state.observed_sec,
            )
            for state in session.engine.seat_states(session.clock_sec)
        )
        session.evaluation_at = session.clock_sec

    def _publish_window(self, session: _Session, monitoring_status: str) -> None:
        """Thoi gian moi ghe o tung trang thai tu the tu window truoc, cho backend web tinh diem."""
        seats = tuple(
            SeatWindow(
                state.seat_id,
                state.seconds["normal"],
                state.seconds["slumping"],
                state.seconds["head_drop"],
                state.last_seen,
                state.last_state,
                state.last_behaviour,
                dict(session.window_alerts.pop(state.seat_id, {})),
            )
            for state in session.engine.take_window(session.clock_sec)
        )
        self._sink.add_window(
            SessionWindow(
                session.session_id,
                self._config.camera.camera_id,
                session.run,
                session.window_seq,
                session.result_at,  # window ghi cung luc voi session_results, ke ca lan ghi dau luc bat dau phien
                session.clock_sec,
                self._now(),
                monitoring_status,
                seats,
            )
        )
        session.window_seq += 1

    def _on_alert(self, session: _Session, alert: AlertEvent) -> None:
        session.distraction[alert.seat_id] += 1
        if alert.type == "side_conversation":
            session.interaction[alert.seat_id] += 1
        session.window_alerts[alert.seat_id][alert.type] += 1
        self._sink.add_alert(alert)

    def _start_capture(self) -> None:
        try:
            worker = self._capture_factory()  # nguon camera tren web: chua them camera hoac Firestore loi
            worker.start()
        except CameraOpenError as error:  # message da an credential (redact_source)
            self._camera_ok, self._camera_retry_at = False, self._mono() + CAMERA_RETRY_SEC
            logger.warning("%s Thu lai sau %.0fs.", error, CAMERA_RETRY_SEC)
            return
        self._worker, self._last_frame_mono = worker, self._mono()  # cho frame dau toi da CAMERA_TIMEOUT_SEC

    def _stop_capture(self) -> None:
        self._worker.stop()  # giai phong camera, xoa frame con trong buffer
        self._worker = None

    def _on_frame(self, frame: Frame) -> None:
        session = self._session
        self._last_frame_mono = self._mono()
        self._last_frame_at = datetime.fromtimestamp(frame.timestamp, timezone.utc)
        self._frames_seen += 1
        if (self._frames_seen - 1) % self._config.sampling.inference_every_n_frames:
            dispose_frame(frame)
            return
        if session.last_frame_ts is not None:
            session.clock_sec += min(max(frame.timestamp - session.last_frame_ts, 0.0), MAX_FRAME_GAP_SEC)
        session.last_frame_ts = frame.timestamp
        height, width = frame.image.shape[:2]
        session.grid.fit_to(width, height)  # o ghe ve tren anh chup co the khac do phan giai luong camera
        process_frame(
            frame,
            session.clock_sec,
            self._pose,
            session.engine,
            lambda record: None,  # record tung ghe chi dung noi bo; Firestore nhan ket qua tong hop ben duoi
            session.alerts,
            lambda alert: self._on_alert(session, alert),
        )
        self._frames_processed += 1
        if session.clock_sec - session.result_at >= RESULT_INTERVAL_SEC:
            self._publish_window(session, "running")  # truoc _publish_result: window bat dau tu result_at
            self._publish_result(session, "running")
        if session.clock_sec - session.evaluation_at >= EVALUATION_INTERVAL_SEC:
            self._publish_evaluations(session)

    def _status(self) -> str:
        if self._class_id is None:
            return "unconfigured"
        if self._session is None:
            return "unavailable" if self._layout_failed else "idle"
        if self._states.get(self._session.session_id) == "paused":
            return "paused"
        if not self._in_schedule:
            return "outside_schedule"
        return "monitoring" if self._worker is not None and self._camera_ok else "unavailable"

    def _heartbeat(self, online: bool = True) -> None:
        """Gui khi trang thai doi hoac moi ``heartbeat_interval_sec``."""
        now, status = self._mono(), self._status()
        elapsed = now - self._heartbeat_mono
        if online and status == self._heartbeat_status and elapsed < self._heartbeat_interval_sec:
            return
        self._sink.set_heartbeat(
            EdgeHeartbeat(
                class_id=self._class_id,
                online=online,
                status=status,
                session_id=self._session.session_id if self._session else None,
                fps=round(self._frames_processed / elapsed, 1) if elapsed > 0 else 0.0,
                camera_ok=self._camera_ok,
                last_frame_at=self._last_frame_at,
                updated_at=self._now(),
            )
        )
        self._heartbeat_status, self._heartbeat_mono, self._frames_processed = status, now, 0
