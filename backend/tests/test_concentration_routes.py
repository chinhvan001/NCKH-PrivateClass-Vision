import json
import pytest
from unittest.mock import patch, MagicMock

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_process_score_missing_payload(client):
    """Gửi body rỗng hoặc không phải JSON -> trả về 400 Bad Request."""
    response = client.post("/api/v1/concentration/process-score", data="not json")
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False


def test_process_score_missing_classroom_id(client):
    """Thiếu trường classroom_id -> trả về 400."""
    payload = {
        "students": [
            {"student_id": "ST_01", "behavior_state": "attentive"}
        ]
    }
    response = client.post(
        "/api/v1/concentration/process-score",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert "classroom_id" in res_data["message"]


def test_process_score_invalid_behavior_state(client):
    """Hành vi không nằm trong bảng trọng số -> trả về 400."""
    payload = {
        "classroom_id": "CR_101",
        "students": [
            {"student_id": "ST_01", "behavior_state": "invalid_state"}
        ]
    }
    response = client.post(
        "/api/v1/concentration/process-score",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    res_data = response.get_json()
    assert res_data["success"] is False
    assert len(res_data["errors"]) > 0


@patch("routes.concentration_routes._service.process_camera_ai_payload")
def test_process_score_success(mock_process, client):
    """Gửi payload hợp lệ -> trả về 200 OK với kết quả tính toán."""
    mock_process.return_value = {
        "success": True,
        "classroom_id": "CR_101",
        "total_students": 2,
        "saved_count": 2,
        "average_score": 95.5,
        "results": [
            {
                "student_id": "ST_01",
                "previous_score": 100.0,
                "current_score": 100.0,
                "behavior_state": "attentive",
                "delta": 1.0,
                "multiplier": 1.0
            },
            {
                "student_id": "ST_02",
                "previous_score": 100.0,
                "current_score": 91.0,
                "behavior_state": "using_phone",
                "delta": -9.0,
                "multiplier": 1.5
            }
        ]
    }

    payload = {
        "classroom_id": "CR_101",
        "students": [
            {"student_id": "ST_01", "behavior_state": "attentive", "duration_counter": 5.0},
            {"student_id": "ST_02", "behavior_state": "using_phone", "duration_counter": 10.0}
        ]
    }

    response = client.post(
        "/api/v1/concentration/process-score",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["total_students"] == 2
    mock_process.assert_called_once()


@patch("routes.concentration_routes._service.get_student_history")
def test_get_student_history_route(mock_history, client):
    """Kiểm tra endpoint lấy history log."""
    mock_history.return_value = [
        {"id": "doc1", "score": 100.0, "timestamp": "2026-11-07T10:00:00Z"},
        {"id": "doc2", "score": 97.0, "timestamp": "2026-11-07T10:00:05Z"},
    ]

    response = client.get("/api/v1/concentration/history/CR_101/ST_01?limit=50")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    assert res_data["total_records"] == 2
    mock_history.assert_called_once_with("CR_101", "ST_01", limit=50)
