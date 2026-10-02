"""Bien hanh vi dang dien ra (theo tung frame) thanh AlertEvent cho giao vien (UC09).

Detector (head_drop, BackTurnDetector, SideConversationDetector) bao hanh vi o
MOI frame khi no con duy tri; AlertManager dam bao:
- moi DOT (episode) hanh vi chi phat 1 alert,
- dot moi cua cung (seat, type) trong ``cooldown_sec`` sau alert truoc bi gom
  vao alert do (khong phat lai),
- chi phat khi phien dang chay (khong pause).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from src.privacy import AlertEvent, make_alert_event


@dataclass(frozen=True)
class AlertCandidate:
    """Hanh vi dang duy tri o frame hien tai; ``duration_sec`` la thoi gian da
    duy tri tinh den frame nay (theo detector)."""

    seat_id: str
    type: str
    duration_sec: float


class AlertManager:
    def __init__(self, session_id: str, *, cooldown_sec: float = 60.0, episode_gap_sec: float = 2.0) -> None:
        """
        cooldown_sec: sau 1 alert cua (seat, type), cac dot moi trong khoang nay
            bi gom (khong phat). GIA TRI KHOI DIEM, can thong nhat voi giao vien.
        episode_gap_sec: khong thay hanh vi qua khoang nay moi coi la het dot --
            mat 1-2 frame do che khuat/nhieu khong tach thanh dot moi.
        """
        if cooldown_sec < 0 or episode_gap_sec < 0:
            raise ValueError("cooldown_sec va episode_gap_sec phai >= 0.")
        self._session_id = session_id
        self._cooldown_sec = cooldown_sec
        self._episode_gap_sec = episode_gap_sec
        self._active = True
        self._last_seen: Dict[Tuple[str, str], float] = {}  # dot dang dien ra
        self._last_alert_at: Dict[Tuple[str, str], float] = {}

    @property
    def active(self) -> bool:
        return self._active

    def pause(self) -> None:
        """Tam dung phien: khong phat alert, bo cac dot dang theo doi (khi resume
        hanh vi con dien ra se tinh la dot moi). Cooldown van duoc nho."""
        self._active = False
        self._last_seen.clear()

    def resume(self) -> None:
        self._active = True

    def update(self, timestamp: float, candidates: Iterable[AlertCandidate]) -> List[AlertEvent]:
        """Goi 1 lan moi frame voi TAT CA hanh vi dang duy tri o frame do."""
        if not self._active:
            return []
        alerts = []
        for candidate in candidates:
            key = (candidate.seat_id, candidate.type)
            last_seen = self._last_seen.get(key)
            self._last_seen[key] = timestamp
            if last_seen is not None and timestamp - last_seen <= self._episode_gap_sec:
                continue  # van trong dot cu, da xu ly
            last_alert_at = self._last_alert_at.get(key)
            if last_alert_at is not None and timestamp - last_alert_at < self._cooldown_sec:
                continue  # dot moi nhung trong cooldown -> gom vao alert truoc
            alerts.append(
                make_alert_event(
                    self._session_id,
                    candidate.seat_id,
                    candidate.type,
                    max(0.0, timestamp - candidate.duration_sec),
                    candidate.duration_sec,
                )
            )
            self._last_alert_at[key] = timestamp
        # Bo dot da ket thuc de bo nho khong tang theo thoi gian phien.
        self._last_seen = {
            key: seen for key, seen in self._last_seen.items() if timestamp - seen <= self._episode_gap_sec
        }
        return alerts
