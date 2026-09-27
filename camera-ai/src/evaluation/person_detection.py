"""Primitive danh gia person detection khong phu thuoc vao model hay dataset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class BoundingBox:
    """Toa do ``x1, y1, x2, y2`` cua mot nguoi trong mot anh."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class DetectionMetrics:
    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float:
        total = self.true_positive + self.false_positive
        return self.true_positive / total if total else 0.0

    @property
    def recall(self) -> float:
        """Ty le phat hien thanh cong tren nguoi co nhan that."""
        total = self.true_positive + self.false_negative
        return self.true_positive / total if total else 0.0

    @property
    def f1(self) -> float:
        total = self.precision + self.recall
        return 2 * self.precision * self.recall / total if total else 0.0


def iou(left: BoundingBox, right: BoundingBox) -> float:
    """Intersection-over-union cua hai bounding box."""
    inter_width = max(0.0, min(left.x2, right.x2) - max(left.x1, right.x1))
    inter_height = max(0.0, min(left.y2, right.y2) - max(left.y1, right.y1))
    intersection = inter_width * inter_height
    if not intersection:
        return 0.0
    left_area = max(0.0, left.x2 - left.x1) * max(0.0, left.y2 - left.y1)
    right_area = max(0.0, right.x2 - right.x1) * max(0.0, right.y2 - right.y1)
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def evaluate_boxes(predictions: Sequence[BoundingBox], ground_truth: Sequence[BoundingBox], iou_threshold: float = 0.5) -> DetectionMetrics:
    """Ghep tham lam prediction/GT theo IoU lon nhat, moi box chi ghep mot lan."""
    if not 0 < iou_threshold <= 1:
        raise ValueError("iou_threshold phai nam trong (0, 1].")
    candidates = sorted(((iou(prediction, truth), prediction_index, truth_index) for prediction_index, prediction in enumerate(predictions) for truth_index, truth in enumerate(ground_truth)), reverse=True)
    used_predictions: set[int] = set()
    used_truth: set[int] = set()
    for overlap, prediction_index, truth_index in candidates:
        if overlap < iou_threshold:
            break
        if prediction_index not in used_predictions and truth_index not in used_truth:
            used_predictions.add(prediction_index)
            used_truth.add(truth_index)
    true_positive = len(used_predictions)
    return DetectionMetrics(true_positive, len(predictions) - true_positive, len(ground_truth) - true_positive)


def combine_metrics(metrics: Iterable[DetectionMetrics]) -> DetectionMetrics:
    """Cong metric cua nhieu anh de bao cao theo nhom."""
    values = list(metrics)
    return DetectionMetrics(sum(item.true_positive for item in values), sum(item.false_positive for item in values), sum(item.false_negative for item in values))
