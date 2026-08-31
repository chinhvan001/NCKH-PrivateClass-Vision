"""
test_config.py -- Unit test cho CaptureConfig (src/capture/config.py)
"""

from src.capture import CaptureConfig


def test_default_values():
    cfg = CaptureConfig()
    assert cfg.source == 0
    assert cfg.width is None
    assert cfg.height is None
    assert cfg.target_fps == 15.0
    assert cfg.reconnect_initial_delay == 2.0
    assert cfg.reconnect_max_delay == 30.0


def test_from_env_uses_defaults_when_unset(monkeypatch):
    for var in ("CAMERA_SOURCE", "CAMERA_WIDTH", "CAMERA_HEIGHT", "CAMERA_FPS"):
        monkeypatch.delenv(var, raising=False)

    cfg = CaptureConfig.from_env()

    assert cfg.source == 0  # "0" -> ep kieu int thanh cong
    assert cfg.width is None
    assert cfg.height is None
    assert cfg.target_fps == 15.0


def test_from_env_parses_numeric_source_as_int(monkeypatch):
    monkeypatch.setenv("CAMERA_SOURCE", "2")
    cfg = CaptureConfig.from_env()
    assert cfg.source == 2
    assert isinstance(cfg.source, int)


def test_from_env_keeps_non_numeric_source_as_string(monkeypatch):
    monkeypatch.setenv("CAMERA_SOURCE", "rtsp://192.168.1.50/stream")
    cfg = CaptureConfig.from_env()
    assert cfg.source == "rtsp://192.168.1.50/stream"
    assert isinstance(cfg.source, str)


def test_from_env_parses_width_height_fps(monkeypatch):
    monkeypatch.setenv("CAMERA_WIDTH", "1280")
    monkeypatch.setenv("CAMERA_HEIGHT", "720")
    monkeypatch.setenv("CAMERA_FPS", "24.5")

    cfg = CaptureConfig.from_env()

    assert cfg.width == 1280
    assert cfg.height == 720
    assert cfg.target_fps == 24.5


def test_from_env_width_height_none_when_empty_string(monkeypatch):
    # Truong hop .env co dong "CAMERA_WIDTH=" (rong) -- khong duoc crash,
    # phai coi nhu chua thiet lap (None).
    monkeypatch.setenv("CAMERA_WIDTH", "")
    cfg = CaptureConfig.from_env()
    assert cfg.width is None