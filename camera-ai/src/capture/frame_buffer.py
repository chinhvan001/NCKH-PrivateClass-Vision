"""
frame_buffer.py -- Bo dem (buffer) khung hinh giua capture/ va cac module tieu
thu phia sau (detection/...).

Thiet ke co chu dich: bounded queue, khi day thi TU DONG LOAI BO khung hinh CU
NHAT de nhuong cho khung hinh MOI (drop-oldest) -- khac voi hang doi cong viec
thong thuong (job queue) can dam bao "khong mat item nao".

Ly do chon drop-oldest cho pipeline video thoi gian thuc: neu detection/ xu ly
cham hon capture/, dieu quan trong la luon co khung hinh MOI NHAT de phan tich
muc do tap trung, khong phai xu ly du 100% khung hinh da qua (mot khung hinh
engagement bi tre vai giay khong con nhieu gia tri). Neu dung hang doi block
thong thuong, capture/ se bi nghen theo toc do cham nhat cua detection/, gay
tre (latency) tich luy ngay cang lon theo thoi gian.
"""

import logging
import queue
import threading
from typing import Optional

from .camera_capture import Frame

logger = logging.getLogger("camera_ai.capture.buffer")


class FrameBuffer:
    """Bo dem khung hinh thread-safe, bounded, chien luoc drop-oldest khi day."""

    def __init__(self, maxsize: int = 5):
        if maxsize < 1:
            raise ValueError("maxsize phai >= 1")
        self._queue: "queue.Queue[Frame]" = queue.Queue(maxsize=maxsize)
        self._dropped_count = 0
        self._lock = threading.Lock()

    def put(self, frame: Frame) -> None:
        """Them mot khung hinh vao buffer. Khong bao gio block: neu buffer day,
        loai bo khung hinh CU NHAT dang cho de nhuong cho khung hinh moi nay."""
        try:
            self._queue.put_nowait(frame)
            return
        except queue.Full:
            pass

        try:
            self._queue.get_nowait()  # bo khung hinh cu nhat de lay cho
            with self._lock:
                self._dropped_count += 1
        except queue.Empty:
            pass  # hiem: thread khac vua lay het trong luc nay, khong sao

        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            # Rat hiem: race condition giua nhieu producer chen vao dung luc.
            # Bo qua khung hinh nay thay vi block hoac raise loi.
            with self._lock:
                self._dropped_count += 1
            logger.debug("Bo qua 1 khung hinh do race condition khi buffer day.")

    def get(self, timeout: Optional[float] = None) -> Optional[Frame]:
        """Lay khung hinh tiep theo, cho toi da `timeout` giay.

        Tra ve None neu het timeout ma khong co khung hinh nao -- khong raise
        exception, de vong lap tieu thu code don gian (kiem tra None thay vi
        try/except queue.Empty o moi noi goi).
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def qsize(self) -> int:
        """So khung hinh dang cho trong buffer (uoc luong, co the lech nho do
        thread khac dang thao tac dong thoi -- chi dung de giam sat, khong dung
        de dieu khien logic chinh xac)."""
        return self._queue.qsize()

    @property
    def dropped_count(self) -> int:
        """Tong so khung hinh da bi loai bo do buffer day tu luc khoi tao --
        huu ich de giam sat xem detection/ co dang xu ly kip capture/ khong.
        So nay tang lien tuc neu detection/ qua cham so voi target_fps cua
        capture/, la dau hieu can giam FPS hoac toi uu detection/.
        """
        with self._lock:
            return self._dropped_count