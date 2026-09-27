"""Kiem tra schema export khong the chua thong tin sinh trac hoc."""

import json

from src.engagement.engagement_score import EngagementScore
from src.privacy import anonymize_engagement, append_anonymized_record


def test_anonymized_export_has_only_allowlisted_metrics(tmp_path):
    score = EngagementScore("A1", 82.345, 12.0, 2.0, 1.0, 3, 1)
    record = anonymize_engagement(score, 123.4567, "NORMAL")

    assert record.to_dict() == {
        "seat_id": "A1",
        "observed_at_sec": 123.457,
        "engagement_score": 82.34,
        "posture_state": "NORMAL",
        "head_drop_events": 3,
        "slumping_events": 1,
    }
    output = tmp_path / "engagement.jsonl"
    append_anonymized_record(output, record)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert set(data) == set(record.to_dict())
    forbidden = {"image", "face", "embedding", "keypoints", "bbox", "name", "student_id"}
    assert not forbidden.intersection(data)
