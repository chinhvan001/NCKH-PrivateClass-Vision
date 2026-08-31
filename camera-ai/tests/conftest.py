"""
conftest.py -- Fixture dung chung cho toan bo test suite cua camera-ai.

Them thu muc goc camera-ai/ vao sys.path de cac test import duoc `src.xxx`
bat ke pytest duoc goi tu dau (tu thu muc goc, tu trong tests/, hay qua IDE).
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

CAMERA_AI_ROOT = Path(__file__).resolve().parent.parent
if str(CAMERA_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(CAMERA_AI_ROOT))


@pytest.fixture
def synthetic_video(tmp_path) -> str:
    """Tao mot file video gia lap ngan (30 khung hinh, 320x240, 20fps) de dung
    lam CAMERA_SOURCE trong test, thay the cho webcam that (khong co san trong
    moi truong CI/test).

    Tra ve duong dan (str) toi file video, tu dong don dep sau khi test xong
    nho tmp_path (fixture co san cua pytest).
    """
    video_path = tmp_path / "synthetic.mp4"
    writer = cv2.VideoWriter(
        str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (320, 240)
    )
    for i in range(30):
        frame = np.full((240, 320, 3), (i * 8) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return str(video_path)