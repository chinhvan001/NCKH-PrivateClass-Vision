"""
Module capture/ -- doc khung hinh camera voi cau hinh FPS/do phan giai, tu dong
ket noi lai khi mat ket noi tam thoi, va cung cap FrameBuffer + CaptureWorker
de chay nen tren thread rieng khong block cac module tieu thu (detection/...).
"""
 
from .camera_capture import CameraCapture, CameraOpenError, Frame
from .capture_worker import CaptureWorker
from .config import CaptureConfig
from .frame_buffer import FrameBuffer
 
__all__ = [
    "CameraCapture",
    "CameraOpenError",
    "Frame",
    "CaptureConfig",
    "FrameBuffer",
    "CaptureWorker",
]
 