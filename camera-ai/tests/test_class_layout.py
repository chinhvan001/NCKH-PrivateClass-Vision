"""So do ghe cua tiet tu file tiet hien tai cua camera (web admin ghi luc bat dau tiet): ma ghe giong
web admin, chi ghe co o ve tren web duoc theo doi, file hong hoac cua tiet khac bi tu choi."""

import pytest

from src.config import ClassLayoutError, seat_id, session_seat_grid


def _order(**changes):
    order = {
        "session_id": "s1",
        "status": "running",
        "class_id": "c1",
        "row_count": 2,
        "column_count": 3,
        "seat_regions": {
            "image_width": 1280,
            "image_height": 720,
            "seats": {"S01": [100, 100, 300, 300], "S03": [700, 100, 900, 300]},
        },
    }
    return {**order, **changes}


def test_seat_ids_follow_web_admin():
    # Nhu backend/routes/class_routes.py: S{(row - 1) * column_count + column:02d}.
    ids = [seat_id(row, column, 3) for row in (1, 2) for column in (1, 2, 3)]
    assert ids == ["S01", "S02", "S03", "S04", "S05", "S06"]
    assert seat_id(10, 10, 10) == "S100"


def test_only_seats_drawn_on_the_web_are_tracked():
    grid = session_seat_grid(_order(), "s1")

    # Toa do theo anh luc ve, edge doi ve khung hinh bang fit_to
    assert [(seat.seat_id, seat.center_x, seat.region) for seat in grid.seats] == [
        ("S01", 200.0, (100.0, 100.0, 300.0, 300.0)),
        ("S03", 800.0, (700.0, 100.0, 900.0, 300.0)),
    ]
    assert grid.image_size == (1280, 720)


def test_bad_boxes_are_skipped_and_unusable_orders_raise():
    # S99 khong co trong so do 2x3, S03 nam ngoai anh: bo qua tung o, khong bo ca so do
    regions = {"image_width": 1280, "image_height": 720, "seats": {"S01": [100, 100, 300, 300], "S99": [0, 0, 10, 10]}}
    regions["seats"]["S03"] = [700, 100, 1300, 300]
    assert [seat.seat_id for seat in session_seat_grid(_order(seat_regions=regions), "s1").seats] == ["S01"]

    for order, message in [
        (None, "chua giao tiet"),
        (_order(session_id="s2"), "chua giao tiet"),  # web vua giao tiet khac cho camera
        (_order(row_count=0), "hang/cot"),
        (_order(column_count=10**9), "hang/cot"),  # file hong khong duoc bat edge sinh hang ty ghe
        (_order(seat_regions=None), "ve o ghe"),
        (_order(seat_regions={"image_width": 0, "image_height": 720, "seats": {}}), "kich thuoc anh"),
        (_order(seat_regions={"image_width": 1280, "image_height": 720, "seats": {"S01": [300, 1, 100, 2]}}), "hop le"),
    ]:
        with pytest.raises(ClassLayoutError, match=message):
            session_seat_grid(order, "s1")
