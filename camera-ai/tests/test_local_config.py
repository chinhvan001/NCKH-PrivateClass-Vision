"""Test schema config local khong chua credential hay sinh trac hoc."""

import json

import pytest

from src.config import LocalConfigError, LocalPipelineConfig


def valid_config():
    return {
        "schema_version": 1,
        "camera": {"camera_id": "CAM-1", "classroom_id": "ROOM-1", "source_env": "CAMERA_1_SOURCE", "width": 1280, "height": 720},
        "sampling": {"capture_fps": 10, "inference_every_n_frames": 2},
        "thresholds": {"pose_confidence": 0.2, "iou_threshold": 0.5, "image_size": 960, "tile_size": 960, "tile_overlap": 0.2, "max_detections": 100, "conversation_duration_sec": 3, "conversation_max_distance_px": 260, "back_turn_duration_sec": 2, "back_turn_max_face_visibility": 0.2},
        "schedule": {"timezone": "Asia/Ho_Chi_Minh", "windows": [{"days": ["mon", "tue"], "start": "07:00", "end": "17:00"}]},
        "privacy": {"frame_buffer_size": 1, "allow_persistent_output": False},
    }


def test_parses_valid_config_and_reads_camera_source_from_environment(monkeypatch):
    monkeypatch.setenv("CAMERA_1_SOURCE", "0")
    config = LocalPipelineConfig.from_dict(valid_config())
    capture = config.to_capture_config()
    assert config.camera.camera_id == "CAM-1"
    assert capture.source == 0
    assert capture.target_fps == 10


@pytest.mark.parametrize("path, value", [
    (("camera", "rtsp_url"), "rtsp://user:password@camera/stream"),
    (("privacy", "allow_persistent_output"), True),
    (("privacy", "frame_buffer_size"), 5),
])
def test_rejects_credentials_and_privacy_policy_violations(path, value):
    data = valid_config()
    data[path[0]][path[1]] = value
    with pytest.raises(LocalConfigError):
        LocalPipelineConfig.from_dict(data)


def test_can_load_example_schema_file():
    path = __import__("pathlib").Path(__file__).parents[1] / "config" / "local_pipeline.example.json"
    config = LocalPipelineConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert config.schedule.windows[0].start == "07:00"
