"""Vong doi edge node theo phien giam sat (UC02, UC04), chay boi ``python -m src.main``.

Listener Firestore chi luu ``{session_id: state}`` (``on_sessions``). Moi quyet
dinh nam trong ``step()`` tren thread chinh: bat/tat CaptureWorker theo trang
thai phien va lich trong config, xu ly frame, heartbeat, tong ket cuoi phien.
Camera chi mo khi phien ``active`` va dang trong cua so lich.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from src.capture import CameraOpenError, CaptureWorker, Frame
from src.config import LocalPipelineConfig, RemoteSeatGrid
from src.engagement.back_turn import BackTurnDetector
from src.engagement.side_conversation import SideConversationDetector
from src.pipeline.alert_manager import AlertManager
from src.pipeline.engagement_pipeline import EngagementEngine, PoseProvider, process_frame
from src.privacy import dispose_frame, make_session_summary
from src.sync import EdgeHeartbeat, FirestoreSink

logger = logging.getLogger("camera_ai.runtime")

LIVE_STATES = ("active", "paused")
MAX_FRAME_GAP_SEC = 5.0  # pause/mat camera chi lam dong ho phien tien toi da chung nay
CAMERA_TIMEOUT_SEC = 5.0  # khong co frame lau hon -> camera tam khong kha dung
CAMERA_RETRY_SEC = 10.0
RESUBSCRIBE_SEC = 30.0


@dataclass
class _Session:
    session_id: str
    engine: EngagementEngine
    alerts: AlertManager
    resumed: bool  # camera nay da co tong ket tu lan chay truoc -> so lieu chi la mot phan
    clock_sec: float = 0.0  # giay da giam sat; pause va mat camera khong tinh (MAX_FRAME_GAP_SEC)
    last_frame_ts: float | None = None


class EdgeRuntime:
    """``seat_grid`` tra ve seat grid hien hanh (``RuntimeConfigPoller.snapshot``), chot
    luc bat dau phien. ``capture_factory`` tao CaptureWorker moi moi lan bat camera.
    ``now``/``monotonic`` duoc thay trong test."""

    def __init__(
        self,
        config: LocalPipelineConfig,
        pose_provider: PoseProvider,
        seat_grid: Callable[[], RemoteSeatGrid],
        sink: FirestoreSink,
        capture_factory: Callable[[], CaptureWorker],
        *,
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

    def on_sessions(self, states: dict[str, Any]) -> None:
        """Callback cua listener (thread khac): chi thay snapshot ``{session_id: state}``."""
        self._states = dict(states)
        self._changed.set()

    def step(self) -> None:
        """1 vong: dong bo phien -> bat/tat camera -> xu ly toi da 1 frame -> heartbeat."""
        states = self._states
        if self._session and states.get(self._session.session_id) not in LIVE_STATES:
            # "ended": giao vien ket thuc. Document bi xoa/trang thai la: phien dut ngang (UC04).
            self._end_session("completed" if states.get(self._session.session_id) == "ended" else "incomplete")
        if self._session is None:
            live = sorted(session_id for session_id, state in states.items() if state in LIVE_STATES)
            if live:
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
        subscribe: Callable[[Callable[[dict[str, Any]], None]], Any],
        should_stop: Callable[[], bool] = lambda: False,
    ) -> None:
        """Vong lap chinh. ``subscribe(on_sessions)`` tra ve watch co ``unsubscribe()``.

        Watch Firestore chet han (``is_active`` False) khi loi quyen, va ca khi mat
        mang: google-api-core mo lai ket noi de quy toi RecursionError roi thread
        listener thoat. Chi dang ky lai khi sink vua ghi duoc (da co mang), neu
        khong moi lan thu se in hang nghin dong traceback. Trong luc do edge giu
        trang thai phien cuoi cung biet duoc."""
        watch = subscribe(self.on_sessions)
        resubscribe_at = 0.0
        try:
            while not should_stop():
                self.step()
                if (
                    not getattr(watch, "is_active", True)
                    and self._sink.failures == 0
                    and self._mono() >= resubscribe_at
                ):
                    logger.warning("Listener phien Firestore da dung, dang ky lai.")
                    watch.unsubscribe()
                    watch, resubscribe_at = subscribe(self.on_sessions), self._mono() + RESUBSCRIBE_SEC
        finally:
            watch.unsubscribe()
            self.close()

    def close(self) -> None:
        """Tat edge node: phien dang chay bi danh dau incomplete, heartbeat bao offline."""
        if self._session is not None:
            self._end_session("incomplete")
        self._heartbeat(online=False)

    def _start_session(self, session_id: str) -> None:
        remote = self._seat_grid()
        thresholds = self._config.thresholds
        engine = EngagementEngine(
            remote.grid,
            back_turn_detector=(
                BackTurnDetector(
                    max_face_visibility=thresholds.back_turn_max_face_visibility,
                    min_duration_sec=thresholds.back_turn_duration_sec,
                )
                if remote.camera_angle_type == "frontal"
                else None
            ),
            side_conversation_detector=SideConversationDetector(
                max_pair_distance=thresholds.conversation_max_distance_px,
                min_duration_sec=thresholds.conversation_duration_sec,
            ),
        )
        resumed = self._sink.summary_exists(session_id)
        self._session = _Session(session_id, engine, AlertManager(session_id), resumed)
        self._sink.add_summary(make_session_summary(session_id, "running", []))
        logger.info("Bat dau phien %s%s.", session_id, " (tiep tuc sau gian doan)" if resumed else "")

    def _end_session(self, status: str) -> None:
        session, self._session = self._session, None
        if self._worker is not None:
            self._stop_capture()
        if session.resumed:
            status = "incomplete"
        self._sink.add_summary(make_session_summary(session.session_id, status, session.engine.scores()))
        logger.info("Ket thuc phien %s: %s.", session.session_id, status)

    def _start_capture(self) -> None:
        worker = self._capture_factory()
        try:
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
        process_frame(
            frame,
            session.clock_sec,
            self._pose,
            session.engine,
            lambda record: self._sink.add_record(session.session_id, record),
            session.alerts,
            self._sink.add_alert,
        )
        self._frames_processed += 1

    def _status(self) -> str:
        if self._session is None:
            return "idle"
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
