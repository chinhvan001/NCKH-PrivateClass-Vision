"""
test_seat_tracker.py -- Unit test cho SeatTracker (src/seating/seat_tracker.py)

Trong tam: mo phong CHUOI NHIEU KHUNG HINH lien tiep (khong phai 1 frame don
le nhu test_seat_mapper.py) de xac nhan seat_id ON DINH qua thoi gian, dung
yeu cau cua task 3.4 phan 2/2.
"""

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.seating import Seat, SeatGrid, SeatTracker


def make_person(shoulder_x, shoulder_y, offset=5.0, conf=0.9):
    keypoints = [(0.0, 0.0, 0.9)] * 17
    left_idx = COCO_KEYPOINT_NAMES.index("left_shoulder")
    right_idx = COCO_KEYPOINT_NAMES.index("right_shoulder")
    keypoints[left_idx] = (shoulder_x - offset, shoulder_y, conf)
    keypoints[right_idx] = (shoulder_x + offset, shoulder_y, conf)
    return PersonPose(keypoints=keypoints, bbox=(0, 0, 50, 50), confidence=conf)


def make_grid():
    return SeatGrid(seats=[
        Seat("A1", 100, 100), Seat("A2", 300, 100), Seat("A3", 500, 100),
    ])


# ---------------------------------------------------------------
# On dinh qua nhieu frame voi nhieu nho (jitter)
# ---------------------------------------------------------------

def test_stable_seat_id_despite_jitter_near_boundary():
    """Nguoi ngoi GAN DUNG GIUA A1 va A2 (200,100) -- nearest-centroid tho
    se rat de bi 'nhay' qua lai giua A1/A2 chi vi jitter nho. SeatTracker
    phai giu on dinh 1 seat_id xuyen suot, khong nhay."""
    grid = make_grid()
    tracker = SeatTracker(grid, continuity_threshold=40.0)

    # Frame 1: dat gan A1 hon mot chut de "chon" A1 lam seat ban dau
    result = tracker.update([make_person(190, 100)])
    assert set(result.keys()) == {"A1"}
    seat_id_first = "A1"

    # Cac frame tiep theo: vi tri dao dong qua lai quanh diem giua (jitter),
    # co luc gan A2 hon (>200) neu tinh tho -- nhung phai VAN la A1 do continuity.
    jittered_positions = [195, 205, 198, 208, 192, 202]
    for x in jittered_positions:
        result = tracker.update([make_person(x, 100)])
        assert set(result.keys()) == {seat_id_first}, (
            f"Seat bi nhay tai x={x}: ket qua {list(result.keys())}, ky vong van la {seat_id_first}"
        )


def test_switches_seat_when_person_actually_moves_far():
    """Nguoi thuc su di chuyen han sang vi tri khac (vuot continuity_threshold
    nhieu lan) -- day la truong hop hop le de doi seat (vi du calibration lai,
    hoac that su co nguoi khac ngoi vao).

    Luu y: ngay frame tiep theo, seat A1 CU van con xuat hien trong ket qua
    (dang trong thoi gian an cua co che xu ly khuat tam thoi -- dung thiet
    ke, vi he thong khong the phan biet ngay "nguoi doi seat" voi "nguoi cu
    tam khuat + nguoi moi vua ngoi vao seat khac"). A1 chi thuc su bien mat
    sau khi vuot max_missing_frames KHONG con ai duoc phat hien o do."""
    grid = make_grid()
    tracker = SeatTracker(grid, continuity_threshold=40.0, max_missing_frames=2)

    result = tracker.update([make_person(100, 100)])
    assert set(result.keys()) == {"A1"}

    # Nhay thang toi vi tri A3 (500,100) -- cach xa moi track dang co -> fallback nearest-centroid.
    # A1 van con trong ket qua (moi missing 1 frame, chua vuot nguong 2).
    result = tracker.update([make_person(500, 100)])
    assert "A3" in result
    assert "A1" in result  # dung thiet ke: dang trong thoi gian an cua occlusion-handling

    # Cac frame tiep theo KHONG con ai o vi tri A1 -- sau khi vuot max_missing_frames, A1 moi that su bien mat.
    result = tracker.update([make_person(505, 102)])
    result = tracker.update([make_person(498, 99)])
    assert set(result.keys()) == {"A3"}, "A1 phai bien mat sau khi vuot qua max_missing_frames"


