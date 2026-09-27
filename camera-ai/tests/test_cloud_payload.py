import pytest

from src.privacy.cloud_payload import CloudPayloadError, make_cloud_payload


def test_cloud_payload_has_exact_allowlisted_fields():
    payload = make_cloud_payload("A1", [(12.345, 99.999)], 76.666).to_dict()
    assert set(payload) == {"seat_id", "keypoints", "engagement_score"}
    assert payload == {"seat_id": "A1", "keypoints": [[12.35, 100.0]], "engagement_score": 76.67}


def test_cloud_payload_rejects_invalid_keypoint():
    with pytest.raises(CloudPayloadError):
        make_cloud_payload("A1", [(float("nan"), 1)], 50)
