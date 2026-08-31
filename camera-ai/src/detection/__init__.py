"""
Module detection/ -- phat hien khuon mat co ban trong khung hinh bang MediaPipe
Face Detector (Tasks API). Xem README.md de biet cach tai model can thiet.
"""

from .config import DetectionConfig
from .face_detector import FaceBox, FaceDetector, FaceDetectorError

__all__ = ["DetectionConfig", "FaceBox", "FaceDetector", "FaceDetectorError"]