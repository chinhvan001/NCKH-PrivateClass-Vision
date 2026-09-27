"""Orchestration pipeline cho capture -> pose -> seating -> engagement."""

from .engagement_pipeline import PipelineRunResult, run_pipeline

__all__ = ["PipelineRunResult", "run_pipeline"]
