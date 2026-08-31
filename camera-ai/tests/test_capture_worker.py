"""
test_capture_worker.py -- Unit test cho CaptureWorker (src/capture/capture_worker.py)
"""

import time

import pytest

from src.capture import CameraOpenError, CaptureConfig, CaptureWorker


def test_start_raises_camera_open_error_and_no_thread_created():
    worker = CaptureWorker(CaptureConfig(source="duong_dan_khong_ton_tai.mp4"))
    with pytest.raises(CameraOpenError):
        worker.start()
    assert worker.is_alive is False


def test_start_stop_lifecycle(synthetic_video):
    cfg = CaptureConfig(source=synthetic_video, target_fps=20)
    worker = CaptureWorker(cfg, buffer_size=3)

    worker.start()
    try:
        assert worker.is_alive is True
    finally:
        worker.stop(timeout=3.0)

    assert worker.is_alive is False


def test_stop_is_safe_even_if_never_started():
    worker = CaptureWorker(CaptureConfig(source="khong_quan_trong.mp4"))
    worker.stop()  # khong duoc raise exception
    assert worker.is_alive is False


def test_worker_delivers_frames_through_buffer(synthetic_video):
    cfg = CaptureConfig(source=synthetic_video, target_fps=20)
    worker = CaptureWorker(cfg, buffer_size=3)
    worker.start()

    try:
        collected = []
        deadline = time.time() + 5.0
        while len(collected) < 5 and time.time() < deadline:
            frame = worker.buffer.get(timeout=1.0)
            if frame is not None:
                collected.append(frame.frame_index)
    finally:
        worker.stop(timeout=3.0)

    assert len(collected) >= 5
    # frame_index phai tang dan (khong nhat thiet lien tuc tuyet doi neu co
    # frame bi drop, nhung phai tang, khong duoc lap lai hay giam).
    assert collected == sorted(collected)
    assert len(set(collected)) == len(collected)  # khong trung lap


def test_dropped_count_increases_when_consumer_is_slow(synthetic_video):
    """Producer nhanh (fps cao) + buffer rat nho + consumer khong doc gi ->
    buffer phai drop frame thay vi phinh to vo han."""
    cfg = CaptureConfig(source=synthetic_video, target_fps=30)
    worker = CaptureWorker(cfg, buffer_size=2)
    worker.start()

    try:
        time.sleep(1.0)  # khong doc gi ca -- ep buffer phai day nhieu lan
    finally:
        worker.stop(timeout=3.0)

    assert worker.buffer.dropped_count > 0
    assert worker.buffer.qsize() <= 2  # khong bao gio vuot maxsize