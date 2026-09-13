"""
posture.py -- Tinh cac chi so hinh hoc tu skeleton (PersonPose, module
detection/pose_detector.py) phuc vu phat hien Head Drop va Slumping.

THAY THE cho head_pose.py + EAR (huong facial cu, da ngung dung sau pivot).
Xem Algorithm-Pivot-Proposal.docx, muc 5 (Tin hieu Posture cho Engagement).

============================================================================
PHAM VI TASK NAY (3.5, phan 1/2): CHI cac ham tinh toan hinh hoc THUAN cho
MOT khung hinh don le. Ap dung nguong thoi gian (>5s), lam muot (rolling
window), va tu dong xac lap baseline "ngoi thang" la task 3.6 (phan 2/2),
CHUA co trong file nay.
============================================================================

============================================================================
CANH BAO QUAN TRONG ve keypoint hong (hip):
============================================================================
compute_torso_vector_angle() va compute_torso_deviation() can ca
left_hip/right_hip DE TINH DUOC. Trong boi canh lop hoc thuc te (camera dat
o buc giang hoac sau lung giao vien, hoc sinh ngoi sau ban hoc), keypoint
hong RAT CO THE BI BAN HOC CHE KHUAT hoan toan -- YOLOv8-pose se tra ve
confidence rat thap hoac khong phat hien duoc hip cho phan lon hoc sinh.

Neu dieu nay xay ra tren du lieu/anh that (CAN KIEM TRA THUC NGHIEM O TASK
3.6), tin hieu torso-angle se KHONG DUNG DUOC cho da so hoc sinh. Module nay
da chuan bi san mot tin hieu du phong KHONG CAN HIP:
compute_shoulder_tilt() -- do nghieng duong noi 2 vai, chi can 2 keypoint vai
(da duoc chung minh de phat hien on dinh hon nhieu trong thuc te). Neu ty le
phat hien hip qua thap, can chuyen huong dung shoulder_tilt lam tin hieu
slumping chinh (hoac ket hop voi head_drop_ratio, vi ca hai deu tuong quan
voi tu the cui nguoi ve truoc khi nhin tu camera phia truoc).
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from src.detection.pose_detector import PersonPose

# Nguong confidence toi thieu cho 1 keypoint de duoc coi la du tin cay.
MIN_KEYPOINT_CONFIDENCE = 0.3

# Do rong vai toi thieu (pixel) de tranh chia cho so gan 0 gay ket qua vo
# nghia (vi du nguoi qua nho/qua xa camera, hoac phat hien loi).
MIN_SHOULDER_WIDTH_PIXELS = 5.0


def _midpoint(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _keypoints_confident(*keypoints: Optional[Tuple[float, float, float]]) -> bool:
    return all(kp is not None and kp[2] >= MIN_KEYPOINT_CONFIDENCE for kp in keypoints)


# ----------------------------------------------------------------------
# Head Drop
# ----------------------------------------------------------------------


def compute_head_drop_ratio(person: PersonPose) -> Optional[float]:
    """Tinh ty le khoang cach (mui -> duong vai) theo truc Y, DA CHUAN HOA
    theo do rong vai (shoulder width) de bat bien tuong doi voi khoang cach
    tu nguoi do toi camera (nguoi gan camera co pixel lon hon nguoi xa,
    chuan hoa giup nguong phat hien ap dung nhat quan cho ca 30-40 hoc sinh
    o cac vi tri khac nhau trong khung hinh).

    Quy uoc gia tri tra ve:
        > 0 va cang lon: mui o CAO hon duong vai ro ret (tu the binh thuong,
            ngoi thang, dau ngang hoac cao hon vai).
        gan 0: mui GAN NGANG duong vai (dau da cui rat thap).
        < 0: mui o DUOI duong vai (truong hop cui gan nhu gap nguoi, hiem).

    Tra ve None neu thieu bat ky keypoint can thiet nao (nose, left_shoulder,
    right_shoulder), confidence qua thap, hoac shoulder_width qua nho
    (< MIN_SHOULDER_WIDTH_PIXELS).
    """
    nose = person.get_keypoint("nose")
    left_shoulder = person.get_keypoint("left_shoulder")
    right_shoulder = person.get_keypoint("right_shoulder")

    if not _keypoints_confident(nose, left_shoulder, right_shoulder):
        return None

    shoulder_width = math.hypot(
        left_shoulder[0] - right_shoulder[0], left_shoulder[1] - right_shoulder[1]
    )
    if shoulder_width < MIN_SHOULDER_WIDTH_PIXELS:
        return None

    shoulder_line_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
    # Luu y he toa do anh: truc Y tang xuong duoi -- mui o TREN vai (binh
    # thuong) nghia la nose_y < shoulder_line_y, nen hieu nay la SO DUONG.
    vertical_distance = shoulder_line_y - nose[1]

    return vertical_distance / shoulder_width


# ----------------------------------------------------------------------
# Slumping -- tin hieu chinh (can hip)
# ----------------------------------------------------------------------


def compute_torso_vector_angle(person: PersonPose) -> Optional[float]:
    """Tinh goc (do) cua vector than tren -- tu trung diem 2 vai toi trung
    diem 2 hong -- so voi truc doc (vertical) huong xuong duoi trong anh.

    0 do = than tren thang dung (vector song song truc doc, ngoi thang
    chuan). Gia tri tuyet doi cang lon = nguoi cang nghieng/cui nhieu (khong
    phan biet duoc nghieng trai/phai hay cui truoc/sau tu 1 camera 2D don,
    chi biet MUC DO lech khoi phuong thang dung).

    CANH BAO: xem canh bao ve keypoint hong o dau file -- ham nay tra ve
    None rat thuong xuyen neu hip bi ban hoc che khuat trong thuc te.

    Tra ve None neu thieu bat ky keypoint can thiet nao (left_shoulder,
    right_shoulder, left_hip, right_hip) hoac confidence qua thap.
    """
    left_shoulder = person.get_keypoint("left_shoulder")
    right_shoulder = person.get_keypoint("right_shoulder")
    left_hip = person.get_keypoint("left_hip")
    right_hip = person.get_keypoint("right_hip")

    if not _keypoints_confident(left_shoulder, right_shoulder, left_hip, right_hip):
        return None

    shoulder_mid = _midpoint(left_shoulder, right_shoulder)
    hip_mid = _midpoint(left_hip, right_hip)

    dx = hip_mid[0] - shoulder_mid[0]
    dy = hip_mid[1] - shoulder_mid[1]

    # Goc giua vector (dx, dy) va truc doc (0, 1) -- dung atan2(dx, dy) thay
    # vi atan2(dy, dx) de 0 do ung voi vector thang dung (dx=0), khong phai
    # vector nam ngang.
    return math.degrees(math.atan2(dx, dy))


def compute_torso_deviation(person: PersonPose, baseline_angle: float) -> Optional[float]:
    """Tinh do lech (do) giua goc than tren HIEN TAI va baseline_angle (goc
    'ngoi thang chuan' da xac lap truoc do cho NGUOI/SEAT nay).

    Viec TU DONG XAC LAP baseline_angle (vi du trung binh vai giay dau buoi
    hoc) la task 3.6 (phan 2/2) -- ham nay chi nhan baseline_angle nhu mot
    tham so co san, khong tu tinh.

    Tra ve None neu khong tinh duoc goc hien tai (thieu keypoint/confidence
    thap -- xem canh bao ve hip o dau file).
    """
    current_angle = compute_torso_vector_angle(person)
    if current_angle is None:
        return None
    return current_angle - baseline_angle


# ----------------------------------------------------------------------
# Slumping -- tin hieu du phong (KHONG can hip)
# ----------------------------------------------------------------------


def compute_shoulder_tilt(person: PersonPose) -> Optional[float]:
    """Tinh do nghieng (do) cua duong noi 2 vai so voi phuong ngang.

    0 do = 2 vai ngang bang nhau. Khac dau/khac 0 = mot ben vai cao hon ben
    kia (nghieng nguoi sang 1 ben).

    Tin hieu DU PHONG cho slumping, KHONG can keypoint hong -- de xuat dung
    thay the hoac ket hop voi compute_torso_deviation() neu ty le phat hien
    hip qua thap trong thuc nghiem (xem canh bao dau file). Khong bat duoc
    truong hop cui ve truoc/sau doi xung (2 vai van ngang nhau du cui gap
    nguoi), chi bat duoc nghieng sang 1 ben -- day la mot tin hieu bo sung,
    khong thay the hoan toan cho torso-angle neu hip phat hien on dinh duoc.

    Tra ve None neu thieu left_shoulder/right_shoulder hoac confidence thap.
    """
    left_shoulder = person.get_keypoint("left_shoulder")
    right_shoulder = person.get_keypoint("right_shoulder")

    if not _keypoints_confident(left_shoulder, right_shoulder):
        return None

    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]

    return math.degrees(math.atan2(dy, dx))