"""Allowlist ``session_windows/{session_id}_{run}_{seq}``: moi ~10 s giam sat, edge gui thoi gian
moi ghe o tung trang thai tu the de backend web tinh diem (docs/backend_scoring_and_schema_proposal.md).

Chi co seat_id, so giay theo dong ho phien, trang thai tu the va so alert. Khong anh, keypoint,
bbox, track ID, ten hay ma hoc sinh. Object kiem tra du lieu ngay khi tao; khong tu tao dict.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime

from .alert_event import ALERT_TYPES, check_session_id
from .session_output import MONITORING_STATUSES, _count, _seat_id, _utc

# Nhu classify_posture_state: normal; slumping (guc, hoac cui dau ma khong ro tay); head_drop (cui dau, tay tinh)
POSTURE_STATES = ("normal", "slumping", "head_drop")
_RUN_PATTERN = re.compile(r"[0-9a-f]{8}")
_ROUNDING_SLACK_SEC = 0.05


def _seconds(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} phai la so huu han >= 0.")


@dataclass(frozen=True)
class SeatWindow:
    seat_id: str
    normal_sec: float
    slumping_sec: float
    head_drop_sec: float
    last_seen_sec: float  # giay theo dong ho phien luc thay nguoi o ghe lan cuoi
    last_state: str  # trang thai tu the luc do
    last_behaviour_sec: float | None  # quay lung/noi chuyen rieng gan nhat trong window
    alerts: dict = field(default_factory=dict)  # loai alert -> so alert bat dau trong window

    def __post_init__(self) -> None:
        _seat_id(self.seat_id)
        for name in ("normal_sec", "slumping_sec", "head_drop_sec", "last_seen_sec"):
            _seconds(getattr(self, name), name)
        if self.last_behaviour_sec is not None:
            _seconds(self.last_behaviour_sec, "last_behaviour_sec")
        if self.last_state not in POSTURE_STATES:
            raise ValueError(f"last_state phai thuoc {list(POSTURE_STATES)}.")
        if not isinstance(self.alerts, dict) or not set(self.alerts) <= ALERT_TYPES:
            raise ValueError(f"alerts chi co cac loai {sorted(ALERT_TYPES)}.")
        for count in self.alerts.values():
            _count(count, "alerts")

    @property
    def seen_sec(self) -> float:
        return self.normal_sec + self.slumping_sec + self.head_drop_sec

    def to_dict(self) -> dict:
        return {
            "normal_sec": round(self.normal_sec, 1),
            "slumping_sec": round(self.slumping_sec, 1),
            "head_drop_sec": round(self.head_drop_sec, 1),
            "last_seen_sec": round(self.last_seen_sec, 1),
            "last_state": self.last_state,
            "last_behaviour_sec": None if self.last_behaviour_sec is None else round(self.last_behaviour_sec, 1),
            "alerts": {alert_type: count for alert_type, count in sorted(self.alerts.items()) if count},
        }


@dataclass(frozen=True)
class SessionWindow:
    session_id: str
    camera_id: str
    run: str  # moi lan edge bat dau/tiep tuc phien: dong ho phien chay lai tu 0
    seq: int  # 0, 1, 2... trong 1 run
    start_sec: float
    end_sec: float
    captured_at: datetime
    monitoring_status: str  # running; window cuoi cua phien: completed/incomplete
    seats: tuple[SeatWindow, ...]

    def __post_init__(self) -> None:
        check_session_id(self.session_id)
        if not isinstance(self.camera_id, str) or not self.camera_id.strip() or "/" in self.camera_id:
            raise ValueError("camera_id phai la chuoi khong rong, khong chua '/'.")
        if not isinstance(self.run, str) or not _RUN_PATTERN.fullmatch(self.run):
            raise ValueError("run phai la 8 ky tu hex.")
        _count(self.seq, "seq")
        _seconds(self.start_sec, "start_sec")
        _seconds(self.end_sec, "end_sec")
        if self.end_sec < self.start_sec:
            raise ValueError("end_sec phai >= start_sec.")
        _utc(self.captured_at)
        if self.monitoring_status not in MONITORING_STATUSES:
            raise ValueError(f"monitoring_status phai thuoc {sorted(MONITORING_STATUSES)}.")
        if not all(isinstance(seat, SeatWindow) for seat in self.seats):
            raise TypeError("seats chi nhan SeatWindow.")
        if len({seat.seat_id for seat in self.seats}) != len(self.seats):
            raise ValueError("seat_id trong window bi trung.")
        if any(seat.seen_sec > self.end_sec - self.start_sec + _ROUNDING_SLACK_SEC for seat in self.seats):
            raise ValueError("Thoi gian cua 1 ghe vuot do dai window.")

    @property
    def doc_id(self) -> str:
        return f"{self.session_id}_{self.run}_{self.seq:05d}"

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "run": self.run,
            "seq": self.seq,
            "start_sec": round(self.start_sec, 1),
            "end_sec": round(self.end_sec, 1),
            "captured_at": self.captured_at,
            "monitoring_status": self.monitoring_status,
            "seats": {seat.seat_id: seat.to_dict() for seat in self.seats},
        }
