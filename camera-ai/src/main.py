"""Edge node: ``python -m src.main --config config/local_pipeline.json``.

Doc LocalPipelineConfig, nghe phien giam sat cua lop tren Firestore va chi bat
camera khi phien dang chay trong cua so lich cua config. Lop va nguon camera de null
trong config thi lay tu camera admin them tren web (camera_configs). Xem docs/edge_node.md.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from src.capture import CameraOpenError, CaptureConfig, CaptureWorker
from src.capture.camera_capture import redact_source
from src.config import (
    ClassLayoutError,
    LocalConfigError,
    LocalPipelineConfig,
    load_camera_class,
    load_camera_setting,
    load_class_seat_grid,
)
from src.detection import PoseDetector
from src.logging_config import setup_logging
from src.pipeline import EdgeRuntime
from src.privacy import dispose_frame
from src.sync import FirestoreSink, firestore_client_from_env


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.main", description="Chay edge node camera-ai.")
    parser.add_argument("--config", type=Path, required=True, help="Config local JSON (config/README.md).")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    parser.add_argument(
        "--check-camera",
        type=float,
        nargs="?",
        const=5.0,
        metavar="GIAY",
        help="Chi doc camera trong GIAY giay (mac dinh 5), in do phan giai va FPS roi thoat.",
    )
    parser.add_argument(
        "--video",
        type=Path,
        help="Thu bang file video thay cho camera: hinh chay theo thoi gian thuc, het thi lap lai; "
        "van chi doc trong phien giam sat.",
    )
    return parser.parse_args(argv)


def pose_detector(model: str, thresholds) -> PoseDetector:
    """PoseDetector theo nguong trong config (demo web offline --video dung chung)."""
    return PoseDetector(
        model,
        min_confidence=thresholds.pose_confidence,
        image_size=thresholds.image_size,
        iou_threshold=thresholds.iou_threshold,
        max_detections=thresholds.max_detections,
        tile_size=thresholds.tile_size,
        tile_overlap=thresholds.tile_overlap,
    )


def check_camera(capture_config: CaptureConfig, seconds: float) -> int:
    """Kiem tra ket noi camera luc lap dat, khong can model (nguon tren web thi can credential
    Firebase de doc). Frame chi nam trong RAM va bi xoa ngay; edge node van chi mo camera trong phien."""
    source = redact_source(capture_config.source)
    worker = CaptureWorker(capture_config)  # buffer 1 frame, nhu privacy.frame_buffer_size
    try:
        worker.start()
    except CameraOpenError as error:  # message da an credential
        print(error, file=sys.stderr)
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
        print(f"Camera {source} mo duoc nhung khong gui frame nao trong {seconds:g}s.", file=sys.stderr)
        return 1
    print(
        f"Camera {source}: {size[0]}x{size[1]}, {count / seconds:.1f} fps trong {seconds:g}s "
        f"(capture_fps {capture_config.target_fps:g})."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.video is not None and not args.video.is_file():
        print(f"Khong tim thay video: {args.video}", file=sys.stderr)
        return 2
    try:
        config = LocalPipelineConfig.from_json_file(args.config)
        if config.camera.source_env is not None and args.video is None:
            config.to_capture_config()  # bao loi som neu thieu bien moi truong nguon camera
    except LocalConfigError as error:
        print(f"Config khong hop le: {error}", file=sys.stderr)
        return 2
    camera, thresholds = config.camera, config.thresholds
    video = None
    if args.video is not None:  # thay camera: khong can nguon camera trong config hay tren web
        video = CaptureConfig(str(args.video), target_fps=config.sampling.capture_fps, live_video=True)
    if args.check_camera is not None and (video or camera.source_env is not None):
        return check_camera(video or config.to_capture_config(), args.check_camera)

    try:
        client = firestore_client_from_env()
    except RuntimeError as error:  # thieu credential
        print(error, file=sys.stderr)
        return 1

    def capture_config() -> CaptureConfig:
        """Nguon tren web doc lai moi lan mo camera: mat khau doi tren web co hieu luc tu lan mo sau."""
        if video:
            return video
        web_source = None if camera.source_env else load_camera_setting(client, camera.camera_id, "source")
        return config.to_capture_config(web_source)

    if args.check_camera is not None:
        try:
            return check_camera(capture_config(), args.check_camera)
        except (LocalConfigError, ClassLayoutError) as error:
            print(error, file=sys.stderr)
            return 1

    def capture() -> CaptureWorker:
        try:
            return CaptureWorker(capture_config(), buffer_size=config.privacy.frame_buffer_size)
        except (LocalConfigError, ClassLayoutError) as error:  # camera chua them tren web, Firestore loi
            raise CameraOpenError(str(error)) from error

    setup_logging()
    detector = pose_detector(args.model, thresholds)
    try:
        detector.open()
    except RuntimeError as error:  # thieu model
        print(error, file=sys.stderr)
        return 1

    sink = FirestoreSink(client, camera.camera_id, retention_days=config.privacy.retention_days)
    sink.start()
    runtime = EdgeRuntime(
        config,
        detector,
        lambda class_id: load_class_seat_grid(client, class_id, config.seating.corner_seats, camera.camera_id),
        sink,
        capture,
        web_class=None if camera.class_id else lambda: load_camera_class(client, camera.camera_id),
    )
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # dung service -> van chay cac khoi finally
    try:
        runtime.run(sink.watch_sessions)
    except KeyboardInterrupt:
        pass
    finally:
        sink.close()
        detector.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
