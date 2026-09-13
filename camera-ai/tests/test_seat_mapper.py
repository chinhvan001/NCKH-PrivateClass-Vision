"""
test_seat_mapper.py -- Unit test cho assign_seats()/shoulder_midpoint()
(src/seating/seat_mapper.py)

Dung PersonPose gia lap (dan skeleton o cac vi tri khac nhau trong khung
hinh) de xac nhan gan dung seat_id theo nearest-centroid -- dung yeu cau cua
task 3.3 phan 1/2.
"""

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.seating import Seat, SeatGrid, assign_seats, shoulder_midpoint


def make_person(shoulder_x=None, shoulder_y=None, left_conf=0.9, right_conf=0.9, offset=0.0):
    """Tao 1 PersonPose gia lap voi 2 vai dat o vi tri chi dinh (trung diem
    se la (shoulder_x, shoulder_y)), cac keypoint khac dat gia tri bat ky
    (khong anh huong den test seating)."""
    keypoints = [(0.0, 0.0, 0.9)] * 17  # gia tri mac dinh cho 17 keypoint
    left_idx = COCO_KEYPOINT_NAMES.index("left_shoulder")
    right_idx = COCO_KEYPOINT_NAMES.index("right_shoulder")

    if shoulder_x is not None:
        keypoints[left_idx] = (shoulder_x - offset, shoulder_y, left_conf)
        keypoints[right_idx] = (shoulder_x + offset, shoulder_y, right_conf)

    return PersonPose(keypoints=keypoints, bbox=(0, 0, 50, 50), confidence=0.9)


# ---------------------------------------------------------------
# shoulder_midpoint()
# ---------------------------------------------------------------

def test_shoulder_midpoint_both_shoulders_confident():
    person = make_person(shoulder_x=100, shoulder_y=200, offset=10)
    mid = shoulder_midpoint(person)
    assert mid == pytest.approx((100.0, 200.0))


def test_shoulder_midpoint_only_left_confident():
    person = make_person(shoulder_x=100, shoulder_y=200, offset=10, right_conf=0.05)
    mid = shoulder_midpoint(person)
    # Chi con left_shoulder dang tin cay -> tra ve dung toa do left_shoulder (90, 200)
    assert mid == pytest.approx((90.0, 200.0))


def test_shoulder_midpoint_both_low_confidence_returns_none():
    person = make_person(shoulder_x=100, shoulder_y=200, offset=10, left_conf=0.05, right_conf=0.05)
    assert shoulder_midpoint(person) is None


# ---------------------------------------------------------------
# assign_seats() -- dan skeleton o nhieu vi tri khac nhau
# ---------------------------------------------------------------

def make_grid():
    """Luoi 3x2 = 6 ghe, mo phong mot goc nho cua lop hoc."""
    return SeatGrid(seats=[
        Seat("R1C1", 100, 100), Seat("R1C2", 300, 100), Seat("R1C3", 500, 100),
        Seat("R2C1", 100, 300), Seat("R2C2", 300, 300), Seat("R2C3", 500, 300),
    ])


def test_assign_seats_multiple_people_different_positions():
    grid = make_grid()
    people = [
        make_person(shoulder_x=105, shoulder_y=95, offset=5),   # gan R1C1
        make_person(shoulder_x=310, shoulder_y=105, offset=5),  # gan R1C2
        make_person(shoulder_x=495, shoulder_y=305, offset=5),  # gan R2C3
    ]

    assignments = assign_seats(people, grid)

    seat_ids = {a.seat_id for a in assignments}
    assert seat_ids == {"R1C1", "R1C2", "R2C3"}
    assert len(assignments) == 3


def test_assign_seats_person_with_no_shoulder_data_is_skipped():
    grid = make_grid()
    people = [
        make_person(shoulder_x=100, shoulder_y=100, offset=5),
        make_person(shoulder_x=None),  # khong co du lieu vai -> bi bo qua
    ]

    assignments = assign_seats(people, grid)

    assert len(assignments) == 1
    assert assignments[0].seat_id == "R1C1"


def test_assign_seats_duplicate_seat_keeps_closest_only():
    """2 nguoi cung gan vao 1 seat (do dung sat nhau) -- chi giu nguoi gan
    tam seat hon, khong tao 2 assignment cho cung seat_id."""
    grid = SeatGrid(seats=[Seat("A1", 100, 100)])
    people = [
        make_person(shoulder_x=102, shoulder_y=100, offset=1),  # rat gan tam seat
        make_person(shoulder_x=140, shoulder_y=100, offset=1),  # xa hon
    ]

    assignments = assign_seats(people, grid)

    assert len(assignments) == 1
    assert assignments[0].person.keypoints[COCO_KEYPOINT_NAMES.index("left_shoulder")][0] == pytest.approx(101.0)


def test_assign_seats_max_distance_excludes_far_person():
    grid = SeatGrid(seats=[Seat("A1", 100, 100)])
    far_person = make_person(shoulder_x=500, shoulder_y=500, offset=5)

    assignments_no_limit = assign_seats([far_person], grid)
    assert len(assignments_no_limit) == 1  # khong gioi han -> van gan (du xa)

    assignments_with_limit = assign_seats([far_person], grid, max_distance=50.0)
    assert len(assignments_with_limit) == 0  # vuot qua 50px -> khong gan


def test_assign_seats_empty_people_list_returns_empty():
    grid = make_grid()
    assert assign_seats([], grid) == []


def test_assign_seats_empty_grid_returns_empty():
    person = make_person(shoulder_x=100, shoulder_y=100, offset=5)
    assert assign_seats([person], SeatGrid(seats=[])) == []


def test_assign_seats_30_people_no_seat_reused():
    """Mo phong gan dung quy mo lop hoc: 30 nguoi, 30 ghe rieng biet, moi
    nguoi dung dung truoc 1 ghe -- xac nhan khong seat nao bi gan 2 lan va
    khong nguoi nao bi bo sot."""
    seats = [Seat(f"S{i}", float(i * 60), 0.0) for i in range(30)]
    grid = SeatGrid(seats=seats)
    people = [make_person(shoulder_x=float(i * 60), shoulder_y=2.0, offset=3) for i in range(30)]

    assignments = assign_seats(people, grid)

    assert len(assignments) == 30
    assert len({a.seat_id for a in assignments}) == 30  # khong trung seat nao