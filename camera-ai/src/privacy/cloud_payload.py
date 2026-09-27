"""Allowlist payload duy nhat duoc phep roi pipeline len Cloud."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


class CloudPayloadError(ValueError):
    pass


@dataclass(frozen=True)
class CloudEngagementPayload:
    """Payload toi thieu: vi tri ghe, toa do keypoint, diem engagement.

    Khong co anh, crop, bbox, confidence, face feature, track ID, timestamp,
    ten hay ma hoc sinh. ``seat_id`` chi la vi tri da calibrate trong phong.
    """

    seat_id: str
    keypoints: tuple[tuple[float, float], ...]
    engagement_score: float | None

    def to_dict(self) -> dict:
        return {
            "seat_id": self.seat_id,
            "keypoints": [[x, y] for x, y in self.keypoints],
            "engagement_score": self.engagement_score,
        }


def make_cloud_payload(seat_id: str, keypoints: Iterable[tuple[float, float]], engagement_score: float | None) -> CloudEngagementPayload:
    if not isinstance(seat_id, str) or not seat_id.strip():
        raise CloudPayloadError("seat_id phai la chuoi khong rong.")
    normalized = []
    for index, point in enumerate(keypoints):
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise CloudPayloadError(f"keypoints[{index}] phai la [x, y].")
        x, y = float(point[0]), float(point[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise CloudPayloadError(f"keypoints[{index}] phai la so huu han.")
        normalized.append((round(x, 2), round(y, 2)))
    if engagement_score is not None:
        engagement_score = float(engagement_score)
        if not math.isfinite(engagement_score) or not 0 <= engagement_score <= 100:
            raise CloudPayloadError("engagement_score phai nam trong [0, 100] hoac null.")
        engagement_score = round(engagement_score, 2)
    return CloudEngagementPayload(seat_id.strip(), tuple(normalized), engagement_score)
