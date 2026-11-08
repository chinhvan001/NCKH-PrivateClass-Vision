import sys
from unittest.mock import MagicMock, patch

# Mock các thư viện đồ họa máy ảnh nếu môi trường test chạy thuần backend
if "cv2" not in sys.modules:
    sys.modules["cv2"] = MagicMock()

from src.sync.concentration_client import ConcentrationHttpClient


def test_send_concentration_payload_empty_data():
    """Kiểm tra xử lý khi thiếu classroom_id hoặc students."""
    client = ConcentrationHttpClient()
    assert client.send_concentration_payload("", [{"student_id": "ST1"}]) is None
    assert client.send_concentration_payload("CR_1", []) is None


@patch("requests.Session.post")
def test_send_concentration_payload_success(mock_post):
    """Kiểm tra gửi HTTP POST thành công."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {"average_score": 96.0}
    }
    mock_post.return_value = mock_resp

    client = ConcentrationHttpClient(backend_base_url="http://localhost:5000")
    students = [
        {"student_id": "HS01", "behavior_state": "attentive", "duration_counter": 3.0}
    ]
    res = client.send_concentration_payload("CR_101", students)

    assert res is not None
    assert res["success"] is True
    assert res["data"]["average_score"] == 96.0
    mock_post.assert_called_once()
