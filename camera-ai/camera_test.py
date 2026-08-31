"""
camera_test.py -- Script kiem tra thu cong module capture/ (Sprint 2)

Day la ban thay the cho capture_test.py o Sprint 1: thay vi tu goi cv2.VideoCapture
truc tiep, script nay dung CameraCapture/CaptureConfig cua module capture/ da xay
o Sprint 2 -- vua de kiem tra truc quan module hoat dong dung, vua la vi du cach
dung module cho cac module khac (detection/...) tham khao sau nay.

Muc dich kiem tra truc quan:
    - Camera mo dung theo cau hinh FPS/do phan giai tu .env
    - FPS thuc te hien thi gan voi target_fps da cau hinh (throttle hoat dong dung)
    - Neu rut camera ra giua chung, module tu ket noi lai ma script khong bi crash
      (dung de test thu UC-CAM-01 -- luong phu/luong ngoai le)

Cach chay (tu thu muc camera-ai/, sau khi da activate venv):
    python camera_test.py

Phim tat khi cua so dang mo:
    q hoac ESC  -> thoat chuong trinh

Cau hinh qua .env (xem CaptureConfig.from_env trong src/capture/config.py):
    CAMERA_SOURCE, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
"""

import logging
import sys

import cv2

from src.capture import CameraCapture, CameraOpenError, CaptureConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("camera_test")


def main():
    config = CaptureConfig.from_env()
    logger.info(
        "Cau hinh doc tu .env: source=%r, width=%s, height=%s, target_fps=%.1f",
        config.source, config.width, config.height, config.target_fps,
    )

    cam = CameraCapture(config)
    try:
        cam.open()
    except CameraOpenError as e:
        logger.error(str(e))
        sys.exit(1)

    print("Nhan 'q' hoac ESC trong cua so hien thi de thoat.")
    print("Co the thu rut camera ra giua chung de kiem tra module tu ket noi lai.")

    display_fps = 0.0
    prev_timestamp = None

    try:
        for frame in cam.frames():
            # Tinh FPS hien thi thuc te tu timestamp cua frame (khac target_fps da
            # cau hinh) -- de kiem tra bang mat throttle cua module capture/ co dung
            # nhu ky vong khong, khong chi tin vao code.
            if prev_timestamp is not None:
                elapsed = frame.timestamp - prev_timestamp
                if elapsed > 0:
                    display_fps = 0.9 * display_fps + 0.1 * (1.0 / elapsed)
            prev_timestamp = frame.timestamp

            image = frame.image
            overlay = (
                f"Frame #{frame.frame_index}  |  FPS thuc te: {display_fps:.1f}"
                f" (target: {config.target_fps:.1f})  |  q/ESC de thoat"
            )
            cv2.putText(
                image, overlay, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2,
            )

            cv2.imshow("camera-ai - Test module capture/ (Sprint 2)", image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 27 = phim ESC
                logger.info("Nguoi dung yeu cau thoat.")
                break

    except KeyboardInterrupt:
        logger.info("Da nhan Ctrl+C, dang thoat...")

    finally:
        cam.close()
        cv2.destroyAllWindows()
        logger.info("Da dong module capture/ va cua so hien thi.")


if __name__ == "__main__":
    main()