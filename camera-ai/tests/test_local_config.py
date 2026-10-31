"""Test schema config local khong chua credential hay sinh trac hoc."""

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.config import LocalConfigError, LocalPipelineConfig


def valid_config():
    return {
        "schema_version": 2,
        "camera": {
            "camera_id": "CAM-1",
            "class_id": "CLASS-1",
            "source_env": "CAMERA_1_SOURCE",
            "width": 1280,
            "height": 720,
            "angle_type": "frontal",
        },
        "seating": {
            "corner_seats": {
                "first_row_first_column": [90, 100],
                "first_row_last_column": [230, 100],
                "last_row_last_column": [230, 300],
                "last_row_first_column": [90, 300],
            }
        },
        "sampling": {"capture_fps": 10, "inference_every_n_frames": 2},
        "thresholds": {
            "pose_confidence": 0.2,
            "iou_threshold": 0.5,
            "image_size": 960,
            "tile_size": 960,
            "tile_overlap": 0.2,
            "max_detections": 100,
            "conversation_duration_sec": 3,
            "conversation_max_distance_px": 260,
            "back_turn_duration_sec": 2,
            "back_turn_max_face_visibility": 0.2,
        },
        "schedule": {
            "timezone": "Asia/Ho_Chi_Minh",
            "windows": [{"days": ["mon", "tue"], "start": "07:00", "end": "17:00"}],
        },
        "privacy": {"frame_buffer_size": 1, "allow_persistent_output": False, "retention_days": 365},
    }


def test_parses_valid_config_and_reads_camera_source_from_environment(monkeypatch):
    monkeypatch.setenv("CAMERA_1_SOURCE", "0")
    config = LocalPipelineConfig.from_dict(valid_config())
    capture = config.to_capture_config()
    assert config.camera.camera_id == "CAM-1"
    assert capture.source == 0
    assert capture.target_fps == 10


@pytest.mark.parametrize(
    "path, value",
    [
        (("camera", "rtsp_url"), "rtsp://user:password@camera/stream"),
        (("privacy", "allow_persistent_output"), True),
        (("privacy", "frame_buffer_size"), 5),
        (("privacy", "retention_days"), 0),
        (("camera", "class_id"), "classes/CLASS-1"),  # thanh duong dan Firestore khac
        (("camera", "angle_type"), "side"),
        (("seating", "corner_seats"), {"first_row_first_column": [90, 100]}),
        (("seating", "student_map"), {"A1": "SV001"}),
    ],
)
def test_rejects_credentials_and_privacy_policy_violations(path, value):
    data = valid_config()
    data[path[0]][path[1]] = value
    with pytest.raises(LocalConfigError):
        LocalPipelineConfig.from_dict(data)


def test_can_load_example_schema_file():
    path = __import__("pathlib").Path(__file__).parents[1] / "config" / "local_pipeline.example.json"
    config = LocalPipelineConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert config.schedule.windows[0].start == "07:00"
    assert config.seating.corner_seats.last_row_last_column == (950.0, 260.0)


def test_rejects_corner_seat_that_is_not_a_pixel_pair():
    data = valid_config()
    data["seating"]["corner_seats"]["last_row_first_column"] = [90, -1]
    with pytest.raises(LocalConfigError, match="last_row_first_column"):
        LocalPipelineConfig.from_dict(data)


@pytest.mark.parametrize(
    "moment, allowed",
    [
        (datetime(2026, 10, 5, 7, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")), True),  # thu 2, mo cua so
        (datetime(2026, 10, 5, 16, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")), True),
        (datetime(2026, 10, 5, 17, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")), False),  # end khong tinh
        (datetime(2026, 10, 7, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")), False),  # thu 4 khong co lich
        (datetime(2026, 10, 5, 1, 0, tzinfo=timezone.utc), True),  # 08:00 gio Viet Nam
        (datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc), False),  # 18:00 gio Viet Nam
    ],
)
def test_schedule_allows_only_configured_local_windows(moment, allowed):
    assert LocalPipelineConfig.from_dict(valid_config()).schedule.allows(moment) is allowed


def test_rejects_unknown_timezone():
    data = valid_config()
    data["schedule"]["timezone"] = "Asia/Hanoi_Typo"
    with pytest.raises(LocalConfigError, match="timezone"):
        LocalPipelineConfig.from_dict(data)


def test_corner_seats_can_be_null_when_seats_are_drawn_on_the_web():
    data = valid_config()
    data["seating"]["corner_seats"] = None
    assert LocalPipelineConfig.from_dict(data).seating.corner_seats is None


def test_class_and_camera_source_can_be_left_to_the_web_admin():
    data = valid_config()
    data["camera"].update(class_id=None, source_env=None)
    config = LocalPipelineConfig.from_dict(data)
    assert config.camera.class_id is None
    source = "rtsp://admin:pw@10.0.0.5:554/stream1"  # camera_configs/{camera_id}.source
    assert config.to_capture_config(source).source == source
    with pytest.raises(LocalConfigError):
        config.to_capture_config(None)  # camera chua duoc them tren web
