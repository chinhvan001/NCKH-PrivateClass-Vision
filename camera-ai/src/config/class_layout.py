"""So do ghe cua tiet tu file tiet hien tai cua camera (``camera_sessions/{camera_id}.json``, ``src/sync``).

Web admin ghi file nay luc bat dau tiet: ``row_count``/``column_count`` cua lop (``classes2/{class_id}``)
va o chu nhat admin ve tren trang Quan ly camera cho dung lop do (``seat_regions``), khong bao gio
``seat_map`` (ghe -> hoc sinh). Ma ghe co dinh theo vi tri: ``S{n:02d}`` voi n dem theo hang tu 1
(``S01``, ``S02``, ...; ``backend/routes/class_routes.py``), nen edge tu sinh ma ghe tu so hang/cot.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from src.seating import Seat, SeatGrid

logger = logging.getLogger("camera_ai.seating")

MAX_GRID_SIDE = 50  # file tiet hong/bi sua khong duoc bat edge tao hang trieu ghe
MAX_IMAGE_SIDE = 10000


class ClassLayoutError(RuntimeError):
    """Khong dung duoc so do ghe cua tiet."""


def seat_id(row: int, column: int, column_count: int) -> str:
    """Ma ghe giong web admin: ``S01`` la hang 1 cot 1, dem theo hang."""
    return f"S{(row - 1) * column_count + column:02d}"


def _size(value: Any, limit: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= limit


def session_seat_grid(order: dict | None, session_id: str) -> SeatGrid:
    """Grid cua tiet ``session_id`` tu file tiet hien tai cua camera (``sync.camera_session``)."""
    if not order or order.get("session_id") != session_id:
        raise ClassLayoutError(f"Web admin chua giao tiet {session_id} cho camera nay.")
    rows, columns = order.get("row_count"), order.get("column_count")
    if not (_size(rows, MAX_GRID_SIDE) and _size(columns, MAX_GRID_SIDE)):
        raise ClassLayoutError(f"Lop cua tiet thieu so hang/cot hop le (1-{MAX_GRID_SIDE}).")
    seat_ids = {seat_id(row, column, columns) for row in range(1, rows + 1) for column in range(1, columns + 1)}
    return _region_grid(order.get("seat_regions"), seat_ids)


def _region_grid(data: Any, seat_ids: set[str]) -> SeatGrid:
    """O ghe admin ve tren anh chup tu camera. Ghe chua ve khong duoc theo doi; o hong bi bo qua."""
    if not isinstance(data, dict):
        raise ClassLayoutError("Chua co vi tri ghe: ve o ghe tren trang Quan ly camera.")
    width, height = data.get("image_width"), data.get("image_height")
    if not (_size(width, MAX_IMAGE_SIDE) and _size(height, MAX_IMAGE_SIDE)):
        raise ClassLayoutError("O ghe cua tiet thieu kich thuoc anh hop le.")
    regions = data.get("seats") if isinstance(data.get("seats"), dict) else {}
    placed = []
    for seat, box in sorted(regions.items()):
        if (
            seat in seat_ids
            and isinstance(box, list)
            and len(box) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in box)
            and 0 <= box[0] < box[2] <= width
            and 0 <= box[1] < box[3] <= height
        ):
            x1, y1, x2, y2 = (float(v) for v in box)
            placed.append(Seat(seat, (x1 + x2) / 2, (y1 + y2) / 2, (x1, y1, x2, y2)))
        else:
            logger.warning("Bo qua o ghe %r: khong co trong so do lop hoac toa do sai.", seat)
    if not placed:
        raise ClassLayoutError("Tiet khong co o ghe hop le nao.")
    return SeatGrid(placed, image_size=(width, height))
