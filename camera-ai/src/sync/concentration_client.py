"""
Camera-AI Edge Node: Concentration HTTP Client
Module gửi dữ liệu hành vi học sinh định kỳ mỗi 3-5 giây từ Edge Node sang Backend API
thông qua giao thức HTTP POST.

Payload mẫu:
{
    "classroom_id": "CR_101",
    "students": [
        {
            "student_id": "ST_001",
            "behavior_state": "attentive",
            "duration_counter": 3.5,
            "seat_id": "S01"
        },
        ...
    ]
}
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("camera_ai.concentration_client")


class ConcentrationHttpClient:
    """HTTP Client gửi dữ liệu phân tích hành vi học sinh tới Backend Concentration Service."""

    def __init__(
        self,
        backend_base_url: str = "http://127.0.0.1:5000",
        endpoint: str = "/api/v1/concentration/process-score",
        timeout: float = 3.0,
    ) -> None:
        """
        :param backend_base_url: URL gốc của Backend Server (vd: http://127.0.0.1:5000).
        :param endpoint: Đường dẫn API xử lý điểm tập trung.
        :param timeout: Thời gian chờ response tối đa (giây).
        """
        self.backend_base_url = backend_base_url.rstrip("/")
        self.endpoint = endpoint
        self.url = f"{self.backend_base_url}{self.endpoint}"
        self.timeout = timeout
        self.session = requests.Session()

    def send_concentration_payload(
        self,
        classroom_id: str,
        students: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Gửi payload điểm tập trung tới Backend.

        :param classroom_id: Mã định danh lớp học.
        :param students: Danh sách dict học sinh gồm student_id, behavior_state, duration_counter.
        :return: Response JSON data từ backend nếu thành công, None nếu thất bại.
        """
        if not classroom_id:
            logger.error("Không thể gửi payload: classroom_id trống.")
            return None

        if not students:
            logger.warning("Danh sách students trống, bỏ qua gửi request.")
            return None

        payload = {
            "classroom_id": classroom_id,
            "students": students,
            "timestamp": time.time(),
        }

        try:
            response = self.session.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "Gửi điểm tập trung thành công: lớp=%s, số HS=%d, điểm TB=%.2f",
                    classroom_id,
                    len(students),
                    data.get("data", {}).get("average_score", 0.0),
                )
                return data
            else:
                logger.error(
                    "Backend trả về mã lỗi HTTP %d: %s",
                    response.status_code,
                    response.text,
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("Timeout khi gửi dữ liệu tới Backend (%s) sau %.1fs", self.url, self.timeout)
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Không thể kết nối tới Backend tại %s. Vui lòng kiểm tra server.", self.url)
            return None
        except Exception as exc:
            logger.error("Lỗi bất ngờ khi gửi dữ liệu tới Backend: %s", str(exc), exc_info=True)
            return None
