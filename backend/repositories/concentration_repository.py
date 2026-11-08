"""
Data Access Tier (Repository): ConcentrationRepository
Chịu trách nhiệm trực tiếp tương tác với cơ sở dữ liệu Cloud Firestore thông qua Firebase Admin SDK.
Bao gồm:
- Đọc điểm số thời gian thực hiện tại của học sinh theo lớp học.
- Sử dụng Firestore Batch Writes để cập nhật đồng thời nhiều học sinh và ghi logs lịch sử một cách nguyên tử (atomic).
- Truy vấn lịch sử điểm số phục vụ vẽ biểu đồ tiến trình.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from firebase_admin import firestore

# Import client db từ cấu hình hệ thống
from firebase_config import db

logger = logging.getLogger("concentration.repository")

# Giới hạn an toàn của Firestore WriteBatch (Firestore cho phép tối đa 500 writes mỗi commit)
# Mỗi học sinh gồm 1 ghi live_scores và 1 tạo mới sub-collection history_logs (= 2 writes/học sinh).
# Chọn BATCH_CHUNK_STUDENTS_LIMIT = 200 học sinh (tương đương 400 operations) để đảm bảo không bao giờ vượt ngưỡng 500.
BATCH_CHUNK_STUDENTS_LIMIT = 200


class ConcentrationRepository:
    """Repository quản lý truy xuất và lưu trữ dữ liệu điểm tập trung học sinh trên Firestore."""

    def __init__(self, firestore_db: Optional[Any] = None) -> None:
        """
        Khởi tạo repository.
        :param firestore_db: Firestore Client tuỳ chọn (hữu ích cho dependency injection và unit test).
        """
        self.db = firestore_db or db

    def get_classroom_live_scores_map(self, classroom_id: str, student_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Lấy điểm số tập trung hiện tại của các học sinh trong một lớp.
        Đường dẫn: classrooms/{classroom_id}/live_scores/{student_id}

        :param classroom_id: Mã định danh lớp học.
        :param student_ids: Danh sách mã học sinh cần lấy (nếu None sẽ lấy tất cả trong lớp).
        :return: Dict ánh xạ {student_id: current_score}
        """
        scores_map: Dict[str, float] = {}
        try:
            live_scores_col = self.db.collection("classrooms").document(classroom_id).collection("live_scores")

            if student_ids and len(student_ids) <= 30:
                docs = live_scores_col.stream()
                target_ids = set(student_ids)
                for doc in docs:
                    if doc.id in target_ids:
                        data = doc.to_dict() or {}
                        score = data.get("current_score")
                        if score is not None:
                            try:
                                scores_map[doc.id] = float(score)
                            except (ValueError, TypeError):
                                pass
            else:
                docs = live_scores_col.stream()
                for doc in docs:
                    data = doc.to_dict() or {}
                    score = data.get("current_score")
                    if score is not None:
                        try:
                            scores_map[doc.id] = float(score)
                        except (ValueError, TypeError):
                            pass

            logger.info("Retrieved %d existing live scores for classroom: %s", len(scores_map), classroom_id)
            return scores_map

        except Exception as e:
            logger.error("Error fetching live scores for classroom %s: %s", classroom_id, str(e), exc_info=True)
            raise RuntimeError(f"Database error while querying classroom scores: {str(e)}") from e

    def save_live_scores_batch(
        self,
        classroom_id: str,
        student_records: List[Dict[str, Any]]
    ) -> int:
        """
        Sử dụng Firestore Batch Writes để cập nhật hàng loạt điểm real-time và tạo bản ghi lịch sử (history_logs).

        Đường dẫn lưu trữ:
        - Real-time: classrooms/{classroom_id}/live_scores/{student_id}
        - History:   classrooms/{classroom_id}/live_scores/{student_id}/history_logs/{auto_id}

        :param classroom_id: Mã lớp học.
        :param student_records: Danh sách bản ghi điểm số đã qua xử lý từ Business Logic Tier.
        :return: Tổng số học sinh đã được lưu thành công.
        """
        if not student_records:
            return 0

        total_saved = 0
        server_ts = firestore.SERVER_TIMESTAMP

        try:
            classroom_ref = self.db.collection("classrooms").document(classroom_id)
            live_scores_col = classroom_ref.collection("live_scores")

            # Chia nhỏ danh sách thành từng chunk nếu số lượng học sinh lớn
            for i in range(0, len(student_records), BATCH_CHUNK_STUDENTS_LIMIT):
                chunk = student_records[i : i + BATCH_CHUNK_STUDENTS_LIMIT]
                batch = self.db.batch()

                for record in chunk:
                    student_id = record["student_id"]
                    student_doc_ref = live_scores_col.document(student_id)

                    # 1. Cập nhật trạng thái real-time hiện tại
                    live_payload = {
                        "student_id": student_id,
                        "classroom_id": classroom_id,
                        "current_score": record["current_score"],
                        "behavior_state": record["behavior_state"],
                        "duration_counter": record["duration_counter"],
                        "multiplier": record.get("multiplier", 1.0),
                        "last_delta": record.get("delta", 0.0),
                        "updated_at": server_ts,
                    }
                    if "seat_id" in record and record["seat_id"]:
                        live_payload["seat_id"] = record["seat_id"]

                    batch.set(student_doc_ref, live_payload)

                    # 2. Ghi bản ghi vào sub-collection history_logs để vẽ biểu đồ thống kê
                    history_doc_ref = student_doc_ref.collection("history_logs").document()
                    history_payload = {
                        "score": record["current_score"],
                        "behavior_state": record["behavior_state"],
                        "duration_counter": record["duration_counter"],
                        "delta": record.get("delta", 0.0),
                        "multiplier": record.get("multiplier", 1.0),
                        "timestamp": server_ts,
                    }
                    batch.set(history_doc_ref, history_payload)

                # Commit batch nguyên tử cho chunk này
                batch.commit()
                total_saved += len(chunk)
                logger.info(
                    "Committed Firestore batch of %d students for classroom %s",
                    len(chunk),
                    classroom_id
                )

            return total_saved

        except Exception as e:
            logger.error("Error committing batch writes for classroom %s: %s", classroom_id, str(e), exc_info=True)
            raise RuntimeError(f"Database error during batch score update: {str(e)}") from e

    def get_student_history_logs(
        self,
        classroom_id: str,
        student_id: str,
        limit: int = 120
    ) -> List[Dict[str, Any]]:
        """
        Truy vấn danh sách lịch sử điểm tập trung của 1 học sinh theo thứ tự thời gian tăng dần
        phục vụ vẽ biểu đồ (Chart.js / Highcharts / Flutter Charts).

        :param classroom_id: Mã lớp học.
        :param student_id: Mã học sinh.
        :param limit: Số lượng bản ghi tối đa (mặc định 120 bản ghi ~ 6-10 phút).
        :return: Danh sách dict log lịch sử.
        """
        logs: List[Dict[str, Any]] = []
        try:
            history_col = (
                self.db.collection("classrooms")
                .document(classroom_id)
                .collection("live_scores")
                .document(student_id)
                .collection("history_logs")
                .order_by("timestamp", direction=firestore.Query.ASCENDING)
                .limit(limit)
            )

            for doc in history_col.stream():
                data = doc.to_dict() or {}
                ts = data.get("timestamp")
                ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                logs.append({
                    "id": doc.id,
                    "score": data.get("score"),
                    "behavior_state": data.get("behavior_state"),
                    "duration_counter": data.get("duration_counter"),
                    "delta": data.get("delta"),
                    "timestamp": ts_str,
                })

            return logs
        except Exception as e:
            logger.error("Error fetching history logs for student %s in classroom %s: %s", student_id, classroom_id, str(e))
            raise RuntimeError(f"Database error while querying history logs: {str(e)}") from e
