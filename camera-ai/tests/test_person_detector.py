"""Test parse/guard cua person detector, khong can model that."""

import pytest

from src.detection.person_detector import PersonDetector


def test_rejects_invalid_inference_thresholds():
    with pytest.raises(ValueError):
        PersonDetector(min_confidence=0)
    with pytest.raises(ValueError):
        PersonDetector(iou_threshold=1.1)


def test_detect_requires_open_model():
    with pytest.raises(RuntimeError, match="chua duoc mo"):
        PersonDetector().detect(object())
