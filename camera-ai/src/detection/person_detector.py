"""Detector nguoi tong quat, tach khoi pose de tang coverage trong lop dong."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger("camera_ai.detection")


@dataclass(frozen=True)
class PersonBox:
    """Box nguoi tam thoi trong RAM; khong phai dinh danh ca nhan."""

    bbox: Tuple[float, float, float, float]
    confidence: float


class PersonDetectorError(RuntimeError):
    pass


class PersonDetector:
    """YOLO object-detection cho class ``person`` (COCO 0).

    Khac voi pose, model nay khong doi hoi phai thay du 17 keypoint. Vi vay no
    phu hop de dem/bao phu hoc sinh ngoi bi ban che; PersonBox khong duoc xuat
    ra khoi pipeline va khong duoc dung de nhan dang danh tinh.
    """

    def __init__(
        self,
        model_path: str = "models/yolo11s.pt",
        min_confidence: float = 0.15,
        image_size: int = 960,
        iou_threshold: float = 0.7,
        max_detections: int = 100,
    ) -> None:
        if not 0 < min_confidence <= 1 or not 0 < iou_threshold <= 1:
            raise ValueError("confidence va iou_threshold phai nam trong (0, 1].")
        if image_size <= 0 or max_detections <= 0:
            raise ValueError("image_size va max_detections phai > 0.")
        self._model_path = model_path
        self._min_confidence = min_confidence
        self._image_size = image_size
        self._iou_threshold = iou_threshold
        self._max_detections = max_detections
        self._model = None

    def open(self) -> None:
        try:
            from ultralytics import YOLO
            self._model = YOLO(self._model_path)
        except Exception as error:
            raise PersonDetectorError(
                f"Khong nap duoc person detector '{self._model_path}': {error}"
            ) from error
        logger.info("Da nap PersonDetector '%s' (conf=%.2f, imgsz=%d).", self._model_path, self._min_confidence, self._image_size)

    def close(self) -> None:
        self._model = None

    def detect(self, image_bgr) -> List[PersonBox]:
        if self._model is None:
            raise RuntimeError("PersonDetector chua duoc mo.")
        result = self._model.predict(
            image_bgr,
            classes=[0],  # COCO class 0 = person
            conf=self._min_confidence,
            iou=self._iou_threshold,
            imgsz=self._image_size,
            max_det=self._max_detections,
            verbose=False,
        )[0]
        if result.boxes is None:
            return []
        return [
            PersonBox(tuple(float(value) for value in bbox), float(confidence))
            for bbox, confidence in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist())
        ]

    def __enter__(self) -> "PersonDetector":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
