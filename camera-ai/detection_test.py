"""Script preview pose da an danh: capture/ + PoseDetector.

Khong su dung face detector, facial landmark hay embedding. Preview da duoc
pixelate truoc khi hien thi va frame goc chi ton tai trong RAM trong luc
inference.

Cach chay (tu thu muc camera-ai/, da activate venv):
    python detection_test.py

Phim tat: q hoac ESC de thoat.
"""

import logging
import sys

import cv2

from src.capture import CameraOpenError, CaptureConfig, CaptureWorker
from src.detection import PoseDetector, PoseDetectorError
from src.logging_config import setup_logging
from src.privacy import anonymize_preview, wipe_image

setup_logging()
logger = logging.getLogger("camera_ai.detection_test")


def draw_person(image, person) -> None:
    x1, y1, x2, y2 = (round(value) for value in person.bbox)
    cv2.rectangle(
        image, (x1, y1), (x2, y2),
        (0, 255, 0), 2,
    )
    cv2.putText(
        image, f"{person.confidence:.2f}", (x1, max(y1 - 8, 0)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
    )


def main():
    capture_config = CaptureConfig.from_env()
    worker = CaptureWorker(capture_config)
    try:
        worker.start()
    except CameraOpenError as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        detector = PoseDetector()
        detector.open()
    except PoseDetectorError as e:
        logger.error(str(e))
        worker.stop()
        sys.exit(1)

    print("Nhan 'q' hoac ESC de thoat.")
    display_fps = 0.0
    prev_timestamp = None

    try:
        while True:
            frame = worker.buffer.get(timeout=1.0)
            if frame is None:
                continue

            if prev_timestamp is not None:
                elapsed = frame.timestamp - prev_timestamp
                if elapsed > 0:
                    display_fps = 0.9 * display_fps + 0.1 * (1.0 / elapsed)
            prev_timestamp = frame.timestamp

            people = detector.detect(frame.image)
            # Inference dung frame goc; chi tao ban sao da an danh cho preview.
            image = frame.image.copy()
            anonymize_preview(image, people)
            for person in people:
                draw_person(image, person)

            overlay = (
                f"People: {len(people)}  |  FPS: {display_fps:.1f}  |  "
                f"Dropped: {worker.buffer.dropped_count}  |  q/ESC de thoat"
            )
            cv2.putText(
                image, overlay, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2,
            )
            cv2.imshow("camera-ai - Test detection/ (Sprint 2)", image)

            key = cv2.waitKey(1) & 0xFF
            wipe_image(image)
            wipe_image(frame.image)
            if key == ord("q") or key == 27:
                logger.info("Nguoi dung yeu cau thoat.")
                break

    except KeyboardInterrupt:
        logger.info("Da nhan Ctrl+C, dang thoat...")

    finally:
        if "image" in locals():
            wipe_image(image)
        if "frame" in locals():
            wipe_image(frame.image)
        detector.close()
        worker.stop()
        cv2.destroyAllWindows()
        logger.info("Da dong detector, capture worker, va cua so hien thi.")


if __name__ == "__main__":
    main()
