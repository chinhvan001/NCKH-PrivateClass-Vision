"""
detection_test.py -- Script kiem tra truc quan tich hop capture/ + detection/

Muc dich: xac nhan FaceDetector hoat dong dung tren luong camera thuc (qua
CaptureWorker + FrameBuffer), ve bounding box + keypoint len man hinh de kiem
tra bang mat.

QUAN TRONG: can tai file model MediaPipe truoc khi chay -- xem
src/detection/README.md.

Cach chay (tu thu muc camera-ai/, da activate venv):
    python detection_test.py

Phim tat: q hoac ESC de thoat.
"""

import logging
import sys

import cv2

from src.capture import CameraOpenError, CaptureConfig, CaptureWorker
from src.detection import DetectionConfig, FaceDetector, FaceDetectorError
from src.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("camera_ai.detection_test")


def draw_face(image, face) -> None:
    cv2.rectangle(
        image, (face.x, face.y), (face.x + face.width, face.y + face.height),
        (0, 255, 0), 2,
    )
    cv2.putText(
        image, f"{face.confidence:.2f}", (face.x, max(face.y - 8, 0)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
    )
    for kp in face.keypoints:
        cv2.circle(image, kp, 3, (0, 0, 255), -1)


def main():
    capture_config = CaptureConfig.from_env()
    detection_config = DetectionConfig.from_env()

    worker = CaptureWorker(capture_config)
    try:
        worker.start()
    except CameraOpenError as e:
        logger.error(str(e))
        sys.exit(1)

    try:
        detector = FaceDetector(detection_config)
        detector.open()
    except FaceDetectorError as e:
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

            faces = detector.detect(frame.image, frame.timestamp)
            image = frame.image
            for face in faces:
                draw_face(image, face)

            overlay = (
                f"Faces: {len(faces)}  |  FPS: {display_fps:.1f}  |  "
                f"Dropped: {worker.buffer.dropped_count}  |  q/ESC de thoat"
            )
            cv2.putText(
                image, overlay, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2,
            )
            cv2.imshow("camera-ai - Test detection/ (Sprint 2)", image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                logger.info("Nguoi dung yeu cau thoat.")
                break

    except KeyboardInterrupt:
        logger.info("Da nhan Ctrl+C, dang thoat...")

    finally:
        detector.close()
        worker.stop()
        cv2.destroyAllWindows()
        logger.info("Da dong detector, capture worker, va cua so hien thi.")


if __name__ == "__main__":
    main()