"""So do lop tu Firestore: chi doc so hang/cot (seat_map voi student_id khong toi edge), ma ghe
giong web admin, loi doc va lop khong ton tai."""

import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError
from src.config import ClassLayoutError, load_class_seat_grid
from src.seating import CornerSeats

CORNERS = CornerSeats((100.0, 600.0), (900.0, 600.0), (700.0, 200.0), (300.0, 200.0))


def test_seat_ids_follow_web_admin_and_class_is_read_without_seat_map():
    client = FakeFirestore()
    client.document("classes2/c1").set(
        {
            "class_name": "11B2",
            "row_count": 2,
            "column_count": 3,
            "teacher_id": "t1",
            "seat_map": {"S01": {"seat_id": "S01", "row": 1, "column": 1, "student_id": "student-1"}},
        }
    )

    grid = load_class_seat_grid(client, "c1", CORNERS)

    # Nhu backend/routes/class_routes.py: S{(row - 1) * column_count + column:02d}.
    assert [seat.seat_id for seat in grid.seats] == ["S01", "S02", "S03", "S04", "S05", "S06"]
    assert (grid.get_seat("S06").center_x, grid.get_seat("S06").center_y) == pytest.approx((700.0, 200.0))
    assert client.reads and all(set(data) <= {"row_count", "column_count"} for data in client.reads)


def test_older_class_documents_with_row_number_still_load():
    client = FakeFirestore()
    client.document("classes2/c1").set({"row_number": 1, "column_number": 2})
    assert [seat.seat_id for seat in load_class_seat_grid(client, "c1", CORNERS).seats] == ["S01", "S02"]


def test_missing_class_bad_counts_and_read_failures_raise_class_layout_error():
    client = FakeFirestore()
    with pytest.raises(ClassLayoutError, match="classes2/c1"):
        load_class_seat_grid(client, "c1", CORNERS)
    for rows in (0, 10**9):  # 10**9: document hong khong duoc bat edge sinh hang ty ghe
        client.document("classes2/c1").set({"row_count": rows, "column_count": 3})
        with pytest.raises(ClassLayoutError, match="hang/cot"):
            load_class_seat_grid(client, "c1", CORNERS)

    class Offline(FakeFirestore):
        def document(self, path):
            raise FakeFirestoreError(503, "unavailable while reading student-1")

    with pytest.raises(ClassLayoutError) as error:
        load_class_seat_grid(Offline(), "c1", CORNERS)
    assert "student-1" not in str(error.value)
