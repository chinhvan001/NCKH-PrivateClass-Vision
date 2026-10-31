"""
test_camera_capture.py -- Unit test cho CameraCapture (src/capture/camera_capture.py)

Dung file video gia lap (fixture synthetic_video trong conftest.py) thay cho
webcam that. Cac test lien quan reconnect/backoff deu override
reconnect_initial_delay ve gia tri rat nho de test chay nhanh.
"""

import time

import cv2
import numpy as np
import pytest

from src.capture import CameraCapture, CameraOpenError, CaptureConfig


def test_open_success_with_valid_video_file(synthetic_video):
    cam = CameraCapture(CaptureConfig(source=synthetic_video))
    cam.open()
    try:
        assert cam.is_open is True
    finally:
        cam.close()
    assert cam.is_open is False


def test_open_failure_raises_camera_open_error():
    cam = CameraCapture(CaptureConfig(source="duong_dan_khong_ton_tai.mp4"))
    with pytest.raises(CameraOpenError):
        cam.open()
    assert cam.is_open is False


def test_read_before_open_raises_runtime_error(synthetic_video):
    cam = CameraCapture(CaptureConfig(source=synthetic_video))
    with pytest.raises(RuntimeError):
        cam.read()


def test_read_returns_frames_with_incrementing_index(synthetic_video):
    cam = CameraCapture(CaptureConfig(source=synthetic_video, target_fps=30))
    cam.open()
    try:
        f1 = cam.read()
        f2 = cam.read()
        f3 = cam.read()
    finally:
        cam.close()

    assert f1.frame_index == 1
    assert f2.frame_index == 2
    assert f3.frame_index == 3
    assert f1.image is not None


def test_context_manager_opens_and_closes(synthetic_video):
    with CameraCapture(CaptureConfig(source=synthetic_video)) as cam:
        assert cam.is_open is True
        frame = cam.read()
        assert frame is not None
    assert cam.is_open is False


def test_frames_generator_throttles_to_target_fps(synthetic_video):
    """Kiem tra frames() thuc su gioi han toc do theo target_fps -- khong chi
    doc nhanh het muc co the. Frame dau tien phat ngay (khong doi), tu frame
    thu 2 tro di moi throttle -- nen thoi gian ly thuyet toi thieu de nhan N
    frame la (N-1)/target_fps.
    """
    target_fps = 10
    n_frames = 4
    cam = CameraCapture(CaptureConfig(source=synthetic_video, target_fps=target_fps))
    cam.open()
    try:
        start = time.time()
        count = 0
        for _ in cam.frames():
            count += 1
            if count >= n_frames:
                break
        elapsed = time.time() - start
    finally:
        cam.close()

    expected_min = (n_frames - 1) / target_fps
    # Cho phep sai so nho (may test co the cham hon may that mot chut khi
    # thuc thi cac phep tinh giua cac lan doc).
    assert elapsed >= expected_min * 0.85, (
        f"frames() khong throttle dung: mat {elapsed:.3f}s cho {n_frames} "
        f"frame, ky vong toi thieu {expected_min:.3f}s"
    )


def test_reconnect_after_source_exhausted(synthetic_video):
    """Khi video het frame (mo phong camera mat tin hieu), read() phai tra ve
    None thay vi crash, va lan doc tiep theo sau do phai tu phuc hoi thanh
    cong (video duoc mo lai tu dau)."""
    cfg = CaptureConfig(
        source=synthetic_video,
        target_fps=30,
        reconnect_initial_delay=0.05,  # rat nho de test chay nhanh
        reconnect_max_delay=0.2,
    )
    cam = CameraCapture(cfg)
    cam.open()
    try:
        # Doc het 30 frame co san trong video gia lap
        for _ in range(30):
            frame = cam.read()
            assert frame is not None

        # Frame thu 31: video da het -> phai kich hoat reconnect, tra ve None,
        # KHONG duoc raise exception.
        result = cam.read()
        assert result is None

        # Sau reconnect (video duoc mo lai tu dau), doc tiep phai thanh cong.
        frame_after = cam.read()
        assert frame_after is not None
    finally:
        cam.close()


def test_live_video_runs_in_real_time_and_loops_like_a_camera(synthetic_video, caplog):
    """--video: doc cham hon FPS cua video thi bo cac frame da qua (nhu camera that, khong
    phat cham lai), het file thi phat lai tu dau ma khong coi la mat camera."""
    # synthetic_video: 30 frame, 20 fps (1.5 s), frame i co mau i*8
    with CameraCapture(CaptureConfig(source=synthetic_video, target_fps=5, live_video=True)) as cam:
        frames = cam.frames()
        shades = [int(next(frames).image[0, 0, 0]) for _ in range(10)]

    steps = [after - before for before, after in zip(shades, shades[1:])]
    assert sorted(steps)[len(steps) // 2] >= 24  # ~4 frame video moi lan doc (20 fps / 5 fps), khong phai 1
    assert min(steps) < 0  # qua 1.5 s thi quay lai dau video
    assert "that bai" not in caplog.text


def test_apply_config_same_source_updates_without_reopen(synthetic_video):
    cam = CameraCapture(CaptureConfig(source=synthetic_video, target_fps=10))
    cam.open()
    try:
        new_cfg = CaptureConfig(source=synthetic_video, target_fps=25, width=200, height=150)
        cam.apply_config(new_cfg)  # khong duoc raise exception
        assert cam.is_open is True  # van dang mo, khong bi dong/mo lai
        frame = cam.read()
        assert frame is not None
    finally:
        cam.close()


class _LiveCamera:
    """Camera mang gia lap phat 100 fps du co ai doc hay khong: grab() cho frame ke
    tiep, anh retrieve() chua so thu tu frame."""

    def __init__(self, *args):
        self.count = 0

    def isOpened(self):
        return True

    def grab(self):
        time.sleep(0.01)
        self.count += 1
        return True

    def retrieve(self):
        return True, np.full((1, 1), self.count, np.int32)

    def read(self):
        self.grab()
        return self.retrieve()

    def get(self, prop):
        return 0

    def release(self):
        pass


def test_network_stream_keeps_only_the_newest_frame(monkeypatch):
    """Ngu giua hai lan doc nhu voi file thi frame cua camera mang don lai va tre dan:
    frames() phai bo cac frame toi truoc han, giu frame moi nhat."""
    monkeypatch.setattr(cv2, "VideoCapture", _LiveCamera)
    with CameraCapture(CaptureConfig(source="rtsp://cam/stream", target_fps=10)) as cam:
        frames = cam.frames()
        counts = [int(next(frames).image[0, 0]) for _ in range(3)]
    assert counts[2] - counts[1] >= 5  # ~10 frame camera giua hai frame giu lai (100 fps / 10 fps)
