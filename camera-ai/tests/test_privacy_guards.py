"""Guard test cho privacy invariant: khong ghi frame ra dia, frame duoc xoa
sau inference, log khong lo credential camera."""

import logging
import re
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.capture import CameraOpenError, CaptureConfig
from src.capture.camera_capture import CameraCapture, redact_source
from src.pipeline import run_pipeline
from src.seating.seat_grid import Seat, SeatGrid

SRC = Path(__file__).resolve().parents[1] / "src"
# Ghi anh/video ra dia. Demo (tests/) va tools/ duoc phep co VideoWriter co gate rieng.
_FRAME_WRITE = re.compile(r"\b(imwrite|VideoWriter|imencode)\b")


def test_production_code_never_writes_frames():
    offenders = [
        f"{path.relative_to(SRC)}:{number}"
        for path in SRC.rglob("*.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _FRAME_WRITE.search(line)
    ]
    assert offenders == []


class _KeepFrames:
    """Pose provider giu tham chieu toi moi frame de kiem tra sau khi pipeline chay."""

    def __init__(self):
        self.frames = []

    def detect(self, image_bgr):
        assert image_bgr.any(), "frame phai con pixel khi inference"
        self.frames.append(image_bgr)
        return []


def test_pipeline_wipes_every_frame_after_inference(tmp_path):
    video = tmp_path / "bright.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (320, 240))
    for _ in range(5):
        writer.write(np.full((240, 320, 3), 128, dtype=np.uint8))
    writer.release()
    provider = _KeepFrames()
    run_pipeline(
        CaptureConfig(source=str(video), target_fps=20.0),
        provider,
        SeatGrid([Seat("A1", 90.0, 100.0)]),
        on_record=lambda record: None,
        max_frames=5,
    )
    assert len(provider.frames) == 5
    assert all(not np.any(frame) for frame in provider.frames)


class _FailingInference(_KeepFrames):
    def detect(self, image_bgr):
        super().detect(image_bgr)
        raise RuntimeError("inference loi")


def test_frame_wiped_even_when_inference_fails(tmp_path):
    video = tmp_path / "bright.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (320, 240))
    writer.write(np.full((240, 320, 3), 128, dtype=np.uint8))
    writer.release()
    provider = _FailingInference()
    with pytest.raises(RuntimeError, match="inference loi"):
        run_pipeline(
            CaptureConfig(source=str(video), target_fps=20.0),
            provider,
            SeatGrid([Seat("A1", 90.0, 100.0)]),
            on_record=lambda record: None,
        )
    assert len(provider.frames) == 1
    assert not np.any(provider.frames[0])


@pytest.mark.parametrize(
    "source, expected",
    [
        ("rtsp://admin:S3cret@10.0.0.5:554/stream1", "rtsp://***@10.0.0.5:554/stream1"),
        ("http://user@cam.local/video", "http://***@cam.local/video"),
        ("rtsp://10.0.0.5/stream1", "rtsp://10.0.0.5/stream1"),
        (0, "0"),
    ],
)
def test_redact_source_hides_camera_credentials(source, expected):
    assert redact_source(source) == expected


class _UnreachableCamera:
    """Thay cv2.VideoCapture: mo that bai ngay, khong cho timeout mang."""

    def __init__(self, source):
        pass

    def isOpened(self):
        return False

    def set(self, *args):
        return False


def test_camera_open_failure_does_not_leak_credentials(caplog, monkeypatch):
    monkeypatch.setattr("src.capture.camera_capture.cv2.VideoCapture", _UnreachableCamera)
    source = "rtsp://admin:S3cret@10.0.0.5:554/stream1"
    with caplog.at_level(logging.INFO, logger="camera_ai.capture"):
        with pytest.raises(CameraOpenError) as error:
            CameraCapture(CaptureConfig(source=source)).open()
    assert "S3cret" not in str(error.value)
    assert "S3cret" not in caplog.text
