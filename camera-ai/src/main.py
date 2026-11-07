"""Camera AI cho ca may: ``python -m src.main``.

Moi camera admin them tren web admin co 1 edge node (EdgeRuntime tren 1 thread mang ten camera,
dung chung model). Web admin va camera AI chay tren cung may va trao doi qua file JSON trong
``sync.DATA_DIR`` (``edge-data/``), khong qua Firebase: web ghi nguon camera, goc camera va tiet
hien tai (kem o ghe), edge ghi ket qua va heartbeat. Them, xoa hay doi goc camera tren web co hieu
luc trong CAMERA_POLL_SEC; dia chi doi co hieu luc tu lan mo camera sau. Moi edge node chi bat
camera khi tiet cua camera dang chay trong lich. Cai dat chung (lich, nguong nhan dien) mac dinh
trong config.local_schema, ``--settings`` de doi. Xem docs/edge_node.md.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from src.capture import CameraOpenError, CaptureConfig, CaptureWorker
from src.capture.camera_capture import redact_source
from src.config import CAMERA_ANGLE_TYPES, EdgeSettings, LocalConfigError, LocalPipelineConfig, session_seat_grid
from src.detection import PoseDetector
from src.logging_config import setup_logging
from src.pipeline import EdgeRuntime
from src.pipeline.engagement_pipeline import PoseProvider
from src.privacy import dispose_frame
from src.sync import DATA_DIR, LocalSink, camera_session, camera_source, cameras, prune_sessions, session_states

logger = logging.getLogger("camera_ai.main")

CAMERA_POLL_SEC = 30.0  # doc lai danh sach camera tren web
CAMERA_STOP_SEC = 20.0  # camera mang khong tra loi: dong toi da STREAM_TIMEOUT_MS
PRUNE_SEC = 86400.0  # moi ngay xoa du lieu tiet cu hon privacy.retention_days


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.main", description="Chay camera AI cho moi camera tren web.")
    parser.add_argument("--settings", type=Path, help="File cai dat chung JSON (config/README.md); mac dinh: san.")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    parser.add_argument("--camera", help="Chi chay camera nay (ten camera tren web), vd khi thu.")
    parser.add_argument(
        "--check-camera",
        type=float,
        nargs="?",
        const=5.0,
        metavar="GIAY",
        help="Chi doc moi camera trong GIAY giay (mac dinh 5), in do phan giai va FPS roi thoat.",
    )
    parser.add_argument(
        "--video",
        type=Path,
        help="Thu bang file video thay cho camera: hinh chay theo thoi gian thuc, het thi lap lai; "
        "van chi doc trong phien giam sat.",
    )
    return parser.parse_args(argv)


def pose_detector(model: str, thresholds) -> PoseDetector:
    """PoseDetector theo nguong trong cai dat (demo web offline --video dung chung)."""
    return PoseDetector(
        model,
        min_confidence=thresholds.pose_confidence,
        image_size=thresholds.image_size,
        iou_threshold=thresholds.iou_threshold,
        max_detections=thresholds.max_detections,
        tile_size=thresholds.tile_size,
        tile_overlap=thresholds.tile_overlap,
    )


def list_cameras(root: Path, only: str | None = None) -> dict[str, str]:
    """{camera_id: goc camera} cua cac camera tren trang Quan ly camera."""
    angles = {}
    for camera_id, data in cameras(root).items():
        if only is None or camera_id == only:
            angle = data.get("angle_type")
            angles[camera_id] = angle if angle in CAMERA_ANGLE_TYPES else "frontal"
    return angles


def check_camera(name: str, capture_config: CaptureConfig, seconds: float) -> int:
    """Kiem tra ket noi camera luc lap dat, khong can model. Frame chi nam trong RAM va bi xoa ngay;
    edge node van chi mo camera trong phien."""
    source = redact_source(capture_config.source)
    worker = CaptureWorker(capture_config)  # buffer 1 frame, nhu privacy.frame_buffer_size
    try:
        worker.start()
    except CameraOpenError as error:  # message da an credential
        print(f"{name}: {error}", file=sys.stderr)
        return 1
    count, size, deadline = 0, None, time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            frame = worker.buffer.get(timeout=0.5)
            if frame is not None:
                count, size = count + 1, frame.image.shape[1::-1]
                dispose_frame(frame)
    finally:
        worker.stop()
    if not count:
        print(f"{name} ({source}) mo duoc nhung khong gui frame nao trong {seconds:g}s.", file=sys.stderr)
        return 1
    print(
        f"{name} ({source}): {size[0]}x{size[1]}, {count / seconds:.1f} fps trong {seconds:g}s "
        f"(capture_fps {capture_config.target_fps:g})."
    )
    return 0


def check_cameras(
    root: Path, settings: EdgeSettings, video: CaptureConfig | None, only: str | None, seconds: float
) -> int:
    try:
        angles = list_cameras(root, only)
    except (OSError, ValueError) as error:  # chi ten loi: file camera chua URL kem mat khau
        print(f"Khong doc duoc danh sach camera tren web ({type(error).__name__}).", file=sys.stderr)
        return 1
    if not angles:
        print("Chua co camera nao tren web admin (trang Quan ly camera).", file=sys.stderr)
        return 1
    code = 0
    for camera_id, angle in sorted(angles.items()):
        try:
            capture = video or settings.for_camera(camera_id, angle).to_capture_config(camera_source(root, camera_id))
        except LocalConfigError as error:  # chua co dia chi tren web
            print(f"{camera_id}: {error}", file=sys.stderr)
            code = 1
            continue
        code = max(code, check_camera(camera_id, capture, seconds))
    return code


def edge_runtime(
    root: Path, config: LocalPipelineConfig, pose: PoseProvider, capture: Callable[[], CaptureWorker], **options: Any
) -> EdgeRuntime:
    """EdgeRuntime cua camera ``config.camera.camera_id`` tren thu muc chung voi web admin; chay bang
    ``run(web_sessions(root, camera_id), ...)``. ``options`` (now, monotonic, poll_sec) cho test va demo."""
    camera_id = config.camera.camera_id
    return EdgeRuntime(
        config,
        pose,
        lambda session_id: session_seat_grid(camera_session(root, camera_id), session_id),
        LocalSink(root, camera_id),
        capture,
        **options,
    )


def web_sessions(root: Path, camera_id: str) -> Callable[[], dict[str, Any]]:
    """{session_id: state} tu tiet hien tai web admin giao cho camera."""
    return lambda: session_states(camera_session(root, camera_id))


def camera_node(
    root: Path, settings: EdgeSettings, detector: PoseDetector, video: CaptureConfig | None, camera_id: str, angle: str
) -> Callable[[Callable[[], bool]], None]:
    """Ham chay edge node cua 1 camera tren thread cua no, toi khi ``should_stop()``."""
    config = settings.for_camera(camera_id, angle)

    def capture() -> CaptureWorker:
        try:  # dia chi va mat khau doc lai moi lan mo camera: doi tren web co hieu luc tu lan mo sau
            source = video or config.to_capture_config(camera_source(root, camera_id))
        except LocalConfigError as error:  # chua co dia chi tren web
            raise CameraOpenError(str(error)) from error
        except (OSError, ValueError) as error:  # chi ten loi: file camera chua URL kem mat khau
            raise CameraOpenError(f"Khong doc duoc dia chi camera {camera_id!r} ({type(error).__name__}).") from error
        return CaptureWorker(source, buffer_size=config.privacy.frame_buffer_size)

    def run(should_stop: Callable[[], bool]) -> None:
        try:
            edge_runtime(root, config, detector, capture).run(web_sessions(root, camera_id), should_stop)
        except Exception:
            logger.exception("Edge node cua %s dung vi loi.", camera_id)  # supervisor chay lai

    return run


class CameraThread:
    """Edge node cua 1 camera tren thread rieng; ten thread (camera_id) hien trong log."""

    def __init__(self, name: str, target: Callable[[Callable[[], bool]], None]) -> None:
        self._stop = threading.Event()
        self._thread = threading.Thread(target=target, args=(self._stop.is_set,), name=name, daemon=True)
        self._thread.start()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(CAMERA_STOP_SEC)


class CameraSupervisor:
    """Giu dung 1 edge node cho moi camera tren web. ``start(camera_id, angle)`` tra ve doi tuong co
    ``stop()`` va ``is_alive()`` (CameraThread; gia lap trong test)."""

    def __init__(self, start: Callable[[str, str], Any]) -> None:
        self._start = start
        self._running: dict[str, tuple[str, Any]] = {}

    def sync(self, wanted: dict[str, str]) -> None:
        for camera_id, (angle, node) in list(self._running.items()):
            if wanted.get(camera_id) == angle and node.is_alive():
                continue
            if not node.is_alive():
                logger.error("Edge node cua %s da dung, chay lai.", camera_id)
            else:
                logger.info("Dung edge node cua %s (%s).", camera_id, "doi goc" if camera_id in wanted else "da xoa")
            node.stop()  # phien dang chay danh dau incomplete, heartbeat bao offline
            del self._running[camera_id]
        for camera_id, angle in sorted(wanted.items()):
            if camera_id not in self._running:
                logger.info("Bat edge node cho %s (goc %s).", camera_id, angle)
                self._running[camera_id] = (angle, self._start(camera_id, angle))

    def stop_all(self) -> None:
        for _, node in self._running.values():
            node.stop()
        self._running.clear()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.video is not None and not args.video.is_file():
        print(f"Khong tim thay video: {args.video}", file=sys.stderr)
        return 2
    try:
        settings = EdgeSettings.from_json_file(args.settings) if args.settings else EdgeSettings.default()
    except LocalConfigError as error:
        print(f"Cai dat khong hop le: {error}", file=sys.stderr)
        return 2
    root = DATA_DIR
    video = None
    if args.video is not None:  # thay nguon cua moi camera: lop va o ghe van lay tu web
        video = CaptureConfig(str(args.video), target_fps=settings.sampling.capture_fps, live_video=True)
    if args.check_camera is not None:
        return check_cameras(root, settings, video, args.camera, args.check_camera)

    setup_logging()
    detector = pose_detector(args.model, settings.thresholds)
    try:
        detector.open()
    except RuntimeError as error:  # thieu model
        print(error, file=sys.stderr)
        return 1

    def start(camera_id: str, angle: str) -> CameraThread:
        return CameraThread(camera_id, camera_node(root, settings, detector, video, camera_id, angle))

    supervisor = CameraSupervisor(start)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # dung service -> van chay cac khoi finally
    first, prune_at = True, 0.0
    try:
        while True:
            if time.monotonic() >= prune_at:
                prune_at = time.monotonic() + PRUNE_SEC
                if removed := prune_sessions(root, settings.privacy.retention_days):
                    logger.info("Da xoa du lieu %d tiet cu hon %d ngay.", removed, settings.privacy.retention_days)
            try:
                wanted = list_cameras(root, args.camera)
            except (OSError, ValueError) as error:  # file sua tay hong: giu cac camera dang chay
                logger.warning("Khong doc duoc danh sach camera tren web (%s), giu nguyen.", type(error).__name__)
            else:
                if first and not wanted:
                    logger.info("Chua co camera nao tren web admin: them camera o trang Quan ly camera.")
                first = False
                supervisor.sync(wanted)
            time.sleep(CAMERA_POLL_SEC)
    except KeyboardInterrupt:
        pass
    finally:
        supervisor.stop_all()
        detector.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
