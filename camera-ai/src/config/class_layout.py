"""So do ghe cua lop tu Firestore: chi doc hang/cot, khong bao gio lay student_id.

``classes/{class_id}`` cho so hang/cot, ``classes/{class_id}/seats/{seat_id}`` cho
hang/cot tung ghe. Ca hai deu doc co chon field (``field_paths``/``select``) nen
student_id cua ghe va cac field khac cua lop khong ve toi edge. Vi tri ghe tren
anh lay tu 4 ghe goc trong config local (``seating.corner_seats``). Client
Firestore truyen vao (``sync.firestore_client_from_env`` hoac fake trong test).
"""

from __future__ import annotations

from itertools import islice
from typing import Any

from src.seating import CornerSeats, SeatGrid, SeatGridError, layout_seat_grid

# Schema cua nhom dung row_count/column_count; nhanh Web hien tai ghi row_number/column_number.
_COUNT_FIELDS = ["row_count", "column_count", "row_number", "column_number"]
MAX_GRID_SIDE = 50  # document lop hong/bi sua khong duoc bat edge tao hang trieu ghe


class ClassLayoutError(RuntimeError):
    """Khong doc duoc hoac khong dung duoc so do ghe cua lop."""


def load_class_seat_grid(client: Any, class_id: str, corners: CornerSeats) -> SeatGrid:
    try:
        snapshot = client.document(f"classes/{class_id}").get(field_paths=_COUNT_FIELDS)
    except Exception as error:  # chi ten loi: message cua server co the lap lai du lieu
        raise ClassLayoutError(f"Khong doc duoc so do lop tu Firestore ({type(error).__name__}).") from error
    if not snapshot.exists:
        raise ClassLayoutError(f"Khong co document classes/{class_id}.")
    data = snapshot.to_dict() or {}
    rows = data.get("row_count", data.get("row_number"))
    columns = data.get("column_count", data.get("column_number"))
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_GRID_SIDE
        for value in (rows, columns)
    ):
        raise ClassLayoutError(f"classes/{class_id} thieu so hang/cot hop le (1-{MAX_GRID_SIDE}).")
    try:
        # Chi doc toi da so ghe cua so do; document thua (du lieu hong) khong duoc lam day RAM.
        query = client.collection(f"classes/{class_id}/seats").select(["row", "column"])
        seat_docs = list(islice(query.stream(), rows * columns))
    except Exception as error:
        raise ClassLayoutError(f"Khong doc duoc ghe cua lop tu Firestore ({type(error).__name__}).") from error
    if seat_docs:
        seats = [(doc.id, *((doc.to_dict() or {}).get(key) for key in ("row", "column"))) for doc in seat_docs]
    else:
        # ponytail: nhanh Web chua ghi classes/{c}/seats, chi co seat_assignments {"S1": student_id};
        # sinh seat_id "S{n}" theo hang giong Web. Bo nhanh nay khi Web/App ghi subcollection seats.
        seats = [
            (f"S{(row - 1) * columns + column}", row, column)
            for row in range(1, rows + 1)
            for column in range(1, columns + 1)
        ]
    try:
        return layout_seat_grid(seats, rows, columns, corners)
    except SeatGridError as error:
        raise ClassLayoutError(str(error)) from error
