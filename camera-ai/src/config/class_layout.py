"""So do ghe cua lop tu Firestore: chi doc so hang/cot, khong bao gio lay seat_map/student_id.

Web admin luu lop o ``classes2/{class_id}`` voi ``row_count``, ``column_count`` va
``seat_map`` (ghe -> hoc sinh). Ma ghe co dinh theo vi tri: ``S{n:02d}`` voi n dem
theo hang tu 1 (``S01``, ``S02``, ...; ``backend/routes/class_routes.py``), nen edge
tu sinh ma ghe tu so hang/cot va doc lop voi ``field_paths`` -- ``seat_map`` khong ve
toi edge. Vi tri ghe tren anh lay tu 4 ghe goc trong config local
(``seating.corner_seats``). Client Firestore truyen vao (``sync.firestore_client_from_env``
hoac fake trong test).
"""

from __future__ import annotations

from typing import Any

from src.seating import CornerSeats, SeatGrid, SeatGridError, layout_seat_grid

CLASS_COLLECTION = "classes2"
# Schema cua nhom dung row_count/column_count; document cu cua nhanh Web ghi row_number/column_number.
_COUNT_FIELDS = ["row_count", "column_count", "row_number", "column_number"]
MAX_GRID_SIDE = 50  # document lop hong/bi sua khong duoc bat edge tao hang trieu ghe


class ClassLayoutError(RuntimeError):
    """Khong doc duoc hoac khong dung duoc so do ghe cua lop."""


def seat_id(row: int, column: int, column_count: int) -> str:
    """Ma ghe giong web admin: ``S01`` la hang 1 cot 1, dem theo hang."""
    return f"S{(row - 1) * column_count + column:02d}"


def load_class_seat_grid(client: Any, class_id: str, corners: CornerSeats) -> SeatGrid:
    path = f"{CLASS_COLLECTION}/{class_id}"
    try:
        snapshot = client.document(path).get(field_paths=_COUNT_FIELDS)
    except Exception as error:  # chi ten loi: message cua server co the lap lai du lieu
        raise ClassLayoutError(f"Khong doc duoc so do lop tu Firestore ({type(error).__name__}).") from error
    if not snapshot.exists:
        raise ClassLayoutError(f"Khong co document {path}.")
    data = snapshot.to_dict() or {}
    rows = data.get("row_count", data.get("row_number"))
    columns = data.get("column_count", data.get("column_number"))
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_GRID_SIDE
        for value in (rows, columns)
    ):
        raise ClassLayoutError(f"{path} thieu so hang/cot hop le (1-{MAX_GRID_SIDE}).")
    seats = [
        (seat_id(row, column, columns), row, column) for row in range(1, rows + 1) for column in range(1, columns + 1)
    ]
    try:
        return layout_seat_grid(seats, rows, columns, corners)
    except SeatGridError as error:
        raise ClassLayoutError(str(error)) from error
