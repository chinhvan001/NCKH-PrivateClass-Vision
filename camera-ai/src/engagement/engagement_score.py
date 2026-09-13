"""
engagement_score.py -- Cai dat cong thuc cham diem engagement tu posture,
theo dung thiet ke da chot o task 4.1 (xem tai lieu
Engagement-Scoring-Formula-Task4.1.docx).

Nhan dau vao la (is_head_drop_event, is_slumping_event) tra ve tu
PostureMonitor.update() (module posture_monitor.py, task 3.6) cho MOT seat,
tich luy thoi gian o tung trang thai qua toan bo session, va tinh diem
engagement 0-100 theo cong thuc da thiet ke.
"""

from dataclasses import dataclass
from typing import Optional

# He so "tin chi mot phan" cho thoi gian slumping -- xem Muc 4, tai lieu
# thiet ke task 4.1. GIA TRI KHOI DIEM, CHUA kiem chung bang du lieu that.
DEFAULT_SLUMP_CREDIT = 0.5


def classify_posture_state(is_head_drop_event: bool, is_slumping_event: bool) -> str:
    """Phan loai 1 thoi diem vao DUNG MOT trong 3 trang thai, uu tien
    head_drop cao hon slumping neu ca hai cung True (xem Muc 3, tai lieu
    thiet ke task 4.1). Dung chung boi ca SeatEngagementTracker (cumulative,
    task 4.2) va RollingSeatEngagementTracker (windowed, task 4.3)."""
    if is_head_drop_event:
        return "head_drop"
    if is_slumping_event:
        return "slumping"
    return "normal"


def compute_score_from_durations(
    time_normal: float,
    time_slumping: float,
    time_head_drop: float,
    slump_credit: float = DEFAULT_SLUMP_CREDIT,
) -> Optional[float]:
    """Ap dung cong thuc Muc 4 (tai lieu thiet ke task 4.1) tren 3 gia tri
    thoi luong cho truoc, tra ve None neu tong thoi luong = 0 (khong co du
    lieu). Ham THUAN, dung chung boi ca 2 loai tracker (cumulative va
    rolling) de tranh trung lap logic cong thuc o 2 noi."""
    time_total = time_normal + time_slumping + time_head_drop
    if time_total <= 0:
        return None

    ratio_slumping = time_slumping / time_total
    ratio_head_drop = time_head_drop / time_total
    raw_score = 100 * (1 - ratio_head_drop - (1 - slump_credit) * ratio_slumping)
    return max(0.0, min(100.0, raw_score))


@dataclass
class EngagementScore:
    """Ket qua tinh diem engagement cho MOT seat (cumulative hoac windowed
    tuy loai tracker tao ra ket qua nay).

    score: None neu seat CHUA TUNG co du lieu nao (time_total == 0 -- vi du
        hoc sinh vang mat ca buoi, hoac chua co lan update() nao). KHONG
        PHAI 0 -- 0 nghia la co du lieu va engagement rat kem, con None
        nghia la khong co thong tin gi ca, can phan biet ro 2 truong hop
        nay khi hien thi cho giao vien.
    head_drop_count / slumping_count: so LAN BAT DAU một chuỗi sự kiện MỚI
        (khong phai so frame) -- chi so PHU, KHONG nam trong cong thuc tinh
        score (xem Muc 5, tai lieu thiet ke).
    """

    seat_id: str
    score: Optional[float]
    time_normal: float
    time_slumping: float
    time_head_drop: float
    head_drop_count: int
    slumping_count: int

    @property
    def time_total(self) -> float:
        return self.time_normal + self.time_slumping + self.time_head_drop


