"""
capture_worker.py -- Chay CameraCapture tren mot thread rieng (nen), day khung
hinh vao FrameBuffer de cac module tieu thu (detection/...) doc ma khong bi
block boi toc do doc camera hay bi cham di khi detection/ xu ly lau.
"""

import logging
import threading
from typing import Optional

from .camera_capture import CameraCapture
from .config import CaptureConfig
from .frame_buffer import FrameBuffer

logger = logging.getLogger("camera_ai.capture.worker")


class CaptureWorker:
    """Boc CameraCapture chay nen tren 1 thread, day khung hinh vao FrameBuffer.

    Cach dung:

        config = CaptureConfig.from_env()
        worker = CaptureWorker(config, buffer_size=5)
        worker.start()  # nem CameraOpenError ngay tai day neu khong mo duoc camera
        try:
            while True:
                frame = worker.buffer.get(timeout=1.0)
                if frame is not None:
                    ...  # xu ly frame (vi du: day sang detection/)
        finally:
            worker.stop()
    """

    def __init__(self, config: CaptureConfig, buffer_size: int = 5):
        self._config = config
        self.buffer = FrameBuffer(maxsize=buffer_size)
        self._cam = CameraCapture(config)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Mo camera (dong bo -- de CameraOpenError nem ra ngay tai day, khong
        bi 'nuot' am tham trong thread nen) roi bat thread doc khung hinh."""
        self._cam.open()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="capture-worker", daemon=True)
        self._thread.start()
        logger.info("Da khoi dong capture worker (thread nen).")

    def stop(self, timeout: float = 5.0) -> None:
        """Dung thread doc khung hinh va giai phong camera. An toan goi nhieu lan
        (kem ca khi start() chua tung duoc goi)."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(
                    "Capture worker khong dung kip trong %.1fs (co the target_fps "
                    "qua thap khien vong lap dang ngu lau).", timeout,
                )
            self._thread = None
        self._cam.close()
        logger.info(
            "Da dung capture worker. Tong so khung hinh bi drop do buffer day: %d",
            self.buffer.dropped_count,
        )

    @property
    def is_alive(self) -> bool:
        """True neu thread nen dang chay binh thuong -- dung de giam sat suc
        khoe worker (vi du tu mot vong lap supervisor ben ngoai)."""
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        try:
            for frame in self._cam.frames():
                if self._stop_event.is_set():
                    break
                self.buffer.put(frame)
        except Exception:
            logger.exception(
                "Capture worker gap loi khong mong doi, thread nen dang dung lai. "
                "Kiem tra is_alive de phat hien truong hop nay."
            )
            