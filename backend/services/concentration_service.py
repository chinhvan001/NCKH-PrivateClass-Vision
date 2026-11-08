"""
Business Logic Tier (Service): ConcentrationService
Chịu trách nhiệm thực hiện toàn bộ thuật toán tính toán điểm tập trung động của học sinh:
- Điểm mặc định khởi tạo từ 100.0.
- Bảng trọng số hành vi: attentive (+1.0), slightly_distracted (-1.5), looking_down (-3.0),
  sleeping (-4.5), using_phone (-6.0), away_from_seat (-4.0), active_participating (+4.0).
- Hệ số lũy tiến vi phạm theo thời gian: multiplier = min(2.5, 1.0 + (duration / 20.0)) cho hành vi bị trừ điểm.
- Giới hạn (clamping) điểm số chặt chẽ trong khoảng [0.0, 100.0].
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from repositories.concentration_repository import ConcentrationRepository

logger = logging.getLogger("concentration.service")

# 1. Bảng trọng số trạng thái hành vi theo đặc tả hệ thống
BEHAVIOR_WEIGHTS: Dict[str, float] = {
    "attentive": 1.0,               # Tập trung nghe giảng: +1.0
    "slightly_distracted": -1.5,    # Mất tập trung nhẹ (nhìn chỗ khác): -1.5
    "looking_down": -3.0,           # Cúi đầu: -3.0
    "sleeping": -4.5,               # Gục đầu ngủ: -4.5
    "using_phone": -6.0,            # Sử dụng điện thoại trong giờ: -6.0
    "away_from_seat": -4.0,         # Rời khỏi chỗ ngồi: -4.0
    "active_participating": 4.0,    # Tích cực phát biểu/tương tác: +4.0
}

# Tập hợp các hành vi hợp lệ
VALID_BEHAVIOR_STATES = frozenset(BEHAVIOR_WEIGHTS.keys())

DEFAULT_INITIAL_SCORE = 100.0
MIN_SCORE = 0.0
MAX_SCORE = 100.0
MAX_PENALTY_MULTIPLIER = 2.5
DURATION_SCALE_FACTOR = 20.0


class ConcentrationService:
    """Service xử lý logic tính điểm tập trung và điều phối cập nhật dữ liệu."""

    def __init__(self, repository: Optional[ConcentrationRepository] = None) -> None:
        """
        Khởi tạo service với repository tương ứng.
        :param repository: ConcentrationRepository instance (Dependency Injection).
        """
        self.repository = repository or ConcentrationRepository()

    @staticmethod
    def calculate_multiplier(behavior_state: str, duration_counter: float) -> float:
        """
        Tính hệ số lũy tiến multiplier theo thời gian kéo dài hành vi.
        Chỉ áp dụng lũy tiến cho các hành vi bị trừ điểm (trọng số âm):
            multiplier = min(2.5, 1.0 + (duration / 20.0))
        Đối với hành vi cộng điểm: multiplier = 1.0.

        :param behavior_state: Trạng thái hành vi.
        :param duration_counter: Số giây hành vi diễn ra liên tục.
        :return: Hệ số multiplier (1.0 <= multiplier <= 2.5 cho hành vi tiêu cực; 1.0 cho hành vi tích cực).
        """
        weight = BEHAVIOR_WEIGHTS.get(behavior_state, 0.0)
        safe_duration = max(0.0, float(duration_counter))

        if weight < 0.0:
            # Hành vi vi phạm: phạt tăng dần theo thời gian kéo dài
            raw_multiplier = 1.0 + (safe_duration / DURATION_SCALE_FACTOR)
            return min(MAX_PENALTY_MULTIPLIER, raw_multiplier)
        
        # Hành vi tích cực hoặc trung tính: giữ nguyên hệ số 1.0
        return 1.0

    @staticmethod
    def compute_student_score(
        previous_score: float,
        behavior_state: str,
        duration_counter: float
    ) -> Tuple[float, float, float]:
        """
        Thực hiện tính toán điểm số mới cho 1 học sinh:
        1. Lấy trọng số hành vi.
        2. Tính multiplier theo duration.
        3. Tính delta = weight * multiplier.
        4. new_score = previous_score + delta.
        5. Clamp kết quả trong [0.0, 100.0] và làm tròn 2 chữ số.

        :param previous_score: Điểm số hiện tại của học sinh (mặc định 100.0 nếu mới bắt đầu).
        :param behavior_state: Trạng thái hành vi ('attentive', 'sleeping', v.v.).
        :param duration_counter: Thời gian duy trì hành vi (giây).
        :return: Tuple (new_score, delta, multiplier).
        """
        if behavior_state not in BEHAVIOR_WEIGHTS:
            raise ValueError(
                f"Trạng thái hành vi '{behavior_state}' không hợp lệ. "
                f"Các trạng thái hợp lệ gồm: {sorted(VALID_BEHAVIOR_STATES)}"
            )

        weight = BEHAVIOR_WEIGHTS[behavior_state]
        multiplier = ConcentrationService.calculate_multiplier(behavior_state, duration_counter)
        delta = round(weight * multiplier, 2)

        raw_new_score = previous_score + delta
        clamped_score = max(MIN_SCORE, min(MAX_SCORE, raw_new_score))
        final_score = round(clamped_score, 2)

        return final_score, delta, round(multiplier, 2)

    def process_camera_ai_payload(
        self,
        classroom_id: str,
        students_payload: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Tiếp nhận và xử lý payload từ camera-ai gửi sang định kỳ (3-5 giây/lần):
        1. Kiểm tra tính hợp lệ của dữ liệu đầu vào.
        2. Đọc điểm hiện tại từ Firestore qua Repository.
        3. Áp dụng thuật toán tính điểm động.
        4. Ghi batch cập nhật live_scores và history_logs vào Firestore.
        5. Tổng hợp và trả về báo cáo kết quả.

        :param classroom_id: Mã định danh lớp học.
        :param students_payload: Danh sách dữ liệu học sinh từ camera-ai.
        :return: Dict chứa kết quả xử lý chi tiết và thống kê.
        """
        if not classroom_id or not isinstance(classroom_id, str):
            raise ValueError("classroom_id phải là chuỗi ký tự không rỗng.")

        if not students_payload or not isinstance(students_payload, list):
            raise ValueError("Payload danh sách học sinh (students) phải là một mảng không rỗng.")

        # Lấy danh sách student_id để truy vấn điểm hiện tại
        student_ids = []
        for idx, item in enumerate(students_payload):
            sid = item.get("student_id")
            if not sid:
                raise ValueError(f"Học sinh tại chỉ mục {idx} thiếu trường bắt buộc 'student_id'.")
            student_ids.append(str(sid))

        # Lấy điểm số hiện tại của các học sinh từ Firestore qua Data Access Tier
        existing_scores = self.repository.get_classroom_live_scores_map(classroom_id, student_ids)

        processed_records: List[Dict[str, Any]] = []

        for item in students_payload:
            student_id = str(item["student_id"])
            behavior_state = str(item.get("behavior_state", "")).strip().lower()
            duration_counter = float(item.get("duration_counter", 0.0))
            seat_id = item.get("seat_id")

            # Điểm bắt đầu mặc định là 100.0 nếu chưa có lịch sử điểm trước đó
            previous_score = existing_scores.get(student_id, DEFAULT_INITIAL_SCORE)

            # Tính điểm mới theo thuật toán động
            new_score, delta, multiplier = self.compute_student_score(
                previous_score=previous_score,
                behavior_state=behavior_state,
                duration_counter=duration_counter
            )

            processed_record = {
                "student_id": student_id,
                "classroom_id": classroom_id,
                "previous_score": previous_score,
                "current_score": new_score,
                "behavior_state": behavior_state,
                "duration_counter": duration_counter,
                "multiplier": multiplier,
                "delta": delta,
                "seat_id": seat_id,
            }
            processed_records.append(processed_record)

        # Lưu đồng loạt qua Firestore Batch Writes
        saved_count = self.repository.save_live_scores_batch(classroom_id, processed_records)

        # Tính toán một số thống kê lớp học phục vụ dashboard
        scores = [r["current_score"] for r in processed_records]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "success": True,
            "classroom_id": classroom_id,
            "total_students": len(processed_records),
            "saved_count": saved_count,
            "average_score": avg_score,
            "results": processed_records,
        }

    def get_student_history(self, classroom_id: str, student_id: str, limit: int = 120) -> List[Dict[str, Any]]:
        """
        Lấy danh sách log lịch sử của học sinh từ Repository phục vụ vẽ biểu đồ.
        """
        return self.repository.get_student_history_logs(classroom_id, student_id, limit)
