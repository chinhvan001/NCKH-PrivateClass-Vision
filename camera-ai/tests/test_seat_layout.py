"""Toa do ghe tu hang/cot + 4 ghe goc: dung o 4 goc, phoi canh o giua, so do 1 hang, ghe hong bi bo."""

import pytest

from src.seating import CornerSeats, SeatGridError, layout_seat_grid

# Camera dat phia truoc: hang 1 gan (rong, o duoi anh), hang cuoi xa (hep, o tren anh).
TRAPEZOID = CornerSeats((100.0, 600.0), (900.0, 600.0), (700.0, 200.0), (300.0, 200.0))


def _centers(grid):
    return {seat.seat_id: (round(seat.center_x, 1), round(seat.center_y, 1)) for seat in grid.seats}


def test_corner_seats_land_on_calibrated_points_and_far_rows_are_compressed():
    seats = [(f"r{r}c{c}", r, c) for r in (1, 2, 3) for c in (1, 2, 3)]
    centers = _centers(layout_seat_grid(seats, 3, 3, TRAPEZOID))

    assert centers["r1c1"] == (100.0, 600.0)
    assert centers["r1c3"] == (900.0, 600.0)
    assert centers["r3c3"] == (700.0, 200.0)
    assert centers["r3c1"] == (300.0, 200.0)
    assert centers["r1c2"][0] == pytest.approx(500.0) and centers["r3c2"][0] == pytest.approx(500.0)
    # Phoi canh: hang giua nam gan hang xa hon (tren duong trung binh 400), khong phai noi suy tuyen tinh.
    assert centers["r2c2"][1] < 400.0


def test_single_row_class_interpolates_along_first_row():
    centers = _centers(layout_seat_grid([("S1", 1, 1), ("S2", 1, 2), ("S3", 1, 3)], 1, 3, TRAPEZOID))
    assert centers == {"S1": (100.0, 600.0), "S2": (500.0, 600.0), "S3": (900.0, 600.0)}


def test_bad_or_out_of_grid_seats_are_skipped_and_empty_layout_is_rejected():
    grid = layout_seat_grid([("S1", "01", "02"), ("bad", "x", 1), ("far", 9, 1), ("unassigned", 0, 0)], 2, 2, TRAPEZOID)
    assert [seat.seat_id for seat in grid.seats] == ["S1"]  # "01"/"02" la chuoi so hop le
    with pytest.raises(SeatGridError):
        layout_seat_grid([("far", 9, 1)], 2, 2, TRAPEZOID)
    with pytest.raises(SeatGridError):
        layout_seat_grid([("S1", 1, 1)], 2, 2, CornerSeats((0, 0), (1, 1), (2, 2), (3, 3)))  # 4 diem thang hang
    swapped = CornerSeats((100.0, 600.0), (900.0, 600.0), (300.0, 200.0), (700.0, 200.0))  # nham 2 goc hang cuoi
    with pytest.raises(SeatGridError):
        layout_seat_grid([("S1", 1, 1)], 2, 2, swapped)
