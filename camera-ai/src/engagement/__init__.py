"""
Module engagement/ -- tinh cac chi so lien quan muc do tap trung tu skeleton,
theo huong skeleton/pose-based da chot sau pivot (Algorithm-Pivot-Proposal.docx).
"""

from .engagement_score import (
    DEFAULT_SLUMP_CREDIT,
    EngagementScore,
    SeatEngagementTracker,
    classify_posture_state,
    compute_score_from_durations,
)
from .rolling_engagement import DEFAULT_MAX_GAP_SEC, RollingSeatEngagementTracker

__all__ = [
    "SeatEngagementTracker",
    "RollingSeatEngagementTracker",
    "EngagementScore",
    "DEFAULT_SLUMP_CREDIT",
    "DEFAULT_MAX_GAP_SEC",
    "classify_posture_state",
    "compute_score_from_durations",
]