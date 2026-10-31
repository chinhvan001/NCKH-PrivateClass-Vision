"""So do lop tu Firestore: chi doc so hang/cot (seat_map voi student_id khong toi edge), ma ghe
giong web admin, loi doc va lop khong ton tai."""

import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError
from src.config import ClassLayoutError, load_camera_class, load_camera_setting, load_class_seat_grid
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


def _regions(client, **changes):
    data = {
        "class_id": "c1",
        "image_width": 1280,
        "image_height": 720,
        "seats": {"S01": [100, 100, 300, 300], "S03": [700, 100, 900, 300]},
        "updated_by": "admin-uid",
    }
    client.document("seat_regions/cam-1").set({**data, **changes})


def test_regions_drawn_on_the_web_replace_corner_seats():
    client = FakeFirestore()
    client.document("classes2/c1").set({"row_count": 2, "column_count": 3})
    _regions(client)

    grid = load_class_seat_grid(client, "c1", None, "cam-1")

    # Chi ghe da ve duoc theo doi; toa do theo anh luc ve, edge doi ve khung hinh bang fit_to
    assert [(seat.seat_id, seat.center_x, seat.region) for seat in grid.seats] == [
        ("S01", 200.0, (100.0, 100.0, 300.0, 300.0)),
        ("S03", 800.0, (700.0, 100.0, 900.0, 300.0)),
    ]
    assert grid.image_size == (1280, 720)
    assert all("updated_by" not in data for data in client.reads)


def test_regions_for_another_class_fall_back_to_corners_and_bad_boxes_are_skipped():
    client = FakeFirestore()
    client.document("classes2/c1").set({"row_count": 2, "column_count": 3})
    _regions(client, class_id="c2")
    assert len(load_class_seat_grid(client, "c1", CORNERS, "cam-1").seats) == 6  # camera da doi sang lop khac
    with pytest.raises(ClassLayoutError, match="ve o ghe"):
        load_class_seat_grid(client, "c1", None, "cam-1")

    # S99 khong co trong so do 2x3, S03 nam ngoai anh: bo qua tung o, khong bo ca so do
    _regions(client, seats={"S01": [100, 100, 300, 300], "S99": [0, 0, 10, 10], "S03": [700, 100, 1300, 300]})
    assert [seat.seat_id for seat in load_class_seat_grid(client, "c1", None, "cam-1").seats] == ["S01"]
    _regions(client, seats={"S01": [300, 100, 100, 300]})
    with pytest.raises(ClassLayoutError, match="khong co o ghe hop le"):
        load_class_seat_grid(client, "c1", CORNERS, "cam-1")


def test_camera_source_is_read_alone_from_the_camera_added_on_the_web_admin():
    client = FakeFirestore()
    assert load_camera_setting(client, "CAM-1", "source") is None  # chua them camera tren web
    client.document("camera_configs/CAM-1").set({"source": "rtsp://admin:pw@10.0.0.5:554/stream1", "updated_by": "a"})
    assert load_camera_setting(client, "CAM-1", "source") == "rtsp://admin:pw@10.0.0.5:554/stream1"
    assert client.reads[-1] == {"source": "rtsp://admin:pw@10.0.0.5:554/stream1"}  # khong doc uid admin


def test_camera_class_is_the_class_whose_camera_id_is_this_camera_without_its_seat_map():
    client = FakeFirestore()
    seat_map = {"S01": {"student_id": "an"}}
    client.document("classes2/c2").set({"class_name": "11B3", "camera_id": "CAM-2", "seat_map": seat_map})
    assert load_camera_class(client, "CAM-1") is None  # chua gan lop tren web
    client.document("classes2/c1").set({"class_name": "11B2", "camera_id": "CAM-1", "seat_map": seat_map})
    assert load_camera_class(client, "CAM-1") == "c1"
    assert "an" not in str(client.reads[-1])  # chi lay field camera_id, khong bao gio seat_map
    client.document("classes2/c3").set({"camera_id": "CAM-1"})
    with pytest.raises(ClassLayoutError, match="Nhieu lop"):
        load_camera_class(client, "CAM-1")
