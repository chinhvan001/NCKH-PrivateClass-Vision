"""Allowlist ket qua phien edge ghi len Firestore theo schema cua nhom.

- ``session_results/{session_id}`` (``SessionResult``): trang thai hien tai moi ghe,
  ghi de ~10 s mot lan (UC07). ``monitoring_status`` cho biet phien giam sat co tron ven (UC04).
- ``session_evaluations/{session_id}_{seat_id}`` (``SeatEvaluation``): tong hop tung ghe,
  ghi de ~5 phut mot lan va lan cuoi khi het phien (UC03, UC11).

Chi co seat_id, diem, trang thai, so dem va thoi diem chup (``captured_at``: wall-clock
UTC cua edge, cung kieu voi ``started_at`` cua phien). Khong anh, keypoint, bbox, ten
hay ma hoc sinh. Object kiem tra du lieu ngay khi tao; khong tu tao dict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from .alert_event import check_session_id

# focused: tu the binh thuong. drowsy: cui dau, tay tinh (head_drop). distracted: guc/cui
# dau khong ro, quay lung hoac noi chuyen rieng vua xay ra. away: khong thay nguoi o ghe.
SEAT_STATUSES = frozenset({"focused", "drowsy", "distracted", "away"})
# running: dang giam sat. completed: giao vien ket thuc phien. incomplete: phien dut ngang
# (huy, bi xoa, edge tat hoac khoi dong lai giua phien) -- so lieu chi la mot phan (UC04).
MONITORING_STATUSES = frozenset({"running", "completed", "incomplete"})


def _seat_id(value: object) -> None:
    if not isinstance(value, str) or not value.strip() or "/" in value:
        raise ValueError("seat_id phai la chuoi khong rong, khong chua '/'.")


def _score(value: object, name: str) -> None:
    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100):
        raise ValueError(f"{name} phai la so nguyen 0-100 hoac None.")


def _count(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} phai la so nguyen >= 0.")


def _utc(value: object) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("captured_at phai la datetime co mui gio.")


@dataclass(frozen=True)
class SeatResult:
    seat_id: str
    concentration: int | None  # diem 60 s gan nhat
    interaction: int  # so dot noi chuyen rieng (alert side_conversation) tu dau phien
    status: str

    def __post_init__(self) -> None:
        _seat_id(self.seat_id)
        _score(self.concentration, "concentration")
        _count(self.interaction, "interaction")
        if self.status not in SEAT_STATUSES:
            raise ValueError(f"status phai thuoc {sorted(SEAT_STATUSES)}.")


@dataclass(frozen=True)
class SessionResult:
    session_id: str
    camera_id: str
    captured_at: datetime
    monitoring_status: str
    seats: tuple[SeatResult, ...]

    def __post_init__(self) -> None:
        check_session_id(self.session_id)
        if not isinstance(self.camera_id, str) or not self.camera_id.strip():
            raise ValueError("camera_id phai la chuoi khong rong.")
        _utc(self.captured_at)
        if self.monitoring_status not in MONITORING_STATUSES:
            raise ValueError(f"monitoring_status phai thuoc {sorted(MONITORING_STATUSES)}.")
        if not all(isinstance(seat, SeatResult) for seat in self.seats):
            raise TypeError("seats chi nhan SeatResult.")
        if len({seat.seat_id for seat in self.seats}) != len(self.seats):
            raise ValueError("seat_id trong result_map bi trung.")

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "captured_at": self.captured_at,
            "monitoring_status": self.monitoring_status,
            "result_map": {
                seat.seat_id: {
                    "concentration": seat.concentration,
                    "interaction": seat.interaction,
                    "status": seat.status,
                }
                for seat in self.seats
            },
        }


@dataclass(frozen=True)
class SeatEvaluation:
    session_id: str
    seat_id: str
    captured_at: datetime
    concentration: int | None  # diem 60 s gan nhat luc chup
    avg_concentration: int | None  # diem tu dau phien
    distraction: int  # so alert cua ghe tu dau phien (head_drop, back_turn, side_conversation)
    observed_sec: int  # thoi gian ghe duoc quan sat: bao cao loc ghe chi co nguoi di ngang

    def __post_init__(self) -> None:
        check_session_id(self.session_id)
        _seat_id(self.seat_id)
        _utc(self.captured_at)
        _score(self.concentration, "concentration")
        _score(self.avg_concentration, "avg_concentration")
        _count(self.distraction, "distraction")
        _count(self.observed_sec, "observed_sec")

    def to_dict(self) -> dict:
        return asdict(self)
