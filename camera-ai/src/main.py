"""Edge node: ``python -m src.main --config config/local_pipeline.json``.

Doc LocalPipelineConfig, nghe phien giam sat cua lop tren Firestore va chi bat
camera khi phien dang chay trong cua so lich cua config. Xem docs/edge_node.md.
"""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from src.capture import CaptureWorker
from src.config import LocalConfigError, LocalPipelineConfig, load_class_seat_grid
from src.detection import PoseDetector
from src.logging_config import setup_logging
from src.pipeline import EdgeRuntime
from src.sync import FirestoreSink, firestore_client_from_env


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.main", description="Chay edge node camera-ai.")
    parser.add_argument("--config", type=Path, required=True, help="Config local JSON (config/README.md).")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = LocalPipelineConfig.from_json_file(args.config)
        capture_config = config.to_capture_config()  # bao loi som neu thieu bien moi truong nguon camera
    except LocalConfigError as error:
        print(f"Config khong hop le: {error}", file=sys.stderr)
        return 2

    setup_logging()
    camera, thresholds = config.camera, config.thresholds
    detector = PoseDetector(
        args.model,
        min_confidence=thresholds.pose_confidence,
        image_size=thresholds.image_size,
        iou_threshold=thresholds.iou_threshold,
        max_detections=thresholds.max_detections,
        tile_size=thresholds.tile_size,
        tile_overlap=thresholds.tile_overlap,
    )
    try:
        client = firestore_client_from_env()
        sink = FirestoreSink(client, camera.class_id, camera.camera_id, retention_days=config.privacy.retention_days)
        detector.open()
    except RuntimeError as error:  # thieu credential hoac model
        print(error, file=sys.stderr)
        return 1

    sink.start()
    runtime = EdgeRuntime(
        config,
        detector,
        lambda: load_class_seat_grid(client, camera.class_id, config.seating.corner_seats, camera.camera_id),
        sink,
        lambda: CaptureWorker(capture_config, buffer_size=config.privacy.frame_buffer_size),
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
