"""So do ghe cua lop tu Firestore: chi doc so hang/cot, khong bao gio lay seat_map/student_id.

Web admin luu lop o ``classes2/{class_id}`` voi ``row_count``, ``column_count`` va
``seat_map`` (ghe -> hoc sinh). Ma ghe co dinh theo vi tri: ``S{n:02d}`` voi n dem
theo hang tu 1 (``S01``, ``S02``, ...; ``backend/routes/class_routes.py``), nen edge
tu sinh ma ghe tu so hang/cot va doc lop voi ``field_paths`` -- ``seat_map`` khong ve
toi edge. Vi tri ghe tren anh: o chu nhat admin ve tren trang Quan ly camera
(``seat_regions/{camera_id}``, ve cho dung lop nay), neu khong co thi 4 ghe goc trong
config local (``seating.corner_seats``). Client Firestore truyen vao
(``sync.firestore_client_from_env`` hoac fake trong test).
"""

from __future__ import annotations

import logging
import math
from typing import Any

from src.seating import CornerSeats, Seat, SeatGrid, SeatGridError, layout_seat_grid

logger = logging.getLogger("camera_ai.seating")

CLASS_COLLECTION = "classes2"
REGION_COLLECTION = "seat_regions"
# Schema cua nhom dung row_count/column_count; document cu cua nhanh Web ghi row_number/column_number.
_COUNT_FIELDS = ["row_count", "column_count", "row_number", "column_number"]
_REGION_FIELDS = ["class_id", "image_width", "image_height", "seats"]  # khong doc updated_by (uid admin)
MAX_GRID_SIDE = 50  # document lop hong/bi sua khong duoc bat edge tao hang trieu ghe
MAX_IMAGE_SIDE = 10000


class ClassLayoutError(RuntimeError):
    """Khong doc duoc hoac khong dung duoc so do ghe cua lop."""


def seat_id(row: int, column: int, column_count: int) -> str:
    """Ma ghe giong web admin: ``S01`` la hang 1 cot 1, dem theo hang."""
    return f"S{(row - 1) * column_count + column:02d}"


def _read(client: Any, path: str, field_paths: list[str]) -> Any:
    try:
        return client.document(path).get(field_paths=field_paths)
    except Exception as error:  # chi ten loi: message cua server co the lap lai du lieu
        raise ClassLayoutError(f"Khong doc duoc {path} tu Firestore ({type(error).__name__}).") from error


def _size(value: Any, limit: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= limit


def load_class_seat_grid(
    client: Any, class_id: str, corners: CornerSeats | None, camera_id: str | None = None
) -> SeatGrid:
    path = f"{CLASS_COLLECTION}/{class_id}"
    snapshot = _read(client, path, _COUNT_FIELDS)
    if not snapshot.exists:
        raise ClassLayoutError(f"Khong co document {path}.")
    data = snapshot.to_dict() or {}
    rows = data.get("row_count", data.get("row_number"))
    columns = data.get("column_count", data.get("column_number"))
    if not (_size(rows, MAX_GRID_SIDE) and _size(columns, MAX_GRID_SIDE)):
        raise ClassLayoutError(f"{path} thieu so hang/cot hop le (1-{MAX_GRID_SIDE}).")
    seats = [
        (seat_id(row, column, columns), row, column) for row in range(1, rows + 1) for column in range(1, columns + 1)
    ]
    if camera_id is not None:
        grid = _region_grid(client, camera_id, class_id, {seat for seat, _, _ in seats})
        if grid is not None:
            return grid
    if corners is None:
        raise ClassLayoutError("Chua co vi tri ghe: ve o ghe tren trang Quan ly camera hoac khai bao 4 ghe goc.")
    try:
        return layout_seat_grid(seats, rows, columns, corners)
    except SeatGridError as error:
        raise ClassLayoutError(str(error)) from error


def _region_grid(client: Any, camera_id: str, class_id: str, seat_ids: set[str]) -> SeatGrid | None:
    """O ghe admin ve tren anh chup tu camera; None neu chua ve hoac ve cho lop khac.
    Ghe chua ve khong duoc theo doi; o hong (sua tay trong Firestore) bi bo qua."""
    path = f"{REGION_COLLECTION}/{camera_id}"
    snapshot = _read(client, path, _REGION_FIELDS)
    data = (snapshot.to_dict() or {}) if snapshot.exists else {}
    if data.get("class_id") != class_id:
        return None
    width, height = data.get("image_width"), data.get("image_height")
    if not (_size(width, MAX_IMAGE_SIDE) and _size(height, MAX_IMAGE_SIDE)):
        raise ClassLayoutError(f"{path} thieu kich thuoc anh hop le.")
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
            logger.warning("Bo qua o ghe %r trong %s: khong co trong so do lop hoac toa do sai.", seat, path)
    if not placed:
        raise ClassLayoutError(f"{path} khong co o ghe hop le nao.")
    return SeatGrid(placed, image_size=(width, height))
