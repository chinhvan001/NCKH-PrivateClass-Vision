"""
camera_capture.py -- Module capture/ cho camera-ai

Chiu trach nhiem doc khung hinh tu camera lop hoc, ap dung cau hinh FPS/do phan
giai, va tu dong ket noi lai khi camera bi ngat tam thoi. Day la lop nen tang
cho pipeline capture -> detection -> engagement -> privacy -> sync.

Tham chieu: UC-CAM-01 (UC Specification) va US-CAM-01 (User Stories) mo ta day
du Acceptance Criteria ma module nay can dap ung.

Luu y pham vi (Sprint 2, task 1): module nay CHI phu trach doc camera + throttle
FPS + tu ket noi lai. Buffer/queue giua capture va detection la task rieng
(Sprint 2, task 2) va se bao boc generator frames() o duoi day.
"""

import logging
import time
from typing import Iterator, NamedTuple, Optional

import cv2

from .config import CaptureConfig

logger = logging.getLogger("camera_ai.capture")


class Frame(NamedTuple):
    """Mot khung hinh da doc duoc, kem metadata can thiet cho cac buoc xu ly sau."""

    image: "cv2.Mat"
    timestamp: float
    frame_index: int


class CameraOpenError(RuntimeError):
    """Nem ra khi khong the mo duoc camera voi nguon da cau hinh (loi khoi tao).

    Khac voi mat ket noi giua chung trong luc chay (duoc tu xu ly ben trong
    read(), khong nem exception ra ngoai -- xem _handle_read_failure()).
    """