class SeatEngagementTracker:
    """Tich luy thoi gian o tung trang thai (NORMAL / SLUMPING / HEAD_DROP,
    LOAI TRU LAN NHAU -- xem Muc 3 tai lieu thiet ke) cho MOT seat qua TOAN
    BO SESSION (tu dau den gio, khong bi cua so cat bo), va tinh diem
    engagement theo cong thuc da chot o task 4.1.

    Dung cho BAO CAO CUOI BUOI (tong ket toan session). Neu can hien thi
    "engagement hien tai" theo cua so gan day, dung
    RollingSeatEngagementTracker (rolling_engagement.py, task 4.3) thay the
    hoac song song.

    Cach dung (moi seat can 1 instance rieng):
        tracker = SeatEngagementTracker(seat_id="A1")
        for frame in session:
            is_drop, is_slump = posture_monitor.update(frame.timestamp, ratio, deviation)
            tracker.update(frame.timestamp, is_drop, is_slump)
        result = tracker.compute_score()
        print(result.score, result.head_drop_count)
    """

    def __init__(self, seat_id: str, slump_credit: float = DEFAULT_SLUMP_CREDIT):
        self._seat_id = seat_id
        self._slump_credit = slump_credit

        self._time_normal = 0.0
        self._time_slumping = 0.0
        self._time_head_drop = 0.0
        self._head_drop_count = 0
        self._slumping_count = 0

        self._last_timestamp: Optional[float] = None
        self._last_state: Optional[str] = None  # "normal" | "slumping" | "head_drop"

    def update(self, timestamp: float, is_head_drop_event: bool, is_slumping_event: bool) -> None:
        """Goi MOT LAN moi khi PostureMonitor.update() tra ve ket qua moi
        cho seat nay.

        Khoang thoi gian [lan goi truoc, lan goi nay] duoc tinh vao trang
        thai VUA DUOC XAC NHAN TAI LAN GOI NAY (khong phai trang thai cu):
        moi lan update() bao cao trang thai hien tai, ham y trang thai do da
        dung suot tu lan quan sat truoc den gio -- day la cach dien giai tu
        nhien khi lay mau dinh ky (frame moi xac nhan "van dang o trang thai
        X" tuc la X dung suot khoang vua troi qua)."""
        current_state = classify_posture_state(is_head_drop_event, is_slumping_event)

        if self._last_timestamp is not None:
            elapsed = timestamp - self._last_timestamp
            if elapsed > 0:
                self._accumulate(current_state, elapsed)

        # Dem so LAN BAT DAU 1 chuoi su kien MOI (chuyen tu trang thai khac
        # sang head_drop/slumping) -- khong dem lai moi lan update() trong
        # khi van dang o giua 1 chuoi da bat dau truoc do.
        if current_state == "head_drop" and self._last_state != "head_drop":
            self._head_drop_count += 1
        if current_state == "slumping" and self._last_state != "slumping":
            self._slumping_count += 1

        self._last_timestamp = timestamp
        self._last_state = current_state

    @staticmethod
    def _classify(is_head_drop_event: bool, is_slumping_event: bool) -> str:
        """Giu lai de tuong thich nguoc -- logic that su nam o
        classify_posture_state(), dung chung voi RollingSeatEngagementTracker."""
        return classify_posture_state(is_head_drop_event, is_slumping_event)

    def _accumulate(self, state: str, elapsed: float) -> None:
        if state == "head_drop":
            self._time_head_drop += elapsed
        elif state == "slumping":
            self._time_slumping += elapsed
        else:
            self._time_normal += elapsed

    def compute_score(self) -> EngagementScore:
        """Tinh diem engagement TICH LUY tu dau session den lan update()
        gan nhat, theo dung cong thuc Muc 4 (tai lieu thiet ke task 4.1).

        score = None neu time_total == 0 (seat chua tung co du lieu -- KHONG
        gay ZeroDivisionError).
        """
        score = compute_score_from_durations(
            self._time_normal, self._time_slumping, self._time_head_drop, self._slump_credit
        )

        return EngagementScore(
            seat_id=self._seat_id,
            score=score,
            time_normal=self._time_normal,
            time_slumping=self._time_slumping,
            time_head_drop=self._time_head_drop,
            head_drop_count=self._head_drop_count,
            slumping_count=self._slumping_count,
        )

    def reset(self) -> None:
        """Reset toan bo trang thai tich luy (vi du bat dau session moi)."""
        self._time_normal = 0.0
        self._time_slumping = 0.0
        self._time_head_drop = 0.0
        self._head_drop_count = 0
        self._slumping_count = 0
        self._last_timestamp = None
        self._last_state = None