"""Danh gia detector bang nhan ground-truth, khong luu khung hinh."""

from .person_detection import BoundingBox, DetectionMetrics, evaluate_boxes, iou

__all__ = ["BoundingBox", "DetectionMetrics", "evaluate_boxes", "iou"]
