"""
seat_mapper.py -- Module seating/: gan moi skeleton (PersonPose) phat hien
duoc vao mot seat_id, dua tren vi tri trung diem 2 vai va thuat toan
nearest-centroid so voi SeatGrid da calibrate.

Pham vi task nay (3.3, phan 1/2): gan seat CHO TUNG KHUNG HINH DOC LAP.
Theo doi on dinh seat_id qua nhieu khung hinh lien tiep (tracking) la task
3.4 (phan 2/2), CHUA lam trong file nay.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.detection.pose_detector import PersonPose
from src.seating.seat_grid import Seat, SeatGrid

logger = logging.getLogger("camera_ai.seating")

# Nguong confidence toi thieu cho 1 keypoint vai de con duoc coi la dang tin
# cay khi tinh trung diem 2 vai. Neu ca 2 vai deu duoi nguong nay (vi du bi
# khuat/quay lung), khong tinh duoc vi tri -> khong gan seat cho nguoi do.
MIN_SHOULDER_CONFIDENCE = 0.3


@dataclass
class SeatAssignment:
    """Ket qua gan 1 nguoi vao 1 seat trong MOT khung hinh cu the."""

    seat_id: str
    person: PersonPose
    distance: float  # khoang cach (pixel) tu trung diem vai den tam seat


def shoulder_midpoint(person: PersonPose) -> Optional[Tuple[float, float]]:
    """Tinh trung diem 2 vai (left_shoulder, right_shoulder) cua 1 PersonPose.

    Tra ve None neu ca hai keypoint vai deu khong du tin cay (duoi
    MIN_SHOULDER_CONFIDENCE) -- vi du nguoi quay lung lai camera, hoac bi
    che khuat hoan toan phan vai. Dung trung diem 2 vai (thay vi 1 diem don
    le nhu mui) vi day la phan than tren on dinh nhat, it bi anh huong boi tu
    the cui/nga dau -- phu hop lam \"vi tri\" dai dien cho 1 nguoi trong bai
    toan seating mapping.
    """
    left = person.get_keypoint("left_shoulder")
    right = person.get_keypoint("right_shoulder")

    left_ok = left is not None and left[2] >= MIN_SHOULDER_CONFIDENCE
    right_ok = right is not None and right[2] >= MIN_SHOULDER_CONFIDENCE

    if left_ok and right_ok:
        return ((left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0)
    if left_ok:
        return (left[0], left[1])
    if right_ok:
        return (right[0], right[1])
    return None


def assign_seats(
    people: List[PersonPose],
    grid: SeatGrid,
    max_distance: Optional[float] = None,
) -> List[SeatAssignment]:
    """Gan tung nguoi trong danh sach 'people' vao seat gan nhat theo
    nearest-centroid (dua tren trung diem 2 vai).

    Neu HAI nguoi tro len cung duoc gan vao MOT seat (vi du do phat hien
    trung/gan nhau, hoac calibration chua chuan), CHI giu lai nguoi co
    khoang cach gan tam seat nhat; nhung nguoi con lai KHONG duoc gan seat
    nao trong lan goi nay (khong tao seat_id trung lap).

    max_distance: neu duoc dat, nguoi co khoang cach toi seat gan nhat VUOT
        QUA gia tri nay se khong duoc gan seat nao (vi du phat hien nham
        giao vien dang dung/di lai trong lop, khong phai hoc sinh dang ngoi
        dung mot vi tri cho ngoi da calibrate).

    Tra ve danh sach SeatAssignment (mot phan tu cho moi nguoi DA duoc gan
    seat thanh cong -- nguoi khong tim duoc seat phu hop se khong xuat hien
    trong ket qua tra ve, khong phai gia tri None trong list).
    """
    candidates: List[SeatAssignment] = []

    for person in people:
        midpoint = shoulder_midpoint(person)
        if midpoint is None:
            logger.debug("Bo qua 1 PersonPose: khong tinh duoc trung diem vai (bi khuat/quay lung).")
            continue

        x, y = midpoint
        nearest_seat: Optional[Seat] = grid.find_nearest_seat(x, y)
        if nearest_seat is None:
            continue  # SeatGrid rong, chua calibrate

        distance = grid.distance_to(nearest_seat, x, y)

        if max_distance is not None and distance > max_distance:
            logger.debug(
                "Bo qua 1 PersonPose: khoang cach %.1f toi seat gan nhat '%s' "
                "vuot qua max_distance=%.1f.",
                distance, nearest_seat.seat_id, max_distance,
            )
            continue

        candidates.append(SeatAssignment(seat_id=nearest_seat.seat_id, person=person, distance=distance))

    return _resolve_duplicate_seats(candidates)


def _resolve_duplicate_seats(candidates: List[SeatAssignment]) -> List[SeatAssignment]:
    """Neu nhieu SeatAssignment cung tro toi 1 seat_id, chi giu lai ban ghi
    co 'distance' nho nhat (gan tam seat nhat), loai bo cac ban ghi con lai."""
    best_by_seat = {}
    for candidate in candidates:
        current_best = best_by_seat.get(candidate.seat_id)
        if current_best is None or candidate.distance < current_best.distance:
            best_by_seat[candidate.seat_id] = candidate
    return list(best_by_seat.values())