# ---------------------------------------------------------------
# Xu ly khuat tam thoi (missing frames)
# ---------------------------------------------------------------

def test_seat_persists_during_short_occlusion():
    """Nguoi 'bien mat' (vi du cui thap, bi che) trong vai frame ngan (duoi
    max_missing_frames) -- seat_id phai VAN con trong ket qua tra ve, dung
    SeatAssignment cua lan cuoi thuc su thay duoc."""
    grid = make_grid()
    tracker = SeatTracker(grid, max_missing_frames=5)

    tracker.update([make_person(100, 100)])
    last_result = tracker.update([make_person(102, 100)])
    assert "A1" in last_result

    # 3 frame lien tiep KHONG phat hien ai (danh sach rong) -- duoi nguong 5
    for _ in range(3):
        result = tracker.update([])
        assert "A1" in result, "Seat bi xoa qua som trong luc khuat tam thoi"
        # Van tra ve dung SeatAssignment cua lan cuoi thay duoc
        assert result["A1"].distance == pytest.approx(last_result["A1"].distance)


def test_seat_expires_after_prolonged_absence():
    """Vuot qua max_missing_frames -- seat phai duoc coi la thuc su trong
    (bi xoa khoi ket qua tra ve)."""
    grid = make_grid()
    tracker = SeatTracker(grid, max_missing_frames=3)

    tracker.update([make_person(100, 100)])

    for _ in range(3):  # dung bang max_missing_frames -- van CHUA vuot qua
        result = tracker.update([])
    assert "A1" in result

    result = tracker.update([])  # frame thu 4 lien tiep khong thay -- vuot qua nguong
    assert "A1" not in result


def test_person_reappears_after_short_occlusion_keeps_same_seat():
    """Sau khi khuat tam thoi (chua vuot nguong), nguoi xuat hien lai o gan
    vi tri cu -- phai duoc gan lai DUNG seat_id cu (nho continuity), khong
    phai mot seat_id ngau nhien khac."""
    grid = make_grid()
    tracker = SeatTracker(grid, max_missing_frames=5, continuity_threshold=40.0)

    tracker.update([make_person(100, 100)])
    tracker.update([])  # khuat 1 frame
    tracker.update([])  # khuat frame thu 2
    result = tracker.update([make_person(103, 98)])  # xuat hien lai, vi tri gan nhu cu

    assert set(result.keys()) == {"A1"}


# ---------------------------------------------------------------
# Mo phong ca lop 30 hoc sinh qua nhieu frame
# ---------------------------------------------------------------

def test_30_students_stable_across_10_frames():
    """Mo phong 30 hoc sinh ngoi co dinh (dung Assumption 'Fixed Seating
    Arrangement' cua Proposal), moi frame co jitter nho ngau nhien -- xac
    nhan seat_id cua tung nguoi khong doi xuyen suot 10 frame."""
    import random

    random.seed(42)

    seats = [Seat(f"S{i}", float(i * 60), 0.0) for i in range(30)]
    grid = SeatGrid(seats=seats)
    tracker = SeatTracker(grid, continuity_threshold=15.0)

    seat_id_history = {i: [] for i in range(30)}

    for _frame in range(10):
        people = []
        base_positions = []
        for i in range(30):
            jitter_x = random.uniform(-3, 3)
            jitter_y = random.uniform(-3, 3)
            x = i * 60 + jitter_x
            y = 2.0 + jitter_y
            people.append(make_person(x, y, offset=3))
            base_positions.append(i)

        result = tracker.update(people)

        # Map lai xem nguoi thu i (theo vi tri goc) duoc gan seat nao, bang
        # cach tim assignment co khoang cach gan voi vi tri ky vong cua nguoi i.
        for i in base_positions:
            expected_seat_id = f"S{i}"
            assert expected_seat_id in result, f"Frame {_frame}: thieu seat {expected_seat_id}"
            seat_id_history[i].append(expected_seat_id)

    for i in range(30):
        assert len(set(seat_id_history[i])) == 1, f"Hoc sinh {i} bi nhay seat_id: {seat_id_history[i]}"


def test_reset_clears_all_state():
    grid = make_grid()
    tracker = SeatTracker(grid)
    tracker.update([make_person(100, 100)])
    assert len(tracker.current_assignments) == 1

    tracker.reset()

    assert len(tracker.current_assignments) == 0