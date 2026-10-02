"""Schema xuat engagement toi thieu, khong chua du lieu sinh trac hoc."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from src.engagement.engagement_score import EngagementScore


@dataclass(frozen=True)
class AnonymizedEngagementRecord:
    """Ban ghi duoc phep roi khoi pipeline camera.

    ``seat_id`` la dinh danh vi tri trong phien, khong duoc gan voi ten, ma
    hoc sinh, khuon mat, embedding, bbox hay keypoint.
    """

    seat_id: str
    observed_at_sec: float
    engagement_score: Optional[float]
    posture_state: str
    head_drop_events: int
    slumping_events: int

    def to_dict(self) -> dict:
        return asdict(self)


def anonymize_engagement(score: EngagementScore, timestamp: float, posture_state: str) -> AnonymizedEngagementRecord:
    """Chuyen ket qua noi bo thanh schema xuat toi thieu da cho phep."""
    return AnonymizedEngagementRecord(
        seat_id=score.seat_id,
        observed_at_sec=round(float(timestamp), 3),
        engagement_score=None if score.score is None else round(float(score.score), 2),
        posture_state=posture_state,
        head_drop_events=score.head_drop_count,
        slumping_events=score.slumping_count,
    )


def append_anonymized_record(path: Path, record: AnonymizedEngagementRecord) -> None:
    """Ghi mot dong JSONL chi theo schema an danh, khong nhan mapping tuy y."""
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
