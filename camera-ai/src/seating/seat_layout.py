"""Toa do ghe trong anh tu so do hang/cot cua lop va 4 ghe goc hieu chinh tren edge.

Firestore chi co so hang/cot cua lop (``classes2/{class_id}``). Vi tri
tren anh phu thuoc cach lap camera nen nam trong config local cua edge: toa do
tam 4 ghe goc. Ghe con lai duoc suy ra bang phep bien doi phoi canh
(homography) tu o vuong don vi sang tu giac 4 ghe goc -- dung cho mat phang
ghe ngoi nhin xien, ghe xa camera tu nhien xit lai gan nhau hon.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np

from .seat_grid import Seat, SeatGrid, SeatGridError

logger = logging.getLogger("camera_ai.seating")


@dataclass(frozen=True)
class CornerSeats:
    """Toa do pixel (x, y) tam 4 ghe goc trong khung hinh camera."""

    first_row_first_column: tuple[float, float]
    first_row_last_column: tuple[float, float]
    last_row_last_column: tuple[float, float]
    last_row_first_column: tuple[float, float]


def layout_seat_grid(
    seats: Iterable[tuple[str, object, object]], row_count: int, column_count: int, corners: CornerSeats
) -> SeatGrid:
    """``seats``: (seat_id, row, column), hang/cot dem tu 1 (chuoi so nhu "02" cung duoc).

    Ghe co hang/cot hong hoac nam ngoai so do bi bo qua (ghi log) de 1 document
    sai khong chan ca phien; khong con ghe hop le nao thi nem SeatGridError."""
    if row_count < 1 or column_count < 1:
        raise SeatGridError("row_count va column_count phai >= 1.")
    quad = np.float32(
        [
            corners.first_row_first_column,
            corners.first_row_last_column,
            corners.last_row_last_column,
            corners.last_row_first_column,
        ]
    )
    homography = None
    if row_count > 1 and column_count > 1:
        # Tu giac loi theo dung thu tu: bat ca 4 diem thang hang lan khai nham nhan 2 goc.
        edges = np.roll(quad, -1, axis=0) - quad
        turns = edges[:, 0] * np.roll(edges, -1, axis=0)[:, 1] - edges[:, 1] * np.roll(edges, -1, axis=0)[:, 0]
        if not (np.all(turns > 0) or np.all(turns < 0)):
            raise SeatGridError("4 ghe goc phai tao thanh tu giac loi theo thu tu hang dau -> hang cuoi.")
        homography = cv2.getPerspectiveTransform(np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]), quad)

    placed = []
    for seat_id, raw_row, raw_column in seats:
        try:
            row, column = int(raw_row), int(raw_column)
        except (TypeError, ValueError):
            row = column = 0
        if not (1 <= row <= row_count and 1 <= column <= column_count):
            logger.warning("Bo qua ghe %r: hang/cot nam ngoai so do %dx%d.", seat_id, row_count, column_count)
            continue
        u = (column - 1) / (column_count - 1) if column_count > 1 else 0.0
        v = (row - 1) / (row_count - 1) if row_count > 1 else 0.0
        if homography is not None:
            x, y = cv2.perspectiveTransform(np.float32([[[u, v]]]), homography)[0, 0]
        else:  # 1 hang hoac 1 cot: noi suy tren canh co ghe
            end = quad[1] if row_count == 1 else quad[3]
            x, y = quad[0] + (end - quad[0]) * (u if row_count == 1 else v)
        placed.append(Seat(str(seat_id), float(x), float(y)))
    if not placed:
        raise SeatGridError("So do lop khong co ghe hop le nao.")
    return SeatGrid(placed)
