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


@dataclass
class LandmarkerConfig:
    """Cau hinh cho FaceLandmarker (MediaPipe Face Landmarker, Tasks API).

    Khac voi Face Detector (dung 1 file .tflite don), Face Landmarker dung
    file .task (mot bundle dong goi nhieu model con: phat hien mat, landmark,
    tuy chon blendshape) -- xem README.md de biet duong dan tai model nay.

    LUU Y QUAN TRONG: mac dinh cua MediaPipe la num_faces=1 (toi uu cho ung
    dung kieu selfie/1 nguoi). Vi lop hoc co NHIEU hoc sinh, max_num_faces o
    day duoc dat mac dinh 30 -- neu quen chinh lai gia tri nay, module se chi
    bao gio phat hien duoc 1 khuon mat duy nhat trong ca lop.
    """

    model_path: str = "models/face_landmarker.task"
    max_num_faces: int = 30
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    output_transformation_matrix: bool = True

    @classmethod
    def from_env(cls) -> "LandmarkerConfig":
        """Doc cau hinh tu bien moi truong (.env), dung gia tri mac dinh neu thieu.

        Bien moi truong ho tro:
            FACE_LANDMARKER_MODEL_PATH                 -- duong dan file .task da tai ve
            FACE_LANDMARKER_MAX_FACES                  -- so khuon mat toi da moi khung hinh
            FACE_LANDMARKER_MIN_DETECTION_CONFIDENCE   -- nguong phat hien mat (0.0-1.0)
            FACE_LANDMARKER_MIN_PRESENCE_CONFIDENCE    -- nguong "con hien dien" (0.0-1.0)
            FACE_LANDMARKER_MIN_TRACKING_CONFIDENCE    -- nguong tracking giua cac frame (0.0-1.0)
            FACE_LANDMARKER_OUTPUT_MATRIX              -- "1"/"0" bat/tat xuat transformation matrix
        """
        default = cls()
        return cls(
            model_path=os.getenv("FACE_LANDMARKER_MODEL_PATH", default.model_path),
            max_num_faces=int(
                os.getenv("FACE_LANDMARKER_MAX_FACES", str(default.max_num_faces))
            ),
            min_detection_confidence=float(
                os.getenv(
                    "FACE_LANDMARKER_MIN_DETECTION_CONFIDENCE",
                    str(default.min_detection_confidence),
                )
            ),
            min_presence_confidence=float(
                os.getenv(
                    "FACE_LANDMARKER_MIN_PRESENCE_CONFIDENCE",
                    str(default.min_presence_confidence),
                )
            ),
            min_tracking_confidence=float(
                os.getenv(
                    "FACE_LANDMARKER_MIN_TRACKING_CONFIDENCE",
                    str(default.min_tracking_confidence),
                )
            ),
            output_transformation_matrix=os.getenv(
                "FACE_LANDMARKER_OUTPUT_MATRIX", "1"
            ).lower()
            not in ("0", "false", ""),
        )