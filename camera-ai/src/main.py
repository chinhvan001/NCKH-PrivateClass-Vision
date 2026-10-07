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
from src.config import (
    FirestoreSeatGridSource,
    LocalConfigError,
    LocalPipelineConfig,
    RuntimeConfigPoller,
    SeatGridResolver,
)
from src.detection import PoseDetector
from src.logging_config import setup_logging
from src.pipeline import EdgeRuntime
from src.sync import FirestoreSink, firestore_client_from_env


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.main", description="Chay edge node camera-ai.")
    parser.add_argument("--config", type=Path, required=True, help="Config local JSON (config/README.md).")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    parser.add_argument("--seats", type=Path, help="Seat grid JSON du phong khi chua doc duoc tu Firestore.")
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
    poller = RuntimeConfigPoller(
        SeatGridResolver(FirestoreSeatGridSource(), camera.camera_id, camera.classroom_id, args.seats), detector
    )
    try:
        sink = FirestoreSink(firestore_client_from_env(), camera.classroom_id, camera.camera_id)
        detector.open()
        poller.start()  # nap seat grid lan dau: Firestore, hoac file --seats
    except RuntimeError as error:  # thieu credential, model hoac seat grid
        print(error, file=sys.stderr)
        return 1

    sink.start()
    runtime = EdgeRuntime(
        config,
        detector,
        poller.snapshot,
        sink,
        lambda: CaptureWorker(capture_config, buffer_size=config.privacy.frame_buffer_size),
    )
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # dung service -> van chay cac khoi finally
    try:
        runtime.run(sink.watch_sessions)
    except KeyboardInterrupt:
        pass
    finally:
        poller.stop()
        sink.close()
        detector.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
