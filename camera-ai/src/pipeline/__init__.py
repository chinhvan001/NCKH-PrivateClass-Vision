"""Orchestration pipeline cho capture -> pose -> seating -> engagement."""

from .alert_manager import AlertCandidate, AlertManager
from .engagement_pipeline import EngagementEngine, PipelineRunResult, SeatObservation, run_pipeline

__all__ = ["AlertCandidate", "AlertManager", "EngagementEngine", "PipelineRunResult", "SeatObservation", "run_pipeline"]
