"""
face_detector.py -- Module detection/ (co ban): phat hien khuon mat trong khung
hinh bang MediaPipe Face Detector (Tasks API, model BlazeFace short-range).

Pham vi (Sprint 2, task 3): CHI phat hien vi tri khuon mat (bounding box) + 6
keypoint co ban (mat, mui, tai, khoe mieng) ma MediaPipe Face Detector tra ve
san. Landmark chi tiet (478 diem, dung cho head pose/EAR o Sprint 4) la task
rieng o Sprint 3 -- se nang cap len MediaPipe Face Landmarker luc do, theo dung
ke hoach da chot trong tai lieu nghien cuu Sprint 1.

QUAN TRONG -- can tai model thu cong truoc khi dung duoc module nay:
MediaPipe Face Detector khong dong goi san file model trong pip package. Xem
README.md trong thu muc nay de biet duong dan tai model.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

from .config import DetectionConfig

logger = logging.getLogger("camera_ai.detection")


@dataclass
class FaceBox:
    """Mot khuon mat phat hien duoc trong 1 khung hinh, toa do pixel tuyet doi
    (khong phai toa do chuan hoa 0-1) de de ghep voi khung hinh goc khi ve/debug."""

    x: int
    y: int
    width: int
    height: int
    confidence: float
    keypoints: List[Tuple[int, int]] = field(default_factory=list)


class FaceDetectorError(RuntimeError):
    """Nem ra khi khong khoi tao duoc FaceDetector (vi du thieu file model,
    hoac file model bi hong/sai dinh dang)."""


class FaceDetector:
    """Boc MediaPipe Face Detector (Tasks API) o che do VIDEO (dong bo -- phu
    hop voi vong lap 'pull' tu FrameBuffer cua module capture/).

    Cach dung:
        with FaceDetector(DetectionConfig.from_env()) as detector:
            faces = detector.detect(frame.image, frame.timestamp)
            for face in faces:
                print(face.x, face.y, face.width, face.height, face.confidence)
    """

    def __init__(self, config: DetectionConfig):
        self._config = config
        self._detector: Optional[vision.FaceDetector] = None
        self._last_timestamp_ms: Optional[int] = None

    # ------------------------------------------------------------------
    # Vong doi (lifecycle)
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Nap file model va khoi tao MediaPipe FaceDetector.

        Nem FaceDetectorError neu khong tim thay file model, hoac MediaPipe
        khong nap duoc model (vi du file hong/sai dinh dang).
        """
        if not os.path.exists(self._config.model_path):
            raise FaceDetectorError(
                f"Khong tim thay file model tai '{self._config.model_path}'. "
                "MediaPipe Face Detector can tai model thu cong -- xem "
                "README.md trong src/detection/ de biet duong dan tai."
            )

        try:
            options = vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=self._config.model_path),
                running_mode=vision.RunningMode.VIDEO,
                min_detection_confidence=self._config.min_detection_confidence,
                min_suppression_threshold=self._config.min_suppression_threshold,
            )
            self._detector = vision.FaceDetector.create_from_options(options)
        except FaceDetectorError:
            raise
        except Exception as e:  # mediapipe co the nem nhieu loai loi C++ khac nhau
            raise FaceDetectorError(
                f"Khong khoi tao duoc MediaPipe FaceDetector tu model "
                f"'{self._config.model_path}': {e}"
            ) from e

        self._last_timestamp_ms = None
        logger.info(
            "Da nap Face Detector tu '%s' (min_confidence=%.2f).",
            self._config.model_path, self._config.min_detection_confidence,
        )

    def close(self) -> None:
        if self._detector is not None:
            self._detector.close()
            self._detector = None

    def __enter__(self) -> "FaceDetector":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Phat hien khuon mat
    # ------------------------------------------------------------------

    def detect(self, image, timestamp: float) -> List[FaceBox]:
        """Phat hien khuon mat trong 1 khung hinh.

        image: numpy array BGR (dung dinh dang tra ve tu Frame.image cua
               module capture/ -- OpenCV doc anh mac dinh la BGR).
        timestamp: giay (float, tu Frame.timestamp cua capture/).

        Tra ve danh sach FaceBox (co the rong neu khong phat hien khuon mat nao).
        """
        if self._detector is None:
            raise RuntimeError("FaceDetector chua duoc mo. Goi open() truoc, hoac dung 'with'.")

        timestamp_ms = self._to_monotonic_ms(timestamp)

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        result = self._detector.detect_for_video(mp_image, timestamp_ms)
        height, width = image.shape[:2]
        return self._parse_result(result, width, height)

    def _to_monotonic_ms(self, timestamp: float) -> int:
        """MediaPipe che do VIDEO yeu cau timestamp (ms) TANG DAN NGHIEM NGAT.
        Ham nay bao ve truong hop dong ho he thong lech nho hoac 2 frame den
        trung/lech thu tu -- tranh MediaPipe nem loi 'timestamp must be
        monotonically increasing'."""
        timestamp_ms = int(timestamp * 1000)
        if self._last_timestamp_ms is not None and timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms

    @staticmethod
    def _parse_result(result, image_width: int, image_height: int) -> List[FaceBox]:
        """Chuyen FaceDetectorResult cua MediaPipe sang danh sach FaceBox.

        Luu y quan trong: 'bounding_box' cua MediaPipe la PIXEL TUYET DOI san,
        nhung 'keypoints' la toa do CHUAN HOA (0.0-1.0) theo chieu rong/cao anh
        -- can nhan voi image_width/image_height de doi ve pixel. Nham lan hai
        loai toa do nay la loi rat de mac (va de khong phat hien ra) khi dung
        MediaPipe Face Detector.
        """
        faces: List[FaceBox] = []
        for detection in result.detections:
            bbox = detection.bounding_box
            keypoints = [
                (int(kp.x * image_width), int(kp.y * image_height))
                for kp in (detection.keypoints or [])
            ]
            confidence = (
                detection.categories[0].score if detection.categories else 0.0
            )
            faces.append(
                FaceBox(
                    x=bbox.origin_x,
                    y=bbox.origin_y,
                    width=bbox.width,
                    height=bbox.height,
                    confidence=confidence,
                    keypoints=keypoints,
                )
            )
        return faces