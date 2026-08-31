"""
test_frame_buffer.py -- Unit test cho FrameBuffer (src/capture/frame_buffer.py)
"""

import threading
import time

import pytest

from src.capture import FrameBuffer
from src.capture.camera_capture import Frame


def make_frame(index: int) -> Frame:
    return Frame(image=f"fake-image-{index}", timestamp=float(index), frame_index=index)


def test_maxsize_must_be_at_least_1():
    with pytest.raises(ValueError):
        FrameBuffer(maxsize=0)


def test_put_then_get_returns_same_frame():
    buf = FrameBuffer(maxsize=2)
    f = make_frame(1)
    buf.put(f)
    assert buf.get(timeout=0.1) == f


def test_get_returns_none_on_empty_after_timeout():
    buf = FrameBuffer(maxsize=2)
    start = time.time()
    result = buf.get(timeout=0.1)
    elapsed = time.time() - start
    assert result is None
    assert elapsed >= 0.09  # phai thuc su cho het timeout, khong tra ve ngay


def test_qsize_reflects_current_count():
    buf = FrameBuffer(maxsize=5)
    assert buf.qsize() == 0
    buf.put(make_frame(1))
    buf.put(make_frame(2))
    assert buf.qsize() == 2
    buf.get()
    assert buf.qsize() == 1


def test_drop_oldest_when_full():
    buf = FrameBuffer(maxsize=2)
    f1, f2, f3 = make_frame(1), make_frame(2), make_frame(3)

    buf.put(f1)
    buf.put(f2)
    assert buf.qsize() == 2

    buf.put(f3)  # buffer day -> phai bo f1 (cu nhat), giu f2 va f3

    assert buf.qsize() == 2
    assert buf.dropped_count == 1

    # Thu tu con lai phai la f2 roi f3 (f1 da bi loai)
    assert buf.get(timeout=0.1).frame_index == 2
    assert buf.get(timeout=0.1).frame_index == 3
    assert buf.get(timeout=0.1) is None  # buffer da rong


def test_dropped_count_starts_at_zero():
    buf = FrameBuffer(maxsize=3)
    assert buf.dropped_count == 0


def test_concurrent_put_does_not_crash_or_lose_count_consistency():
    """Nhieu thread cung put() dong thoi vao buffer nho -- khong duoc crash,
    va dropped_count + qsize cuoi cung phai khop voi tong so frame da put."""
    buf = FrameBuffer(maxsize=3)
    total_frames = 200
    n_threads = 4
    frames_per_thread = total_frames // n_threads

    def worker(start_index: int):
        for i in range(frames_per_thread):
            buf.put(make_frame(start_index + i))

    threads = [
        threading.Thread(target=worker, args=(t * frames_per_thread,))
        for t in range(n_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive(), "Thread khong hoan tat kip -- co the bi deadlock"

    # Tong so frame "bien mat" hop le (hoac con trong buffer, hoac bi dem la
    # dropped) phai khop voi tong so da put -- khong duoc am tham mat frame
    # ma khong duoc dem.
    assert buf.qsize() + buf.dropped_count == total_frames