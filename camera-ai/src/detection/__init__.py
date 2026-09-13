"""
Module detection/ -- phat hien nguoi/pose (PoseDetector, YOLOv8-pose -- huong
chinh thuc hien tai) va cac lop facial cu (FaceDetector, FaceLandmarker -- da
NGUNG DUNG sau khi pivot sang skeleton/pose-based, giu lai chi de tham khao
lich su code). Xem Algorithm-Pivot-Proposal.docx (04/09/2026) va README.md de
biet chi tiet quyet dinh pivot va cach tai model.
"""

from .config import DetectionConfig, LandmarkerConfig
from .face_detector import FaceBox, FaceDetector, FaceDetectorError
from .face_landmarker import FaceLandmarker, FaceLandmarkerError, FaceLandmarks
from .pose_detector import (
    COCO_KEYPOINT_NAMES,
    PersonPose,
    PoseDetector,
    PoseDetectorError,
)

__all__ = [
    # Huong hien tai (skeleton/pose-based)
    "PoseDetector",
    "PoseDetectorError",
    "PersonPose",
    "COCO_KEYPOINT_NAMES",
    # Huong cu (facial, da ngung dung -- giu lai de tham khao)
    "DetectionConfig",
    "FaceBox",
    "FaceDetector",
    "FaceDetectorError",
    "LandmarkerConfig",
    "FaceLandmarker",
    "FaceLandmarkerError",
    "FaceLandmarks",
]