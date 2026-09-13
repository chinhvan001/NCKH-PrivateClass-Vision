"""
rolling_engagement.py -- Tinh diem engagement theo CUA SO TRUOT (rolling
window, vi du 5-10 phut gan nhat) thay vi cumulative tu dau session
(SeatEngagementTracker, task 4.2).

============================================================================
KHAC BIET VOI ROLLING WINDOW O SPRINT 3 (RollingSmoother, posture_monitor.py):
============================================================================
RollingSmoother (Sprint 3) lam muot TIN HIEU THO (head_drop_ratio,
torso_deviation_deg) o tung khung hinh, truoc khi dua vao PostureMonitor de
xac dinh su kien >5s. RollingSeatEngagementTracker o day lam viec o TANG
DIEM SO TONG HOP: tinh diem engagement dua tren cac SU KIEN da qua xu ly
(is_head_drop_event, is_slumping_event), trong mot cua so thoi gian dai hon
nhieu (vi du 5-10 PHUT, khong phai 3 GIAY). Hai lop rolling window nay giai
quyet 2 van de khac nhau:
    - RollingSmoother: chong nhieu tuc thoi giua cac khung hinh.
    - RollingSeatEngagementTracker: phan anh XU HUONG GAN DAY thay vi trung
      binh toan buoi hoc (mot buoi 1 tieng ngoi tot 50 phut + xao nhang 10
      phut cuoi van nen hien "dang xao nhang" tren dashboard REAL-TIME, du
      diem CUMULATIVE ca buoi van con cao).

Dung SeatEngagementTracker (task 4.2) cho BAO CAO CUOI BUOI (tong ket toan
session). Dung RollingSeatEngagementTracker (file nay) cho HIEN THI TRUC
TIEP tren dashboard/mobile trong luc buoi hoc dang dien ra. Co the chay CA
HAI song song cho cung 1 seat, khong xung dot (2 instance doc lap).
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.engagement.engagement_score import (
    DEFAULT_SLUMP_CREDIT,
    EngagementScore,
    classify_posture_state,
    compute_score_from_durations,
)

logger = logging.getLogger("camera_ai.engagement")

# Neu khoang cach giua 2 lan update() lien tiep VUOT QUA gia tri nay, coi la
# mot khoang TRONG THUC SU (hoc sinh roi cho, camera mat dau seat trong thoi
# gian dai) -- KHONG tinh vao bat ky trang thai nao (loai khoi ca tu va mau
# so cua ty le), thay vi am tham gan het khoang trong do cho trang thai vua
# quan sat duoc sau khoang trong.
#
# GIA TRI KHOI DIEM 30 giay: lon hon nhieu so voi chu ky cap nhat binh
# thuong (ke ca o FPS thap nhat da do duoc trong benchmark task 3.2, ~1
# frame/giay), nhung du nho de phat hien dung luc hoc sinh thuc su roi cho
# thay vi chi la 1-2 nhip xu ly cham/mat frame tam thoi. CAN kiem chung lai
# bang du lieu that.
DEFAULT_MAX_GAP_SEC = 30.0


@dataclass
class _Segment:
    start: float
    end: float
    state: str  # "normal" | "slumping" | "head_drop"

    @property
    def duration(self) -> float:
        return self.end - self.start


class RollingSeatEngagementTracker:
    """Tinh diem engagement cho MOT seat, chi dua tren du lieu trong
    window_sec giay GAN NHAT (khong phai toan bo session tu dau).

    Cach dung (moi seat can 1 instance rieng, doc lap voi
    SeatEngagementTracker neu dung ca 2 song song):
        tracker = RollingSeatEngagementTracker(seat_id="A1", window_sec=300.0)
        for frame in session:
            is_drop, is_slump = posture_monitor.update(frame.timestamp, ratio, deviation)
            tracker.update(frame.timestamp, is_drop, is_slump)
        result = tracker.compute_score()  # chi phan anh 5 phut gan nhat
    """

    def __init__(
        self,
        seat_id: str,
        window_sec: float = 300.0,
        slump_credit: float = DEFAULT_SLUMP_CREDIT,
        max_gap_sec: float = DEFAULT_MAX_GAP_SEC,
    ):
        self._seat_id = seat_id
        self._window_sec = window_sec
        self._slump_credit = slump_credit
        self._max_gap_sec = max_gap_sec

        self._segments: List[_Segment] = []
        self._last_timestamp: Optional[float] = None
        self._last_state: Optional[str] = None

    def update(self, timestamp: float, is_head_drop_event: bool, is_slumping_event: bool) -> None:
        """Goi MOT LAN moi khi PostureMonitor.update() tra ve ket qua moi
        cho seat nay. Cung dau vao voi SeatEngagementTracker.update() -- co
        the goi ca 2 tracker voi cung 1 lan quan sat neu can ca 2 loai diem."""
        current_state = classify_posture_state(is_head_drop_event, is_slumping_event)

        if self._last_timestamp is not None:
            elapsed = timestamp - self._last_timestamp
            if elapsed > self._max_gap_sec:
                # Khoang trong qua lon -- hoc sinh roi cho/bi che khuat lau.
                # KHONG tao segment nao cho khoang nay (loai khoi tu va mau
                # so), khac voi khoang binh thuong duoc tinh vao current_state.
                logger.debug(
                    "Seat '%s': khoang trong %.1fs (> max_gap_sec=%.1fs) -- "
                    "loai khoi tinh diem, khong gan cho trang thai nao.",
                    self._seat_id, elapsed, self._max_gap_sec,
                )
            elif elapsed > 0:
                self._segments.append(_Segment(self._last_timestamp, timestamp, current_state))

        self._last_timestamp = timestamp
        self._last_state = current_state
        self._prune_old_segments(timestamp)

    def _prune_old_segments(self, now: float) -> None:
        """Loai bo (hoac cat bot) cac segment nam ngoai cua so [now -
        window_sec, now] -- giu dung tinh than 'cua so truot' thay vi tich
        luy vo han nhu SeatEngagementTracker."""
        cutoff = now - self._window_sec
        pruned = []
        for seg in self._segments:
            if seg.end <= cutoff:
                continue  # hoan toan ngoai cua so -- bo han
            if seg.start < cutoff:
                seg = _Segment(cutoff, seg.end, seg.state)  # cat bot phan ngoai cua so
            pruned.append(seg)
        self._segments = pruned

    def compute_score(self) -> EngagementScore:
        """Tinh diem engagement CHI DUA TREN cac segment con trong cua so
        truot hien tai (da duoc _prune_old_segments() cat/loai bo o moi lan
        update()). Cong thuc giong het task 4.1/4.2, chi khac pham vi du
        lieu dau vao (windowed thay vi cumulative).

        head_drop_count/slumping_count duoc dem lai TU CAC SEGMENT CON
        TRONG CUA SO (khong phai bo dem rieng cong don qua thoi gian) --
        nen cung phan anh dung 'trong cua so gan day', nhat quan voi
        time_normal/time_slumping/time_head_drop.
        """
        time_by_state = {"normal": 0.0, "slumping": 0.0, "head_drop": 0.0}
        for seg in self._segments:
            time_by_state[seg.state] += seg.duration

        head_drop_count = 0
        slumping_count = 0
        previous_state = None
        for seg in self._segments:
            if seg.state == "head_drop" and previous_state != "head_drop":
                head_drop_count += 1
            if seg.state == "slumping" and previous_state != "slumping":
                slumping_count += 1
            previous_state = seg.state

        score = compute_score_from_durations(
            time_by_state["normal"],
            time_by_state["slumping"],
            time_by_state["head_drop"],
            self._slump_credit,
        )

        return EngagementScore(
            seat_id=self._seat_id,
            score=score,
            time_normal=time_by_state["normal"],
            time_slumping=time_by_state["slumping"],
            time_head_drop=time_by_state["head_drop"],
            head_drop_count=head_drop_count,
            slumping_count=slumping_count,
        )

    def reset(self) -> None:
        """Xoa toan bo segment dang luu (vi du bat dau session moi)."""
        self._segments.clear()
        self._last_timestamp = None
        self._last_state = None