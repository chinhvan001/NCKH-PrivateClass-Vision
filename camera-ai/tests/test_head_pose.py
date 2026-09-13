"""
test_head_pose.py -- Unit test cho estimate_head_pose() (src/engagement/head_pose.py)

Chien luoc kiem thu: vi khong co model/webcam that trong moi truong test, ta
KHONG THE kiem tra do chinh xac thuc te tren khuon mat that. Thay vao do, bai
test dung phuong phap ROUND-TRIP: dung mot goc yaw/pitch/roll BIET TRUOC, xay
dung ma tran xoay 3x3 tuong ung bang cong thuc luong giac chuan, dua qua
estimate_head_pose(), va kiem tra ket qua giai ma co khop voi goc ban dau
khong. Day la cach xac minh CO SO TOAN HOC cua cong thuc phan tich (dung thu
tu YZX, khong bi nham truc, xu ly dung gimbal lock) -- KHONG xac minh duoc quy
uoc dau thuc te cua MediaPipe (xem canh bao trong docstring cua head_pose.py).
"""

import math

import numpy as np
import pytest

from src.engagement import HeadPose, estimate_head_pose, estimate_head_pose_for_face


def rot_x(deg: float) -> np.ndarray:
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(deg: float) -> np.ndarray:
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(deg: float) -> np.ndarray:
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def build_matrix(pitch: float, yaw: float, roll: float) -> np.ndarray:
    """Dung ma tran 3x3 tuong ung voi bo (pitch, yaw, roll) mong muon, theo
    dung cong thuc nghich dao cua estimate_head_pose() (da xac dinh bang thuc
    nghiem round-trip khi phat trien module nay): R = Ry(-yaw) @ Rz(-roll) @ Rx(-pitch).
    """
    return rot_y(-yaw) @ rot_z(-roll) @ rot_x(-pitch)


def build_4x4(pitch: float, yaw: float, roll: float) -> np.ndarray:
    """Nhu build_matrix() nhung tra ve ma tran 4x4 (giong dinh dang that cua
    MediaPipe facial_transformation_matrixes) de test ca viec cat [:3, :3] dung."""
    m = np.eye(4)
    m[:3, :3] = build_matrix(pitch, yaw, roll)
    m[:3, 3] = [10.0, -5.0, 2.0]  # phan tinh tien gia lap, phai bi bo qua
    return m


def assert_pose_close(pose: HeadPose, pitch: float, yaw: float, roll: float, tol=1e-6):
    assert pose.pitch == pytest.approx(pitch, abs=tol)
    assert pose.yaw == pytest.approx(yaw, abs=tol)
    assert pose.roll == pytest.approx(roll, abs=tol)


def test_identity_matrix_gives_zero_pose():
    pose = estimate_head_pose(np.eye(3))
    assert_pose_close(pose, 0.0, 0.0, 0.0)


def test_identity_4x4_gives_zero_pose():
    pose = estimate_head_pose(np.eye(4))
    assert_pose_close(pose, 0.0, 0.0, 0.0)


@pytest.mark.parametrize("pitch,yaw,roll", [
    (20, 0, 0),
    (0, 30, 0),
    (0, 0, 15),
    (-20, 0, 0),
    (0, -30, 0),
    (0, 0, -15),
])
def test_single_axis_rotation_recovered_exactly(pitch, yaw, roll):
    """Khi chi 1 truc xoay, thu tu phan tich (YZX vs XYZ) khong anh huong ket
    qua -- day la test co ban nhat, xac nhan truc/dau khop voi dinh nghia cua
    build_matrix()."""
    matrix = build_matrix(pitch, yaw, roll)
    pose = estimate_head_pose(matrix)
    assert_pose_close(pose, pitch, yaw, roll, tol=1e-4)


@pytest.mark.parametrize("pitch,yaw,roll", [
    (15, 25, 10),
    (-10, 40, -5),
    (30, -20, 20),
    (5, 5, 5),
    (-45, 45, -30),
])
def test_combined_rotation_round_trip(pitch, yaw, roll):
    """Ca 3 truc cung xoay dong thoi -- day la test quan trong nhat, xac nhan
    dung THU TU PHAN TICH YZX (khac voi XYZ thong thuong), vi day la truong
    hop de sai nhat neu dung nham thu tu."""
    matrix = build_matrix(pitch, yaw, roll)
    pose = estimate_head_pose(matrix)
    assert_pose_close(pose, pitch, yaw, roll, tol=1e-4)


def test_4x4_matrix_ignores_translation_part():
    matrix = build_4x4(15, 25, 10)
    pose = estimate_head_pose(matrix)
    assert_pose_close(pose, 15, 25, 10, tol=1e-4)


def test_none_raises_value_error():
    with pytest.raises(ValueError):
        estimate_head_pose(None)


def test_gimbal_lock_positive_does_not_crash():
    # r[1,0] = 1 -- truong hop bien, khong duoc raise loi toan hoc (vi du
    # domain error cua asin/acos), phai tra ve mot HeadPose hop le.
    matrix = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
    pose = estimate_head_pose(matrix)
    assert isinstance(pose, HeadPose)
    assert not math.isnan(pose.yaw)
    assert not math.isnan(pose.pitch)
    assert not math.isnan(pose.roll)


def test_gimbal_lock_negative_does_not_crash():
    matrix = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)
    pose = estimate_head_pose(matrix)
    assert isinstance(pose, HeadPose)
    assert not math.isnan(pose.yaw)
    assert not math.isnan(pose.pitch)
    assert not math.isnan(pose.roll)


class _FakeFace:
    """Gia lap FaceLandmarks (module detection/) chi voi thuoc tinh can thiet,
    tranh phu thuoc truc tiep vao detection/ trong file test cua engagement/."""

    def __init__(self, transformation_matrix):
        self.transformation_matrix = transformation_matrix


def test_estimate_head_pose_for_face_returns_none_when_no_matrix():
    face = _FakeFace(transformation_matrix=None)
    assert estimate_head_pose_for_face(face) is None


def test_estimate_head_pose_for_face_returns_pose_when_matrix_present():
    face = _FakeFace(transformation_matrix=build_4x4(10, 20, 5))
    pose = estimate_head_pose_for_face(face)
    assert isinstance(pose, HeadPose)
    assert_pose_close(pose, 10, 20, 5, tol=1e-4)