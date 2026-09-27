"""
seat_tracker.py -- Module seating/: duy tri seat_id ON DINH qua nhieu khung
hinh lien tiep, phuc vu Pseudonymous Spatial Seating Mapping (task 3.4, phan
2/2).

Van de can giai quyet: assign_seats() (task 3.3, phan 1/2) gan seat DOC LAP
tung khung hinh, dua thuan tuy vao nearest-centroid. Vi keypoint tu
YOLOv8-pose luon co it nhieu nhieu (jitter) frame-sang-frame, mot nguoi ngoi
YEN MOT CHO van co the bi "nhay" seat_id neu vi tri trung diem vai dao dong
qua lai giua 2 seat gan nhau -- gay nhieu du lieu dau ra.

Giai phap: SeatTracker uu tien TINH LIEN TUC (continuity) -- neu vi tri hien
tai gan voi vi tri da biet cua mot seat dang duoc theo doi (tu khung hinh
truoc), giu nguyen seat_id do thay vi tinh lai nearest-centroid tu dau. Chi
khi khong khop voi track nao dang co (nguoi moi xuat hien, hoac seat da
"mat dau" nguoi qua lau), moi fallback ve nearest-centroid tho.

Dong thoi xu ly khuat tam thoi: mot seat khong bi coi la "trong" ngay khi 1
khung hinh khong phat hien duoc nguoi o do (hoc sinh cui thap, bi bang/ban
che khuat mot phan) -- chi thuc su xoa khoi trang thai theo doi sau
max_missing_frames khung hinh lien tiep khong thay.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.detection.pose_detector import PersonPose
from src.seating.seat_grid import SeatGrid
from src.seating.seat_mapper import SeatAssignment, shoulder_midpoint

logger = logging.getLogger("camera_ai.seating")


@dataclass
class _SeatState:
    """Trang thai noi bo cua 1 seat dang duoc theo doi (khong public)."""

    seat_id: str
    last_assignment: SeatAssignment
    last_position: Tuple[float, float]
    missing_count: int = 0


class SeatTracker:
    """Lop theo doi (tracking) giu seat_id on dinh qua nhieu khung hinh lien
    tiep, dua tren khoang cach vi tri giua cac frame (don gian hoa cua
    centroid-tracking, phu hop bai toan nguoi NGOI CO DINH, khong di chuyen).

    Cach dung:
        tracker = SeatTracker(grid, max_missing_frames=15)
        for frame in video_stream:
            people = pose_detector.detect(frame.image)
            current_assignments = tracker.update(people)
            # current_assignments: Dict[seat_id, SeatAssignment] -- da qua
            # xu ly on dinh, KHONG PHAI ket qua tho tung frame.
    """

    def __init__(
        self,
        grid: SeatGrid,
        max_missing_frames: int = 15,
        continuity_threshold: float = 40.0,
        max_distance: Optional[float] = None,
    ):
        """
        max_missing_frames: so khung hinh LIEN TIEP khong phat hien duoc
            nguoi o 1 seat truoc khi coi seat do la thuc su trong (vacant)
            va xoa khoi trang thai theo doi.
        continuity_threshold: neu vi tri (trung diem vai) o khung hinh hien
            tai cach vi tri da biet gan day nhat cua 1 seat trong pham vi
            nay (pixel), coi la CUNG MOT NGUOI dang tiep tuc ngoi o seat do
            -- giu nguyen seat_id, KHONG tinh lai nearest-centroid. Gia tri
            nay can > muc do jitter binh thuong cua detection, nhung < mot
            nua khoang cach toi thieu giua 2 seat lien ke (neu qua lon se
              gan nham nguoi o seat ben canh).
        max_distance: nhu assign_seats() -- gioi han khoang cach toi da khi
            fallback ve nearest-centroid (nguoi moi/seat vua "mat dau" qua lau).
        """
        self._grid = grid
        self._max_missing_frames = max_missing_frames
        self._continuity_threshold = continuity_threshold
        self._max_distance = max_distance
        self._states: Dict[str, _SeatState] = {}
        self._frame_count = 0

    def update(self, people: List[PersonPose]) -> Dict[str, SeatAssignment]:
        """Goi MOT LAN moi khung hinh moi voi danh sach PersonPose phat hien
        duoc trong khung hinh do.

        Tra ve dict {seat_id: SeatAssignment} the hien trang thai DA QUA XU
        LY ON DINH -- bao gom ca cac seat khong co nguoi trong CHINH khung
        hinh nay nhung van con trong pham vi max_missing_frames (dung
        SeatAssignment cua lan cuoi thuc su thay duoc nguoi).
        """
        self._frame_count += 1
        previous_states = dict(self._states)  # chup lai truoc khi cap nhat, dung cho continuity check

        candidates = []
        for person in people:
            midpoint = shoulder_midpoint(person)
            if midpoint is not None:
                candidates.append((person, midpoint))

        raw_choices = []
        for person, (x, y) in candidates:
            seat_id, distance = self._choose_seat(x, y, previous_states)
            if seat_id is not None:
                raw_choices.append((person, (x, y), seat_id, distance))

        # Giai quyet trung lap: 2 nguoi cung chon 1 seat trong CHINH khung
        # hinh nay -> chi giu nguoi gan tam seat hon (giong assign_seats()).
        best_by_seat: Dict[str, Tuple[PersonPose, Tuple[float, float], float]] = {}
        for person, pos, seat_id, distance in raw_choices:
            current = best_by_seat.get(seat_id)
            if current is None or distance < current[2]:
                best_by_seat[seat_id] = (person, pos, distance)

        seen_this_frame = set(best_by_seat.keys())

        for seat_id, (person, pos, distance) in best_by_seat.items():
            self._states[seat_id] = _SeatState(
                seat_id=seat_id,
                last_assignment=SeatAssignment(seat_id=seat_id, person=person, distance=distance),
                last_position=pos,
                missing_count=0,
            )

        expired_seat_ids = []
        for seat_id, state in self._states.items():
            if seat_id not in seen_this_frame:
                state.missing_count += 1
                if state.missing_count > self._max_missing_frames:
                    expired_seat_ids.append(seat_id)

        for seat_id in expired_seat_ids:
            logger.debug(
                "Seat '%s' khong thay nguoi sau %d khung hinh lien tiep -- coi la trong.",
                seat_id, self._max_missing_frames,
            )
            del self._states[seat_id]

        return self.current_assignments

    def _choose_seat(
        self, x: float, y: float, previous_states: Dict[str, _SeatState]
    ) -> Tuple[Optional[str], Optional[float]]:
        """Chon seat_id phu hop nhat cho vi tri (x, y): uu tien tinh lien
        tuc voi track dang co, fallback ve nearest-centroid neu khong khop."""
        best_seat_id = None
        best_distance_to_prev = None
        for seat_id, state in previous_states.items():
            prev_x, prev_y = state.last_position
            d = math.hypot(prev_x - x, prev_y - y)
            if best_distance_to_prev is None or d < best_distance_to_prev:
                best_distance_to_prev = d
                best_seat_id = seat_id

        if best_seat_id is not None and best_distance_to_prev <= self._continuity_threshold:
            seat = self._grid.get_seat(best_seat_id)
            if seat is not None:
                return best_seat_id, self._grid.distance_to(seat, x, y)

        nearest = self._grid.find_nearest_seat(x, y)
        if nearest is None:
            return None, None
        nearest_distance = self._grid.distance_to(nearest, x, y)
        if self._max_distance is not None and nearest_distance > self._max_distance:
            return None, None
        return nearest.seat_id, nearest_distance

    @property
    def current_assignments(self) -> Dict[str, SeatAssignment]:
        """Trang thai gan seat on dinh HIEN TAI (sau lan update() gan nhat),
        bao gom ca seat dang trong thoi gian an (missing nhung chua vuot
        max_missing_frames)."""
        return {seat_id: state.last_assignment for seat_id, state in self._states.items()}

    def reset(self) -> None:
        """Xoa toan bo trang thai theo doi (vi du khi bat dau buoi hoc moi)."""
        self._states.clear()
        self._frame_count = 0