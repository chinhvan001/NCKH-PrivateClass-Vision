import pytest
from repositories.concentration_repository import ConcentrationRepository


def test_repository_get_live_scores_empty(db):
    """Khi lớp học chưa có dữ liệu điểm -> trả về map rỗng."""
    repo = ConcentrationRepository(firestore_db=db)
    scores = repo.get_classroom_live_scores_map("CR_TEST_01")
    assert scores == {}


def test_repository_save_live_scores_and_history_batch(db):
    """
    Kiểm tra lưu live score và sub-collection history_logs qua Firestore Batch Writes.
    Đường dẫn:
    - classrooms/{classroom_id}/live_scores/{student_id}
    - classrooms/{classroom_id}/live_scores/{student_id}/history_logs/{auto_id}
    """
    repo = ConcentrationRepository(firestore_db=db)
    classroom_id = "CR_MATH_101"

    student_records = [
        {
            "student_id": "STUDENT_A",
            "current_score": 95.0,
            "behavior_state": "attentive",
            "duration_counter": 5.0,
            "multiplier": 1.0,
            "delta": 1.0,
            "seat_id": "S01",
        },
        {
            "student_id": "STUDENT_B",
            "current_score": 88.0,
            "behavior_state": "using_phone",
            "duration_counter": 20.0,
            "multiplier": 2.0,
            "delta": -12.0,
            "seat_id": "S02",
        },
    ]

    saved_count = repo.save_live_scores_batch(classroom_id, student_records)
    assert saved_count == 2

    # 1. Kiểm tra document live_scores
    doc_a = db.document(f"classrooms/{classroom_id}/live_scores/STUDENT_A").get().to_dict()
    assert doc_a is not None
    assert doc_a["student_id"] == "STUDENT_A"
    assert doc_a["current_score"] == 95.0
    assert doc_a["behavior_state"] == "attentive"
    assert doc_a["seat_id"] == "S01"

    doc_b = db.document(f"classrooms/{classroom_id}/live_scores/STUDENT_B").get().to_dict()
    assert doc_b is not None
    assert doc_b["student_id"] == "STUDENT_B"
    assert doc_b["current_score"] == 88.0
    assert doc_b["behavior_state"] == "using_phone"

    # 2. Kiểm tra subcollection history_logs
    history_col_a = db.collection(f"classrooms/{classroom_id}/live_scores/STUDENT_A/history_logs")
    history_docs = list(history_col_a.stream())
    assert len(history_docs) == 1
    h_data = history_docs[0].to_dict()
    assert h_data["score"] == 95.0
    assert h_data["behavior_state"] == "attentive"
    assert h_data["delta"] == 1.0

    # 3. Kiểm tra đọc lại live_scores_map
    scores_map = repo.get_classroom_live_scores_map(classroom_id)
    assert scores_map["STUDENT_A"] == 95.0
    assert scores_map["STUDENT_B"] == 88.0
