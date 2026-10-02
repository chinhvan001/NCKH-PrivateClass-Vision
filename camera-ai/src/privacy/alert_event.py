"""Allowlist schema cho canh bao hanh vi (UC09) roi khoi pipeline.

Moi alert gui ra (Firestore, FCM, log) phai tao qua ``make_alert_event()``;
khong tu tao dict. Schema chi co 5 truong, khong co anh, keypoint, bbox,
confidence, ten hay ma hoc sinh.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# head_drop: cui dau + tay tinh keo dai (nghi ngu gat).
# back_turn: vai ro nhung mat khong huong camera (chi camera frontal).
# side_conversation: 2 ghe quay ve nhau -- producer phat 1 alert cho MOI ghe.
ALERT_TYPES = frozenset({"head_drop", "back_turn", "side_conversation"})

# session_id phai la ma ngau nhien (vd uuid4), an toan lam Firestore doc id;
# khong duoc ghep ten lop/giao vien/ngay vao.
_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")


class AlertEventError(ValueError):
    pass


@dataclass(frozen=True)
class AlertEvent:
    """Canh bao cho MOT ghe trong MOT phien.

    ``start_sec`` la so giay tu luc bat dau phien (khong phai wall-clock),
    lam tron 0.1s; ``duration_sec`` la do dai hanh vi da duy tri tinh den luc
    phat alert.
    """

    session_id: str
    seat_id: str
    type: str
    start_sec: float
    duration_sec: float

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "seat_id": self.seat_id,
            "type": self.type,
            "start_sec": self.start_sec,
            "duration_sec": self.duration_sec,
        }


def _non_negative_seconds(value: float, name: str) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as error:
        raise AlertEventError(f"{name} phai la so.") from error
    if not math.isfinite(value) or value < 0:
        raise AlertEventError(f"{name} phai la so huu han >= 0.")
    return round(value, 1)


def make_alert_event(
    session_id: str, seat_id: str, alert_type: str, start_sec: float, duration_sec: float
) -> AlertEvent:
    if not isinstance(session_id, str) or not _SESSION_ID_PATTERN.fullmatch(session_id):
        raise AlertEventError("session_id phai la ma 1-64 ky tu [A-Za-z0-9_-].")
    if not isinstance(seat_id, str) or not seat_id.strip():
        raise AlertEventError("seat_id phai la chuoi khong rong.")
    if alert_type not in ALERT_TYPES:
        raise AlertEventError(f"type phai thuoc {sorted(ALERT_TYPES)}.")
    return AlertEvent(
        session_id=session_id,
        seat_id=seat_id.strip(),
        type=alert_type,
        start_sec=_non_negative_seconds(start_sec, "start_sec"),
        duration_sec=_non_negative_seconds(duration_sec, "duration_sec"),
    )
