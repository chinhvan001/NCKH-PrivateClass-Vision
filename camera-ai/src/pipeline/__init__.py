"""Orchestration pipeline cho capture -> pose -> seating -> engagement."""

from .alert_manager import AlertCandidate, AlertManager
from .engagement_pipeline import EngagementEngine, FrameResult, PipelineRunResult, SeatObservation, run_pipeline

__all__ = [
    "AlertCandidate",
    "AlertManager",
    "EngagementEngine",
    "FrameResult",
    "PipelineRunResult",
    "SeatObservation",
    "run_pipeline",
]
