"""
hand_activity.py -- Theo doi hoat dong cua tay (wrist) theo thoi gian, phan
biet "tay dang hoat dong" (chep bai/lat trang -- co the dang hoc that) voi
"tay tinh keo dai" (nghi ngo mat tap trung that su) -- tin hieu phu giai
quyet van de head_drop bi nham voi chep bai/doc sach, phat hien tu test
thuc te tren video.

Xem thiet ke day du: Head-Drop-Redesign.docx, Muc 3 (13/09/2026).

============================================================================
QUAN TRONG -- day la tin hieu THEO THOI GIAN (can nhieu khung hinh), khac
voi cac ham trong posture.py (tinh tuc thoi tu 1 khung hinh don):
============================================================================
Chep bai/doc sach co CHUYEN DONG TAY LAP LAI, LIEN TUC (viet, lat trang);
ngu gat/mat tap trung co tay TINH trong thoi gian dai. Module nay do DO
BIEN THIEN (variance) vi tri co tay trong mot cua so thoi gian, KHONG PHAI
gia tri trung binh nhu RollingSmoother (posture_monitor.py, Sprint 3).

QUAN TRONG -- CHUA kiem chung bang du lieu that:
Nguong movement_threshold la GIA TRI KHOI DIEM dua tren suy luan, giong tat
ca cac nguong khac trong du an nay -- BAT BUOC phai tinh chinh lai bang cach
xem truc tiep video that va doi chieu (xem canh bao trong
Head-Drop-Redesign.docx, Muc 4).
"""

import math
import statistics
from collections import deque
from typing import Deque, List, Optional, Tuple

# Nguong bien thien vi tri co tay, DA CHUAN HOA theo do rong vai (giong
# cach chuan hoa head_drop_ratio trong posture.py) -- vi du 0.15 nghia la
# do lech chuan vi tri co tay trong cua so bang ~15% do rong vai. Chuan hoa
# giup nguong ap dung nhat quan cho nguoi o gan/xa camera khac nhau.
DEFAULT_MOVEMENT_THRESHOLD_RATIO = 0.15

MIN_WRIST_CONFIDENCE = 0.3
MIN_SHOULDER_CONFIDENCE = 0.3


def _wrist_positions(person) -> List[Tuple[float, float]]:
    """Lay toa do (x, y) cua cac wrist du tin cay (co the 0, 1, hoac 2 diem)."""
    positions = []
    for name in ("left_wrist", "right_wrist"):
        kp = person.get_keypoint(name)
        if kp is not None and kp[2] >= MIN_WRIST_CONFIDENCE:
            positions.append((kp[0], kp[1]))
    return positions


def _average_position(positions: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    if not positions:
        return None
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    return (statistics.mean(xs), statistics.mean(ys))


def _shoulder_width(person) -> Optional[float]:
    """Tinh do rong vai lam thuoc do chuan hoa -- ban sao ngan gon cua logic
    tuong tu trong posture.py (khong import truc tiep de tranh phu thuoc
    cheo giua 2 file cho MOT phep tinh don gian; neu posture.py thay doi
    cong thuc nay trong tuong lai, can dong bo lai ca hai noi)."""
    left = person.get_keypoint("left_shoulder")
    right = person.get_keypoint("right_shoulder")
    if left is None or right is None:
        return None
    if left[2] < MIN_SHOULDER_CONFIDENCE or right[2] < MIN_SHOULDER_CONFIDENCE:
        return None
    width = math.hypot(left[0] - right[0], left[1] - right[1])
    return width if width > 0 else None


class HandActivityMonitor:
    """Theo doi MOT seat, xac dinh xem tay co dang HOAT DONG (bien thien vi
    tri cao -- vi du viet, lat trang) hay TINH KEO DAI (bien thien thap)
    trong cua so thoi gian gan day.

    Cach dung (moi seat can 1 instance rieng):
        monitor = HandActivityMonitor(window_sec=4.0)
        for frame in session:
            person = ...  # PersonPose cua seat nay tai frame hien tai
            activity = monitor.update(frame.timestamp, person)
            # activity: True (dang hoat dong) / False (tinh) / None (khong
            # du du lieu de ket luan)
    """

    def __init__(
        self,
        window_sec: float = 4.0,
        movement_threshold_ratio: float = DEFAULT_MOVEMENT_THRESHOLD_RATIO,
        min_samples: int = 3,
    ):
        """
        window_sec: do dai cua so thoi gian de tinh bien thien vi tri co tay.
        movement_threshold_ratio: nguong do lech chuan vi tri (DA CHUAN HOA
            theo do rong vai) -- vuot qua gia tri nay duoc coi la "dang
            hoat dong". GIA TRI KHOI DIEM, chua kiem chung.
        min_samples: so mau toi thieu trong cua so de dua ra ket luan --
            neu chua du (vi du seat vua co nguoi ngoi vao, hoac wrist bi
            che khuat lien tuc), tra ve None thay vi ket luan voi du lieu
            it oi.
        """
        self._window_sec = window_sec
        self._movement_threshold_ratio = movement_threshold_ratio
        self._min_samples = min_samples
        # Moi phan tu: (timestamp, x, y, shoulder_width)
        self._samples: Deque[Tuple[float, float, float, float]] = deque()

    def update(self, timestamp: float, person) -> Optional[bool]:
        """Them 1 quan sat moi (tu 1 khung hinh), tra ve ket qua phan loai
        hoat dong tay dua tren cua so [timestamp - window_sec, timestamp].

        Tra ve None neu khong du du lieu de ket luan (chua du min_samples
        mau con hop le trong cua so -- vi du wrist/shoulder khong phat hien
        duoc du tin cay o nhieu khung hinh lien tiep).
        """
        positions = _wrist_positions(person)
        avg_pos = _average_position(positions)
        scale = _shoulder_width(person)

        if avg_pos is not None and scale is not None:
            self._samples.append((timestamp, avg_pos[0], avg_pos[1], scale))

        cutoff = timestamp - self._window_sec
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

        if len(self._samples) < self._min_samples:
            return None

        xs = [s[1] for s in self._samples]
        ys = [s[2] for s in self._samples]
        scales = [s[3] for s in self._samples]

        std_x = statistics.pstdev(xs)
        std_y = statistics.pstdev(ys)
        combined_std = math.hypot(std_x, std_y)

        avg_scale = statistics.mean(scales)
        if avg_scale <= 0:
            return None

        normalized_std = combined_std / avg_scale
        return normalized_std >= self._movement_threshold_ratio

    def reset(self) -> None:
        """Xoa toan bo mau dang luu (vi du bat dau session moi)."""
        self._samples.clear()
