"""
config.py -- Cau hinh cho module detection/
"""

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class DetectionConfig:
    """Cau hinh cho FaceDetector (MediaPipe Face Detector, Tasks API).

    model_path phai tro toi file model MediaPipe Face Detector da tai ve THU
    CONG truoc -- thu vien mediapipe khong tu dong tai model qua mang. Xem
    README.md trong thu muc nay de biet duong dan tai model.
    """

    model_path: str = "models/blaze_face_short_range.tflite"
    min_detection_confidence: float = 0.5
    min_suppression_threshold: float = 0.3

    @classmethod
    def from_env(cls) -> "DetectionConfig":
        """Doc cau hinh tu bien moi truong (.env), dung gia tri mac dinh neu thieu.

        Bien moi truong ho tro:
            FACE_DETECTOR_MODEL_PATH      -- duong dan toi file model da tai ve
            FACE_DETECTOR_MIN_CONFIDENCE  -- nguong tin cay toi thieu (0.0-1.0)
        """
        default = cls()
        return cls(
            model_path=os.getenv("FACE_DETECTOR_MODEL_PATH", default.model_path),
            min_detection_confidence=float(
                os.getenv("FACE_DETECTOR_MIN_CONFIDENCE", str(default.min_detection_confidence))
            ),
        )