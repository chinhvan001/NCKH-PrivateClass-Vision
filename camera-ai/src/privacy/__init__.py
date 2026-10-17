"""Tien ich bao ve privacy cho pipeline camera-ai."""

from .frame_lifecycle import dispose_frame, wipe_image
from .anonymize import anonymize_preview, blur_regions, face_regions_from_poses
from .engagement_export import (
    AnonymizedEngagementRecord,
    anonymize_engagement,
    append_anonymized_record,
)
from .alert_event import ALERT_TYPES, AlertEvent, AlertEventError, check_session_id, make_alert_event
from .session_output import MONITORING_STATUSES, SEAT_STATUSES, SeatEvaluation, SeatResult, SessionResult

__all__ = [
    "MONITORING_STATUSES",
    "SEAT_STATUSES",
    "SeatEvaluation",
    "SeatResult",
    "SessionResult",
    "ALERT_TYPES",
    "AlertEvent",
    "AlertEventError",
    "anonymize_preview",
    "anonymize_engagement",
    "append_anonymized_record",
    "AnonymizedEngagementRecord",
    "blur_regions",
    "check_session_id",
    "dispose_frame",
    "face_regions_from_poses",
    "make_alert_event",
    "wipe_image",
]
