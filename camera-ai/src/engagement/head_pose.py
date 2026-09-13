"""
head_pose.py -- Uoc luong head pose (yaw/pitch/roll) tu facial transformation
matrix cua MediaPipe Face Landmarker.

Cach tiep can: MediaPipe Face Landmarker (voi output_facial_transformation_matrixes=True,
da bat mac dinh trong LandmarkerConfig o Sprint 3) tra ve san mot ma tran bien
doi 4x4 mo ta huong xoay cua khuon mat. Module nay CHI can tach 3 goc Euler
(yaw, pitch, roll) tu phan ma tran xoay 3x3 (goc tren trai cua ma tran 4x4) --
KHONG can tu cai dat solvePnP thu cong nhu khi chi co landmark tho + camera
matrix xap xi. Day la huong da chot trong tai lieu nghien cuu Sprint 1 (muc
2.3: "Truong hop dung MediaPipe Face Landmarker").

============================================================================
QUAN TRONG #1 -- thu tu phan tich (decomposition order):
============================================================================
Cong thuc duoi day dung thu tu phan tich YZX (KHONG PHAI XYZ thong thuong hay
gap trong cac vi du solvePnP/OpenCV/dlib). Day la thu tu DUNG rieng cho ma
tran bien doi cua MediaPipe -- tham khao tu thao luan cong dong da duoc kiem
chung thuc te tren google-ai-edge/mediapipe issue #2809 (nguoi dung xac nhan
hoat dong dung voi du lieu MediaPipe that), dan chieu cong thuc goc tu
geometrictools.com/Documentation/EulerAngles.pdf.

Dung nham thu tu XYZ thay vi YZX se cho ra ket qua NHIN QUA co ve hop ly (dung
khi chi 1 truc xoay rieng le) nhung SAI ve mat toan hoc khi 2-3 truc cung xoay
dong thoi (vi du vua nghieng dau vua quay dau cung luc).

============================================================================
QUAN TRONG #2 -- quy uoc dau (sign convention) CAN TU KIEM TRA THUC TE:
============================================================================
Da verify bang toan hoc (round-trip: dung goc bat ky -> dung thanh ma tran
xoay -> giai ma lai -> phai ra dung goc ban dau, ke ca truong hop 3 truc xoay
dong thoi) rang cong thuc phan tich ben duoi la DUNG va on dinh, kem xu ly
dung ca truong hop gimbal lock (r10 = +-1, khi pitch/roll dat gan +-90 do).
Chi tiet xem tests/engagement/test_head_pose.py.

TUY NHIEN, sandbox phat trien khong co model/webcam that de xac nhan quy uoc
truc toa do CU THE cua MediaPipe (vi du: quay dau sang phai thi yaw ra so
duong hay am?). Ban BAT BUOC phai tu kiem tra thuc te sau khi tich hop:
    1. Chay thu voi webcam that, quay dau tu tu sang phai/trai, ngua/cui, va
       nghieng dau sang 2 ben.
    2. Doi chieu dau (duong/am) cua yaw/pitch/roll in ra co khop truc giac
       thong thuong khong (vi du: quay sang phai la yaw duong).
    3. Neu bi nguoc, KHONG sua truc tiep vao ham estimate_head_pose() -- bao
       loi/chinh sua o tang goi (module engagement/scoring se dung o Sprint 4),
       de giu ham nay dung nguyen theo cong thuc da duoc toan hoc kiem chung.
"""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class HeadPose:
    """Goc xoay dau, don vi DO (degree, khong phai radian)."""

    yaw: float    # quay dau sang trai/phai
    pitch: float  # ngua dau len / cui dau xuong
    roll: float   # nghieng dau sang 2 ben (tai vai)


def estimate_head_pose(transformation_matrix: "np.ndarray") -> HeadPose:
    """Tach goc Euler (yaw, pitch, roll) tu facial transformation matrix (4x4
    hoac 3x3) do MediaPipe Face Landmarker tra ve
    (FaceLandmarks.transformation_matrix trong module detection/).

    Nem ValueError neu transformation_matrix la None -- chi goi ham nay sau
    khi da kiem tra face.transformation_matrix is not None (co the la None
    neu LandmarkerConfig.output_transformation_matrix=False, hoac dung
    estimate_head_pose_for_face() ben duoi de tu dong xu ly truong hop nay).
    """
    if transformation_matrix is None:
        raise ValueError(
            "transformation_matrix la None -- kiem tra LandmarkerConfig."
            "output_transformation_matrix=True truoc khi goi ham nay, hoac "
            "dung estimate_head_pose_for_face() de tu dong xu ly truong hop None."
        )

    r = transformation_matrix[:3, :3]  # phan ma tran xoay 3x3, bo qua tinh tien

    r10 = r[1, 0]
    if r10 < 1:
        if r10 > -1:
            theta_z = math.asin(r10)
            theta_y = math.atan2(-r[2, 0], r[0, 0])
            theta_x = math.atan2(-r[1, 2], r[1, 1])
        else:  # gimbal lock: r10 = -1 (khong the tach rieng theta_x)
            theta_z = -math.pi / 2
            theta_y = -math.atan2(r[2, 1], r[2, 2])
            theta_x = 0.0
    else:  # gimbal lock: r10 = 1
        theta_z = math.pi / 2
        theta_y = math.atan2(r[2, 1], r[2, 2])
        theta_x = 0.0

    return HeadPose(
        yaw=math.degrees(-theta_y),
        pitch=math.degrees(-theta_x),
        roll=math.degrees(-theta_z),
    )


def estimate_head_pose_for_face(face) -> Optional[HeadPose]:
    """Tien ich: uoc luong head pose truc tiep tu 1 FaceLandmarks (module
    detection/), tra ve None (thay vi raise ValueError) neu face khong co
    transformation_matrix -- tien loi hon khi dung trong vong lap xu ly nhieu
    khuon mat cung luc, khong can tu kiem tra None truoc moi lan goi.

    face: bat ky object nao co thuoc tinh .transformation_matrix (thuong la
        FaceLandmarks tra ve tu FaceLandmarker.detect() cua module detection/).
    """
    if face.transformation_matrix is None:
        return None
    return estimate_head_pose(face.transformation_matrix)