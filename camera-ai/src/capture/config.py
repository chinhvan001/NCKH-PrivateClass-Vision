"""
config.py -- Cau hinh cho module capture/
"""

import os
from dataclasses import dataclass
from typing import Optional, Union

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv chua duoc cai, van chay duoc voi gia tri mac dinh / bien moi
    # truong da co san trong process.
    pass


@dataclass
class CaptureConfig:
    """Cau hinh cho CameraCapture. Co the tao truc tiep hoac qua from_env().

    width/height de None nghia la giu nguyen do phan giai mac dinh cua camera
    (khong goi cv2.CAP_PROP_FRAME_WIDTH/HEIGHT).
    """

    source: Union[int, str] = 0
    width: Optional[int] = None
    height: Optional[int] = None
    target_fps: float = 15.0

    # Tham so cho co che tu ket noi lai (UC-CAM-01, luong phu / luong ngoai le)
    reconnect_initial_delay: float = 2.0
    reconnect_max_delay: float = 30.0
    reconnect_backoff_factor: float = 2.0
    max_consecutive_failures_before_alert: int = 10

    @classmethod
    def from_env(cls) -> "CaptureConfig":
        """Doc cau hinh tu bien moi truong (.env), dung gia tri mac dinh neu thieu.

        Bien moi truong ho tro:
            CAMERA_SOURCE  -- chi so webcam (vd '0') hoac URL RTSP/duong dan IP camera
            CAMERA_WIDTH   -- do rong khung hinh mong muon (bo trong = giu mac dinh)
            CAMERA_HEIGHT  -- do cao khung hinh mong muon (bo trong = giu mac dinh)
            CAMERA_FPS     -- FPS muc tieu de doc (mac dinh 15.0)
        """
        raw_source = os.getenv("CAMERA_SOURCE", "0")
        try:
            source: Union[int, str] = int(raw_source)
        except ValueError:
            source = raw_source  # vi du: rtsp://... hoac duong dan file video

        def _int_or_none(name: str) -> Optional[int]:
            val = os.getenv(name)
            return int(val) if val else None

        return cls(
            source=source,
            width=_int_or_none("CAMERA_WIDTH"),
            height=_int_or_none("CAMERA_HEIGHT"),
            target_fps=float(os.getenv("CAMERA_FPS", "15.0")),
        )