class CameraCapture:
    """Doc khung hinh tu camera theo FPS/do phan giai da cau hinh, tu dong ket
    noi lai khi camera bi ngat tam thoi.

    Cach dung co ban:

        config = CaptureConfig.from_env()
        with CameraCapture(config) as cam:
            for frame in cam.frames():
                ...  # xu ly frame.image (numpy array, BGR)
    """

    def __init__(self, config: CaptureConfig):
        self._config = config
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_index = 0
        self._consecutive_failures = 0
        self._is_open = False

    # ------------------------------------------------------------------
    # Vong doi (lifecycle)
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Mo ket noi camera va ap dung cau hinh do phan giai.

        Nem CameraOpenError neu khong mo duoc camera ngay tu dau.
        """
        logger.info("Dang mo camera voi source=%r", self._config.source)
        self._cap = cv2.VideoCapture(self._config.source)
        self._apply_resolution()

        if not self._cap.isOpened():
            self._cap = None
            raise CameraOpenError(
                f"Khong mo duoc camera voi source={self._config.source!r}. "
                "Kiem tra lai CAMERA_SOURCE, quyen truy cap camera, hoac camera "
                "co dang bi ung dung khac chiem dung khong."
            )

        self._is_open = True
        self._consecutive_failures = 0
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(
            "Camera da mo thanh cong. Do phan giai thuc te: %dx%d, FPS muc tieu: %.1f",
            actual_w, actual_h, self._config.target_fps,
        )

    def close(self) -> None:
        """Giai phong camera. An toan khi goi nhieu lan hoac khi camera chua mo."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_open = False
        logger.info("Da giai phong camera.")

    def __enter__(self) -> "CameraCapture":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return self._is_open

    # ------------------------------------------------------------------
    # Doc khung hinh
    # ------------------------------------------------------------------

    def read(self) -> Optional[Frame]:
        """Doc mot khung hinh don le. Tra ve None neu doc that bai (da tu dong
        thu ket noi lai ben trong ham nay theo co che backoff).

        Khong throttle theo FPS o day -- dung frames() cho vong lap co throttle.
        """
        if self._cap is None:
            raise RuntimeError("Camera chua duoc mo. Goi open() truoc, hoac dung cau truc 'with'.")

        ret, image = self._cap.read()

        if not ret or image is None:
            return self._handle_read_failure()

        self._consecutive_failures = 0
        self._frame_index += 1
        return Frame(image=image, timestamp=time.time(), frame_index=self._frame_index)

    def frames(self) -> Iterator[Frame]:
        """Generator doc khung hinh lien tuc, tu throttle theo target_fps da cau hinh.

        Day la cach dung chinh cho vong lap xu ly (module detection/ se lap qua
        generator nay, hoac buffer/queue cua task tiep theo se bao boc no).
        """
        frame_interval = 1.0 / self._config.target_fps if self._config.target_fps > 0 else 0.0
        next_read_time = time.time()

        while True:
            frame = self.read()
            if frame is not None:
                yield frame

            next_read_time += frame_interval
            sleep_for = next_read_time - time.time()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                # Xu ly cham hon frame_interval -- khong ngu, tranh don tich luy do tre.
                next_read_time = time.time()

    # ------------------------------------------------------------------
    # Xu ly mat ket noi & tu ket noi lai (UC-CAM-01, luong phu / luong ngoai le)
    # ------------------------------------------------------------------

    def _handle_read_failure(self) -> Optional[Frame]:
        self._consecutive_failures += 1
        logger.warning(
            "Doc khung hinh that bai (lan thu %d lien tiep).", self._consecutive_failures
        )

        if self._consecutive_failures == self._config.max_consecutive_failures_before_alert:
            logger.error(
                "Camera mat ket noi keo dai (%d lan doc lien tiep that bai). "
                "Can lop goi ben ngoai xu ly canh bao (xem UC-CAM-08, chua trien "
                "khai trong module capture/ nay).",
                self._consecutive_failures,
            )

        self._attempt_reconnect()
        return None

    def _attempt_reconnect(self) -> None:
        delay = min(
            self._config.reconnect_initial_delay
            * (self._config.reconnect_backoff_factor ** min(self._consecutive_failures - 1, 6)),
            self._config.reconnect_max_delay,
        )
        logger.info("Thu ket noi lai camera sau %.1fs...", delay)
        time.sleep(delay)

        if self._cap is not None:
            self._cap.release()

        self._cap = cv2.VideoCapture(self._config.source)
        self._apply_resolution()

        if self._cap.isOpened():
            logger.info("Ket noi lai camera thanh cong.")
            self._consecutive_failures = 0
        else:
            logger.warning("Ket noi lai camera chua thanh cong, se thu lai o lan doc tiep theo.")

    # ------------------------------------------------------------------
    # Cau hinh dong (module config/ o Sprint 7 se goi apply_config khi Admin
    # doi cau hinh tu xa -- UC-CAM-05)
    # ------------------------------------------------------------------

    def apply_config(self, new_config: CaptureConfig) -> None:
        """Ap dung cau hinh moi ma khong can tao lai doi tuong CameraCapture.

        Neu nguon camera (source) thay doi, camera se duoc mo lai. Neu chi FPS/do
        phan giai thay doi, ap dung truc tiep len ket noi hien tai.
        """
        source_changed = new_config.source != self._config.source
        self._config = new_config

        if source_changed and self._is_open:
            logger.info("CAMERA_SOURCE thay doi -- mo lai camera voi nguon moi.")
            self.close()
            self.open()
        elif self._is_open:
            self._apply_resolution()
            logger.info(
                "Da ap dung cau hinh moi: fps=%.1f, resolution=%sx%s",
                new_config.target_fps, new_config.width, new_config.height,
            )

    def _apply_resolution(self) -> None:
        if self._cap is None:
            return
        if self._config.width:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
        if self._config.height:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)


if __name__ == "__main__":
    # Chay truc tiep file nay de kiem tra nhanh module capture/:
    #     python -m src.capture.camera_capture
    # Khong thay the cho unit test chinh thuc (task rieng o Sprint 2).
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    cfg = CaptureConfig.from_env()
    with CameraCapture(cfg) as cam:
        print("Nhan Ctrl+C de dung.")
        start = time.time()
        count = 0
        try:
            for frame in cam.frames():
                count += 1
                if count % 30 == 0:
                    elapsed = time.time() - start
                    print(f"Da doc {count} khung hinh, FPS trung binh: {count / elapsed:.1f}")
        except KeyboardInterrupt:
            print(f"\nDung lai. Tong cong doc duoc {count} khung hinh.")