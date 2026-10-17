"""So do lop tu Firestore: chi doc hang/cot (student_id khong toi edge), du phong seat_id "S{n}"
cua nhanh Web, loi doc va lop khong ton tai."""

import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError
from src.config import ClassLayoutError, load_class_seat_grid
from src.seating import CornerSeats

CORNERS = CornerSeats((100.0, 600.0), (900.0, 600.0), (700.0, 200.0), (300.0, 200.0))


def test_reads_only_rows_and_columns_from_class_and_seat_documents():
    client = FakeFirestore()
    client.document("classes/c1").set({"class_name": "11B2", "row_count": 2, "column_count": 2, "teacher_id": "t1"})
    for seat_id, row, column in [("S01-c1", 1, 1), ("S02-c1", 1, 2), ("S03-c1", 2, 1), ("S04-c1", 2, 2)]:
        client.document(f"classes/c1/seats/{seat_id}").set(
            {"row": row, "column": column, "student_id": f"student-{seat_id}", "status": "assigned"}
        )

    grid = load_class_seat_grid(client, "c1", CORNERS)

    assert sorted(seat.seat_id for seat in grid.seats) == ["S01-c1", "S02-c1", "S03-c1", "S04-c1"]
    assert (grid.get_seat("S04-c1").center_x, grid.get_seat("S04-c1").center_y) == pytest.approx((700.0, 200.0))
    assert client.reads and all(set(data) <= {"row_count", "column_count", "row", "column"} for data in client.reads)


def test_falls_back_to_web_branch_seat_ids_when_class_has_no_seat_documents():
    client = FakeFirestore()
    client.document("classes/c1").set({"row_number": 2, "column_number": 3, "seat_assignments": {"S1": "student-1"}})

    grid = load_class_seat_grid(client, "c1", CORNERS)

    assert [seat.seat_id for seat in grid.seats] == ["S1", "S2", "S3", "S4", "S5", "S6"]  # theo hang, nhu nhanh Web
    assert (grid.get_seat("S6").center_x, grid.get_seat("S6").center_y) == pytest.approx((700.0, 200.0))
    assert all("seat_assignments" not in data for data in client.reads)


def test_missing_class_bad_counts_and_read_failures_raise_class_layout_error():
    client = FakeFirestore()
    with pytest.raises(ClassLayoutError, match="classes/c1"):
        load_class_seat_grid(client, "c1", CORNERS)
    for rows in (0, 10**9):  # 10**9: document hong khong duoc bat edge sinh hang ty ghe
        client.document("classes/c1").set({"row_count": rows, "column_count": 3})
        with pytest.raises(ClassLayoutError, match="hang/cot"):
            load_class_seat_grid(client, "c1", CORNERS)

    class Offline(FakeFirestore):
        def document(self, path):
            raise FakeFirestoreError(503, "unavailable while reading student-1")

    with pytest.raises(ClassLayoutError) as error:
        load_class_seat_grid(Offline(), "c1", CORNERS)
    assert "student-1" not in str(error.value)
