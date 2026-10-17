"""
Module detection/ -- chi phat hien pose da nguoi (YOLOv8-pose), khong export
API face detector/face landmarker. Pipeline hien tai khong su dung khuon mat,
facial landmark hay embedding de tranh dua du lieu sinh trac hoc vao luong AI.
"""

from .pose_detector import (
    COCO_KEYPOINT_NAMES,
    PersonPose,
    PoseDetector,
    PoseDetectorError,
)
from .person_detector import PersonBox, PersonDetector, PersonDetectorError

__all__ = [
    # Huong hien tai (skeleton/pose-based)
    "PoseDetector",
    "PoseDetectorError",
    "PersonPose",
    "COCO_KEYPOINT_NAMES",
    "PersonBox",
    "PersonDetector",
    "PersonDetectorError",
]
