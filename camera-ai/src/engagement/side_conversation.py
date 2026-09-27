"""Phat hien dau hieu tuong tac rieng tu skeleton va vi tri ghe.

Module nay chi xuat *canh bao can quan sat*, khong ket luan mot hoc sinh dang
noi. Video khong co am thanh khong the phan biet chac chan noi chuyen voi
viec quay sang nghe, dua do dung, hoac tuong tac hoc tap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from src.detection.pose_detector import PersonPose


@dataclass(frozen=True)
class SideConversationEvent:
    """Canh bao cho mot cap ghe, da vuot nguong duy tri thoi gian."""

    first_seat_id: str
    second_seat_id: str
    duration_sec: float


@dataclass
class _PairState:
    active_since: float
    last_seen: float


class SideConversationDetector:
    """Phat hien cap ngoi gan quay mat ve phia nhau lien tuc.

    Dau vao la mapping ``seat_id -> PersonPose`` nen khong luu hay gan danh
    tinh ca nhan. Hai tin hieu bat buoc la (1) hai ghe gan nhau va (2) ca hai
    mui lech ve phia nguoi con lai so voi trung diem vai. Neu keypoint mat/vai
    khong ro, cap do bi bo qua thay vi suy dien.
    """

    def __init__(
        self,
        max_pair_distance: float = 260.0,
        min_head_turn_ratio: float = 0.12,
        min_duration_sec: float = 3.0,
        max_gap_sec: float = 0.75,
    ) -> None:
        if max_pair_distance <= 0 or min_duration_sec <= 0 or max_gap_sec < 0:
            raise ValueError("Nguong khoang cach/thoi gian khong hop le.")
        if not 0 <= min_head_turn_ratio <= 1:
            raise ValueError("min_head_turn_ratio phai nam trong [0, 1].")
        self.max_pair_distance = max_pair_distance
        self.min_head_turn_ratio = min_head_turn_ratio
        self.min_duration_sec = min_duration_sec
        self.max_gap_sec = max_gap_sec
        self._states: Dict[Tuple[str, str], _PairState] = {}

    def update(
        self, timestamp: float, people_by_seat: Mapping[str, PersonPose]
    ) -> List[SideConversationEvent]:
        """Cap nhat mot frame va tra ve cac cap da duy tri du lau.

        Chi ghep moi nguoi voi mot nguoi gan nhat trong frame, tranh mot hoc
        sinh tao nhieu canh bao dong thoi khi ngoi giua hai ban khac.
        """
        candidates = []
        items = sorted(people_by_seat.items())
        for index, (first_id, first) in enumerate(items):
            first_center = self._shoulder_midpoint(first)
            if first_center is None:
                continue
            for second_id, second in items[index + 1:]:
                second_center = self._shoulder_midpoint(second)
                if second_center is None:
                    continue
                distance = math.dist(first_center, second_center)
                if distance > self.max_pair_distance:
                    continue
                if self._faces_toward_each_other(first, first_center, second, second_center):
                    candidates.append((distance, (first_id, second_id)))

        active_pairs = set()
        occupied = set()
        for _, pair in sorted(candidates):
            if pair[0] in occupied or pair[1] in occupied:
                continue
            active_pairs.add(pair)
            occupied.update(pair)

        events = []
        for pair in active_pairs:
            state = self._states.get(pair)
            # Mot frame dang co cap nay la bang chung lien tuc tiep theo. Khong
            # reset chi vi detector duoc goi thua (vi du pipeline xu ly moi
            # 2--3 frame); chi reset khi da QUAN SAT mot frame khong co cap
            # nay qua max_gap_sec o buoc cleanup ben duoi.
            if state is None:
                state = _PairState(active_since=timestamp, last_seen=timestamp)
                self._states[pair] = state
            else:
                state.last_seen = timestamp
            duration = timestamp - state.active_since
            if duration >= self.min_duration_sec:
                events.append(SideConversationEvent(*pair, duration_sec=duration))

        # Xoa state da mat lau de khi hai ban quay lai thi phai tich luy lai.
        self._states = {
            pair: state
            for pair, state in self._states.items()
            if pair in active_pairs or timestamp - state.last_seen <= self.max_gap_sec
        }
        return sorted(events, key=lambda event: (event.first_seat_id, event.second_seat_id))

    @staticmethod
    def _shoulder_midpoint(person: PersonPose) -> Optional[Tuple[float, float]]:
        left = person.get_keypoint("left_shoulder")
        right = person.get_keypoint("right_shoulder")
        if left is None or right is None or left[2] < 0.3 or right[2] < 0.3:
            return None
        return ((left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0)

    def _faces_toward_each_other(
        self,
        first: PersonPose,
        first_center: Tuple[float, float],
        second: PersonPose,
        second_center: Tuple[float, float],
    ) -> bool:
        first_turn = self._head_turn_ratio(first, first_center)
        second_turn = self._head_turn_ratio(second, second_center)
        if first_turn is None or second_turn is None:
            return False
        direction = 1 if second_center[0] > first_center[0] else -1
        return (
            first_turn * direction >= self.min_head_turn_ratio
            and second_turn * direction <= -self.min_head_turn_ratio
        )

    @staticmethod
    def _head_turn_ratio(
        person: PersonPose, shoulder_center: Tuple[float, float]
    ) -> Optional[float]:
        """Do lech ngang cua mui theo be rong vai; am=trai, duong=phai."""
        nose = person.get_keypoint("nose")
        left = person.get_keypoint("left_shoulder")
        right = person.get_keypoint("right_shoulder")
        if (
            nose is None or left is None or right is None
            or nose[2] < 0.3 or left[2] < 0.3 or right[2] < 0.3
        ):
            return None
        shoulder_width = math.dist((left[0], left[1]), (right[0], right[1]))
        if shoulder_width < 5.0:
            return None
        return (nose[0] - shoulder_center[0]) / shoulder_width
