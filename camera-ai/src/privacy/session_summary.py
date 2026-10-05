"""Allowlist tong ket cuoi phien (UC03 bao cao, UC11 xuat file): diem tung ghe va trung binh lop.

Moi tong ket gui ra phai tao qua ``make_session_summary()``; khong tu tao dict.
Khong co anh, keypoint, bbox, timestamp wall-clock, ten hay ma hoc sinh.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.engagement.engagement_score import EngagementScore

from .alert_event import check_session_id

# running: edge dang xu ly phien. completed: giao vien ket thuc phien.
# incomplete: phien dut ngang (edge tat/khoi dong lai giua phien, document phien
# bi xoa) -- so lieu chi la mot phan cua buoi hoc (UC04 luong phu).
SUMMARY_STATUSES = frozenset({"running", "completed", "incomplete"})


@dataclass(frozen=True)
class SeatSummary:
    seat_id: str
    engagement_score: float | None
    observed_sec: int  # thoi gian ghe duoc quan sat trong phien
    head_drop_events: int
    slumping_events: int


@dataclass(frozen=True)
class SessionSummary:
    """``class_average``: trung binh diem cac ghe, trong so = thoi gian quan sat,
    nen ghe chi thoang thay vai giay (nguoi di ngang) gan nhu khong anh huong.
    None neu chua ghe nao co diem."""

    session_id: str
    status: str
    class_average: float | None
    seats: tuple[SeatSummary, ...]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "class_average": self.class_average,
            "seats": [
                {
                    "seat_id": seat.seat_id,
                    "engagement_score": seat.engagement_score,
                    "observed_sec": seat.observed_sec,
                    "head_drop_events": seat.head_drop_events,
                    "slumping_events": seat.slumping_events,
                }
                for seat in self.seats
            ],
        }


def make_session_summary(session_id: str, status: str, scores: Iterable[EngagementScore]) -> SessionSummary:
    check_session_id(session_id)
    if status not in SUMMARY_STATUSES:
        raise ValueError(f"status phai thuoc {sorted(SUMMARY_STATUSES)}.")
    scores = sorted(scores, key=lambda score: score.seat_id)
    weighted = [(score.score, score.time_total) for score in scores if score.score is not None and score.time_total > 0]
    total_sec = sum(seconds for _, seconds in weighted)
    return SessionSummary(
        session_id=session_id,
        status=status,
        class_average=(
            round(sum(value * seconds for value, seconds in weighted) / total_sec, 2) if total_sec > 0 else None
        ),
        seats=tuple(
            SeatSummary(
                seat_id=score.seat_id,
                engagement_score=None if score.score is None else round(float(score.score), 2),
                observed_sec=round(score.time_total),
                head_drop_events=score.head_drop_count,
                slumping_events=score.slumping_count,
            )
            for score in scores
        ),
    )
