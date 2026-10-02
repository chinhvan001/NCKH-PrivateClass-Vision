"""
posture.py -- Tinh cac chi so hinh hoc tu skeleton (PersonPose, module
detection/pose_detector.py) phuc vu phat hien Head Drop va Slumping.

THAY THE cho head_pose.py + EAR (huong facial cu, da ngung dung sau pivot).
Xem Algorithm-Pivot-Proposal.docx, muc 5 (Tin hieu Posture cho Engagement).

============================================================================
CAP NHAT 13/09/2026 (Head-Drop-Redesign.docx, Giai phap 1): bo sung
compute_face_visibility_score() va select_head_down_signal() de ho tro
camera goc TOP-DOWN, phat hien tu test thuc te tren video cho thay
compute_head_drop_ratio() (cong thuc goc, chi dung cho camera FRONTAL) cho
ket qua sai lech nghiem trong voi camera nhin thang tu tren xuong. Xem Muc
cuoi file de biet chi tiet.
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

Ghi chu thuc te (13/09/2026): test tren video top-down cho thay co the HIP
lai QUAN SAT DUOC TOT HON tu goc tren xuong (khong bi ban che theo huong
nhin nay) -- neu dung, slumping co the tro thanh tin hieu DANG TIN CAY HON
head-down cho dung loai camera nay. Con can kiem chung bang du lieu that.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from src.detection.pose_detector import PersonPose

# Nguong confidence toi thieu cho 1 keypoint de duoc coi la du tin cay.
MIN_KEYPOINT_CONFIDENCE = 0.3

# Do rong vai toi thieu (pixel) de tranh chia cho so gan 0 gay ket qua vo
# nghia (vi du nguoi qua nho/qua xa camera, hoac phat hien loi).
MIN_SHOULDER_WIDTH_PIXELS = 5.0

# Loai goc camera -- khai bao THU CONG tai buoc calibration (cung luc voi
# seat_grid.json, module seating/), KHONG tu dong phat hien. Xem Muc 2.1,
# Head-Drop-Redesign.docx: goc lap camera la gia tri tinh, khong doi trong
# suot vong doi lap dat, nen khong can suy luan lai moi khung hinh.
CameraAngleType = Literal["frontal", "top_down"]

# GIA TRI KHOI DIEM cho nguong face_visibility (camera top_down) -- CHUA
# kiem chung bang du lieu that, can thuc nghiem rieng (xem Head-Drop-Redesign.docx
# Muc 2.3). KHONG dung chung thang do voi head_drop_ratio_threshold (frontal)
# vi day la 2 don vi khac nhau (ty le hinh hoc chuan hoa vs. confidence trung binh 0-1).
DEFAULT_FACE_VISIBILITY_THRESHOLD = 0.3


def _midpoint(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _keypoints_confident(*keypoints: Optional[Tuple[float, float, float]]) -> bool:
    return all(kp is not None and kp[2] >= MIN_KEYPOINT_CONFIDENCE for kp in keypoints)


# ----------------------------------------------------------------------
# Head Drop -- camera FRONTAL (cong thuc hinh hoc goc, task 3.5)
# ----------------------------------------------------------------------


def compute_head_drop_ratio(person: PersonPose) -> Optional[float]:
    """Tinh ty le khoang cach (mui -> duong vai) theo truc Y, DA CHUAN HOA
    theo do rong vai (shoulder width) de bat bien tuong doi voi khoang cach
    tu nguoi do toi camera.

    CHI DUNG CHO CAMERA FRONTAL/GOC NGHIENG NHE -- xem canh bao dau file va
    select_head_down_signal() ben duoi de tu dong chon dung ham theo loai
    camera. Voi camera top_down, dung compute_face_visibility_score() thay the.

    Quy uoc gia tri tra ve:
        > 0 va cang lon: mui o CAO hon duong vai ro ret (tu the binh thuong).
        gan 0: mui GAN NGANG duong vai (dau da cui rat thap).
        < 0: mui o DUOI duong vai (truong hop cui gan nhu gap nguoi, hiem).

    Tra ve None neu thieu bat ky keypoint can thiet nao, confidence qua
    thap, hoac shoulder_width qua nho (< MIN_SHOULDER_WIDTH_PIXELS).
    """
    nose = person.get_keypoint("nose")
    left_shoulder = person.get_keypoint("left_shoulder")
    right_shoulder = person.get_keypoint("right_shoulder")

    if not _keypoints_confident(nose, left_shoulder, right_shoulder):
        return None

    shoulder_width = math.hypot(left_shoulder[0] - right_shoulder[0], left_shoulder[1] - right_shoulder[1])
    if shoulder_width < MIN_SHOULDER_WIDTH_PIXELS:
        return None

    shoulder_line_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
    vertical_distance = shoulder_line_y - nose[1]

    return vertical_distance / shoulder_width


# ----------------------------------------------------------------------
# Head Drop -- camera TOP-DOWN (tin hieu moi, 13/09/2026)
# ----------------------------------------------------------------------


def compute_face_visibility_score(person: PersonPose) -> Optional[float]:
    """Tinh do "nhin thay mat" trung binh (nose, left_eye, right_eye) --
    tin hieu THAY THE cho compute_head_drop_ratio() khi camera dat THANG TU
    TREN XUONG (top-down/overhead).

    Nguyen ly: tu camera nhin thang xuong, khi dau cui thap, MAT QUAY RA XA
    ong kinh -- model phat hien pose (YOLOv8-pose) se tra ve CONFIDENCE THAP
    cho cac keypoint vung mat, du vai van phat hien tot (vai nhin tu tren
    xuong it bi anh huong boi viec cui dau). Day la tin hieu GIAN TIEP
    (dua vao confidence, khong phai toa do hinh hoc truc tiep) va NHIEU HON
    compute_head_drop_ratio() -- xem canh bao trong Head-Drop-Redesign.docx
    Muc 2.3, can thuc nghiem rieng de chot nguong (xem DEFAULT_FACE_VISIBILITY_THRESHOLD).

    Quy uoc gia tri tra ve (0.0 - 1.0), CUNG CHIEU voi compute_head_drop_ratio():
        Cao (gan 1.0): mat huong ve phia camera ro rang (dang nhin len/thang).
        Thap (gan 0.0): mat khong phat hien duoc ro (co the dang cui dau,
            hoac cung co the do goc dau tu nhien/khuat tam thoi khac).

    Tra ve None neu KHONG mot keypoint nao trong (nose, left_eye, right_eye)
    duoc phat hien (kha nang do het bi che khuat/ra khoi khung hinh, khac
    voi truong hop phat hien duoc nhung confidence thap do cui dau)."""
    keypoints = [
        person.get_keypoint("nose"),
        person.get_keypoint("left_eye"),
        person.get_keypoint("right_eye"),
    ]
    confidences = [kp[2] for kp in keypoints if kp is not None]

    if not confidences:
        return None

    return sum(confidences) / len(confidences)


def select_head_down_signal(person: PersonPose, camera_angle_type: CameraAngleType) -> Optional[float]:
    """Diem vao THONG NHAT: tu dong chon dung ham tinh tin hieu "cui dau"
    theo loai goc camera da khai bao (xem CameraAngleType, khai bao thu
    cong tai buoc calibration -- KHONG tu dong phat hien).

    Ca 2 tin hieu tra ve deu CUNG QUY UOC CHIEU (gia tri THAP = dang cui
    dau), nhung KHAC DON VI/THANG DO -- goi dung threshold tuong ung khi so
    sanh:
        camera_angle_type="frontal"  -> compute_head_drop_ratio(),
            so sanh voi PostureThresholds.head_drop_ratio_threshold.
        camera_angle_type="top_down" -> compute_face_visibility_score(),
            so sanh voi DEFAULT_FACE_VISIBILITY_THRESHOLD (hoac gia tri
            rieng da tinh chinh).

    Nem ValueError neu camera_angle_type khong hop le (khong phai "frontal"
    hay "top_down") -- day la loi cau hinh can phat hien ngay, khong nen
    am tham tra ve None.
    """
    if camera_angle_type == "frontal":
        return compute_head_drop_ratio(person)
    if camera_angle_type == "top_down":
        return compute_face_visibility_score(person)
    raise ValueError(
        f"camera_angle_type khong hop le: {camera_angle_type!r} " '(chi chap nhan "frontal" hoac "top_down")'
    )


# ----------------------------------------------------------------------
# Slumping -- tin hieu chinh (can hip)
# ----------------------------------------------------------------------


def compute_torso_vector_angle(person: PersonPose) -> Optional[float]:
    """Tinh goc (do) cua vector than tren -- tu trung diem 2 vai toi trung
    diem 2 hong -- so voi truc doc (vertical) huong xuong duoi trong anh.

    0 do = than tren thang dung (vector song song truc doc, ngoi thang
    chuan). Gia tri tuyet doi cang lon = nguoi cang nghieng/cui nhieu.

    CANH BAO: xem canh bao ve keypoint hong o dau file.

    Tra ve None neu thieu bat ky keypoint can thiet nao hoac confidence qua
    thap.
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

    return math.degrees(math.atan2(dx, dy))


def compute_torso_deviation(person: PersonPose, baseline_angle: float) -> Optional[float]:
    """Tinh do lech (do) giua goc than tren HIEN TAI va baseline_angle.

    Tra ve None neu khong tinh duoc goc hien tai.
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

    0 do = 2 vai ngang bang nhau. Tin hieu DU PHONG cho slumping, KHONG can
    keypoint hong.

    Tra ve None neu thieu left_shoulder/right_shoulder hoac confidence thap.
    """
    left_shoulder = person.get_keypoint("left_shoulder")
    right_shoulder = person.get_keypoint("right_shoulder")

    if not _keypoints_confident(left_shoulder, right_shoulder):
        return None

    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]

    return math.degrees(math.atan2(dy, dx))
