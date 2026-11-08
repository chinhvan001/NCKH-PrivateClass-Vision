"""Canh bao hoc sinh co mat khong huong ve camera (nghi quay lung).

Chi dung voi camera frontal. Skeleton 2D khong the phan biet chac chan quay
lung voi mat bi ban tay/nguoi khac che, do do event la tin hieu can quan sat,
khong phai ket luan hanh vi.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from src.detection.pose_detector import PersonPose


@dataclass(frozen=True)
class BackTurnEvent:
    seat_id: str
    duration_sec: float
    face_visibility: float


@dataclass
class _SeatState:
    active_since: float
    last_seen: float


class BackTurnDetector:
    """Phat hien vai ro nhung cac diem mat khong ro trong mot khoang thoi gian."""

    def __init__(
        self,
        max_face_visibility: float = 0.20,
        min_duration_sec: float = 2.0,
        max_gap_sec: float = 2.0,
    ) -> None:
        # max_gap_sec: khoang khong thay hanh vi van coi la cung 1 dot. 2.0s (bang
        # AlertManager.episode_gap_sec) chiu duoc 1 frame bo sot ngay ca o ~1 FPS (CPU);
        # 0.75s cu lam 1 lan detect hut o 1 FPS xoa sach thoi gian da tich luy.
        if not 0 <= max_face_visibility <= 1 or min_duration_sec <= 0 or max_gap_sec < 0:
            raise ValueError("Nguong BackTurnDetector khong hop le.")
        self.max_face_visibility = max_face_visibility
        self.min_duration_sec = min_duration_sec
        self.max_gap_sec = max_gap_sec
        self._states: Dict[str, _SeatState] = {}

    def update(self, timestamp: float, people_by_seat: Mapping[str, PersonPose]) -> List[BackTurnEvent]:
        events = []
        active_seats = set()
        for seat_id, person in people_by_seat.items():
            visibility = self._face_visibility_if_shoulders_visible(person)
            if visibility is None or visibility > self.max_face_visibility:
                continue
            active_seats.add(seat_id)
            state = self._states.get(seat_id)
            if state is None:
                state = _SeatState(active_since=timestamp, last_seen=timestamp)
                self._states[seat_id] = state
            else:
                state.last_seen = timestamp
            duration = timestamp - state.active_since
            if duration >= self.min_duration_sec:
                events.append(BackTurnEvent(seat_id, duration, visibility))

        self._states = {
            seat_id: state
            for seat_id, state in self._states.items()
            if seat_id in active_seats or timestamp - state.last_seen <= self.max_gap_sec
        }
        return sorted(events, key=lambda event: event.seat_id)

    @staticmethod
    def _face_visibility_if_shoulders_visible(person: PersonPose) -> Optional[float]:
        shoulders = [person.get_keypoint("left_shoulder"), person.get_keypoint("right_shoulder")]
        if any(keypoint is None or keypoint[2] < 0.3 for keypoint in shoulders):
            return None
        face = [
            person.get_keypoint("nose"),
            person.get_keypoint("left_eye"),
            person.get_keypoint("right_eye"),
        ]
        # YOLO tra keypoint co confidence 0 khi diem khong thay; van can coi do
        # la face_visibility=0 thay vi bo qua frame.
        confidences = [keypoint[2] for keypoint in face if keypoint is not None]
        return sum(confidences) / len(confidences) if confidences else 0.0
