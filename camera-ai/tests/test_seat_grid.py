"""
test_seat_grid.py -- Unit test cho SeatGrid/Seat (src/seating/seat_grid.py)
"""

import json

import pytest

from src.seating import Seat, SeatGrid, SeatGridError


def test_find_nearest_seat_basic():
    grid = SeatGrid(seats=[
        Seat("A1", 100, 100),
        Seat("A2", 300, 100),
        Seat("A3", 500, 100),
    ])
    nearest = grid.find_nearest_seat(310, 105)
    assert nearest.seat_id == "A2"


def test_find_nearest_seat_empty_grid_returns_none():
    grid = SeatGrid(seats=[])
    assert grid.find_nearest_seat(100, 100) is None


def test_duplicate_seat_id_raises_error():
    with pytest.raises(SeatGridError):
        SeatGrid(seats=[Seat("A1", 0, 0), Seat("A1", 100, 100)])


def test_from_json_file_valid(tmp_path):
    data = {
        "seats": [
            {"seat_id": "A1", "center_x": 120, "center_y": 340},
            {"seat_id": "A2", "center_x": 260, "center_y": 340},
        ]
    }
    path = tmp_path / "grid.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    grid = SeatGrid.from_json_file(path)

    assert len(grid.seats) == 2
    assert grid.seats[0].seat_id == "A1"
    assert grid.seats[0].center_x == 120
    assert grid.seats[1].center_y == 340


def test_from_json_file_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(SeatGridError, match="Khong tim thay"):
        SeatGrid.from_json_file(tmp_path / "khong_ton_tai.json")


def test_from_json_file_invalid_json_raises_clear_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{ khong phai json hop le", encoding="utf-8")
    with pytest.raises(SeatGridError, match="khong phai JSON hop le"):
        SeatGrid.from_json_file(path)


def test_from_json_file_missing_field_raises_clear_error(tmp_path):
    data = {"seats": [{"seat_id": "A1", "center_x": 120}]}  # thieu center_y
    path = tmp_path / "grid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SeatGridError, match="thieu truong bat buoc"):
        SeatGrid.from_json_file(path)


def test_from_json_file_missing_seats_key_raises_clear_error(tmp_path):
    path = tmp_path / "grid.json"
    path.write_text(json.dumps({"not_seats": []}), encoding="utf-8")
    with pytest.raises(SeatGridError, match="thieu truong 'seats'"):
        SeatGrid.from_json_file(path)


def test_round_trip_to_json_and_back(tmp_path):
    original = SeatGrid(seats=[Seat("A1", 10, 20), Seat("B2", 30, 40)])
    path = tmp_path / "grid.json"
    original.to_json_file(path)

    loaded = SeatGrid.from_json_file(path)

    assert len(loaded.seats) == 2
    assert {s.seat_id for s in loaded.seats} == {"A1", "B2"}
    a1 = next(s for s in loaded.seats if s.seat_id == "A1")
    assert a1.center_x == 10
    assert a1.center_y == 20