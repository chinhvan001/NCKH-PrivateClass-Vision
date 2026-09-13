"""
posture_monitor.py -- Ap dung nguong thoi gian (>5s) + lam muot theo cua so
thoi gian, va tu dong xac lap baseline "ngoi thang", cho tin hieu Head Drop
va Slumping (tu posture.py).

============================================================================
QUAN TRONG -- ngong theo THOI GIAN THUC (giay), KHONG PHAI so luong khung
hinh:
============================================================================
Benchmark FPS YOLOv8-pose tren CPU (task 3.2) cho thay FPS xu ly co the rat
thap va KHONG ON DINH (du kien 1-3 FPS, co the thap hon tuy cau hinh may).
Vi vay MOI nguong thoi gian trong file nay deu tinh theo do lech
TIMESTAMP THUC TE (giay) giua cac mau, khong dung so luong mau/frame co
dinh -- neu dung so luong frame co dinh (vi du "150 frame = 5 giay" gia dinh
30fps), nguong se sai hoan toan khi FPS thuc te thap hon nhieu.
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger("camera_ai.engagement")


@dataclass
class PostureThresholds:
    """Cac nguong cau hinh duoc cho viec phat hien Head Drop/Slumping.

    ========================================================================
    CANH BAO: day la GIA TRI KHOI DIEM dua tren suy luan hinh hoc, CHUA duoc
    kiem chung bang du lieu/video that. BAT BUOC phai tinh chinh lai bang
    thuc nghiem (video hoc sinh that hoac dien lai tinh huong) truoc khi
    dung ket qua de bao cao chinh thuc cho giao vien.
    ========================================================================

    head_drop_ratio_threshold: head_drop_ratio (tu posture.py) THAP HON gia
        tri nay duoc coi la "dau da cui thap". Gia tri khoi diem 0.4: theo
        test round-trip o task 3.5, tu the ngoi thang thu duoc ty le ~1.0-1.5;
        giam xuong duoi 0.4 nghia la khoang cach mui-vai chi con ~40% do
        rong vai, tuong ung dau da cui dang ke ve phia vai.
    torso_deviation_threshold_deg: do lech goc than tren (so voi baseline)
        VUOT QUA gia tri nay (tri tuyet doi) duoc coi la "slumping". Gia tri
        khoi diem 15.0 do -- muc lech duoc chon vi lon hon dang ke so voi
        dao dong tu nhien khi ngoi yen binh thuong (uoc luong vai do), nhung
        van dai dien cho mot su thay doi tu the ro rang. CANH BAO: chi co y
        nghia neu tin hieu torso_deviation tinh duoc on dinh -- neu hip bi
        che khuat thuong xuyen (xem canh bao trong posture.py), can chuyen
        sang nguong rieng cho shoulder_tilt (chua dinh nghia o day, se can bo
        sung sau khi co ket qua thuc nghiem ty le phat hien hip).
    sustained_duration_sec: thoi gian TOI THIEU dieu kien phai duy tri LIEN
        TUC de tinh la 1 su kien thuc su. Gia tri 5.0 giay lay TRUC TIEP tu
        muc tieu da neu trong Proposal chinh thuc ("head drop > 5s").
    """

    head_drop_ratio_threshold: float = 0.4
    torso_deviation_threshold_deg: float = 15.0
    sustained_duration_sec: float = 5.0


class RollingSmoother:
    """Lam muot 1 chuoi gia tri (vi du head_drop_ratio hoac
    torso_deviation_deg) theo CUA SO THOI GIAN (khong phai so luong mau co
    dinh) -- phu hop voi FPS thap/khong on dinh cua YOLOv8-pose tren CPU.

    Muc dich: tranh de 1 khung hinh nhieu don le (vi du mot lan detect keypoint
    sai lech tam thoi) lam sai lech ket qua thresholding phia sau.
    """

    def __init__(self, window_sec: float = 3.0):
        self._window_sec = window_sec
        self._samples: List[Tuple[float, float]] = []  # (timestamp, value)

    def add(self, timestamp: float, value: Optional[float]) -> Optional[float]:
        """Them 1 mau moi (bo qua neu value la None -- khong tinh duoc o
        khung hinh do, khong lam "loang" trung binh bang gia tri gia).

        Tra ve trung binh cua cac mau con trong cua so [timestamp - window_sec,
        timestamp], hoac None neu cua so hien khong co mau nao (vi du ngay
        sau khi khoi tao, hoac qua nhieu khung hinh lien tiep khong tinh
        duoc gia tri).
        """
        if value is not None:
            self._samples.append((timestamp, value))

        cutoff = timestamp - self._window_sec
        self._samples = [(t, v) for t, v in self._samples if t >= cutoff]

        if not self._samples:
            return None
        return statistics.mean(v for _, v in self._samples)

    def reset(self) -> None:
        self._samples.clear()


class BaselineEstablisher:
    """Thu thap mau torso_angle (tu posture.compute_torso_vector_angle)
    trong N giay dau cua buoi hoc, tinh baseline "ngoi thang chuan" bang
    median (ben vung hon trung binh cong truoc mot vai mau nhieu bat thuong
    trong luc calibrate).

    Sau khi da chot (is_ready=True), baseline KHONG doi trong suot buoi hoc
    -- dung dung Assumption "Fixed Seating Arrangement" cua Proposal chinh
    thuc (hoc sinh khong doi tu the ngoi "chuan" giua buoi).
    """

    def __init__(self, calibration_duration_sec: float = 5.0):
        self._calibration_duration_sec = calibration_duration_sec
        self._start_time: Optional[float] = None
        self._samples: List[float] = []
        self._baseline: Optional[float] = None

    def add_sample(self, timestamp: float, torso_angle: Optional[float]) -> None:
        """Them 1 mau trong giai doan calibration. Khong co tac dung gi neu
        baseline da duoc chot (is_ready=True) -- goi tiep khong gay loi,
        chi bi bo qua."""
        if self._baseline is not None:
            return

        if self._start_time is None:
            self._start_time = timestamp

        if torso_angle is not None:
            self._samples.append(torso_angle)

        if timestamp - self._start_time >= self._calibration_duration_sec:
            self._finalize()

    def _finalize(self) -> None:
        if self._samples:
            self._baseline = statistics.median(self._samples)
        else:
            # Khong thu duoc mau nao trong ca giai doan calibration -- vi du
            # hip bi che khuat suot (xem canh bao trong posture.py). Dung 0.0
            # lam fallback (tuong duong "khong co thong tin baseline, coi
            # nhu thang dung") thay vi treo vo han cho du lieu khong bao gio
            # den.
            self._baseline = 0.0
            logger.warning(
                "Khong thu thap duoc mau torso_angle nao trong %.1fs calibration -- "
                "dung baseline mac dinh 0.0. Co the do keypoint hong bi che khuat lien tuc.",
                self._calibration_duration_sec,
            )

    @property
    def is_ready(self) -> bool:
        return self._baseline is not None

    @property
    def baseline_angle(self) -> Optional[float]:
        return self._baseline

    def reset(self) -> None:
        self._start_time = None
        self._samples.clear()
        self._baseline = None


class PostureMonitor:
    """Theo doi MOT seat qua thoi gian, xac dinh xem dieu kien head_drop
    hoac slumping co dang duoc duy tri LIEN TUC qua nguong
    sustained_duration_sec hay khong.

    Quy tac xu ly du lieu thieu (None, vi du 1 khung hinh khong tinh duoc
    head_drop_ratio do keypoint confidence thap): KHONG reset tien trinh
    dang tich luy, cung KHONG tinh la dang tiep tuc dieu kien -- chi mot
    lan doc XAC NHAN dieu kien la SAI (vi du head_drop_ratio quay ve tren
    nguong) moi reset tien trinh ve 0. Ly do: du lieu thieu tam thoi (1-2
    khung hinh) la binh thuong trong thuc te, khong nen bi hieu nham la
    "da het cui dau" chi vi 1 lan detect khong ra ket qua.
    """

    def __init__(self, thresholds: Optional[PostureThresholds] = None):
        self._thresholds = thresholds or PostureThresholds()
        self._head_drop_start: Optional[float] = None
        self._slump_start: Optional[float] = None

    def update(
        self,
        timestamp: float,
        head_drop_ratio: Optional[float],
        torso_deviation_deg: Optional[float],
    ) -> Tuple[bool, bool]:
        """Goi 1 lan moi khi co mau moi (da qua RollingSmoother) cho 1 seat.

        Tra ve (is_head_drop_event, is_slumping_event) -- True neu dieu kien
        tuong ung DA duoc xac nhan duy tri lien tuc >= sustained_duration_sec
        TINH DEN thoi diem nay.
        """
        is_head_drop_event = self._update_condition(
            timestamp,
            head_drop_ratio,
            is_active=lambda v: v < self._thresholds.head_drop_ratio_threshold,
            state_attr="_head_drop_start",
        )
        is_slumping_event = self._update_condition(
            timestamp,
            torso_deviation_deg,
            is_active=lambda v: abs(v) > self._thresholds.torso_deviation_threshold_deg,
            state_attr="_slump_start",
        )
        return is_head_drop_event, is_slumping_event

    def _update_condition(self, timestamp, value, is_active, state_attr: str) -> bool:
        start_time = getattr(self, state_attr)

        if value is None:
            pass  # du lieu thieu -- giu nguyen trang thai, khong reset khong tinh tiep
        elif is_active(value):
            if start_time is None:
                start_time = timestamp
                setattr(self, state_attr, start_time)
        else:
            start_time = None
            setattr(self, state_attr, None)

        if start_time is None:
            return False
        return (timestamp - start_time) >= self._thresholds.sustained_duration_sec

    def reset(self) -> None:
        self._head_drop_start = None
        self._slump_start = None