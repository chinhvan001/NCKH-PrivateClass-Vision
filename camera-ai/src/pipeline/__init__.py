"""Orchestration pipeline cho capture -> pose -> seating -> engagement."""

from .alert_manager import AlertCandidate, AlertManager
from .engagement_pipeline import (
    EngagementEngine,
    FrameResult,
    PipelineRunResult,
    SeatObservation,
    process_frame,
    run_pipeline,
)
from .edge_runtime import EdgeRuntime

__all__ = [
    "AlertCandidate",
    "AlertManager",
    "EdgeRuntime",
    "EngagementEngine",
    "FrameResult",
    "PipelineRunResult",
    "SeatObservation",
    "process_frame",
    "run_pipeline",
]
