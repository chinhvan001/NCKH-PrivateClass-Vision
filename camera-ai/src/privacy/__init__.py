"""Tien ich bao ve privacy cho pipeline camera-ai."""

from .frame_lifecycle import dispose_frame, wipe_image
from .anonymize import anonymize_preview, blur_regions, face_regions_from_poses
from .engagement_export import (
    AnonymizedEngagementRecord,
    anonymize_engagement,
    append_anonymized_record,
)
from .cloud_payload import CloudEngagementPayload, CloudPayloadError, make_cloud_payload
from .alert_event import ALERT_TYPES, AlertEvent, AlertEventError, make_alert_event

__all__ = [
    "ALERT_TYPES",
    "AlertEvent",
    "AlertEventError",
    "anonymize_preview",
    "anonymize_engagement",
    "append_anonymized_record",
    "AnonymizedEngagementRecord",
    "blur_regions",
    "CloudEngagementPayload",
    "CloudPayloadError",
    "dispose_frame",
    "face_regions_from_poses",
    "make_alert_event",
    "make_cloud_payload",
    "wipe_image",
]
