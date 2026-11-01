"""Worker tính điểm định kỳ hoặc theo yêu cầu từ session_windows (backend/jobs/scoring_worker.py)."""

from __future__ import annotations

import argparse
import time

from routes.test_helpers import commit_writes, db, server_timestamp
from services import scoring_service


def process_session_scoring(database, session_id: str) -> bool:
    windows_ref = database.collection("session_windows")
    docs = windows_ref.where("session_id", "==", session_id).stream()
    windows = [doc.to_dict() for doc in docs if doc.to_dict()]
    if not windows:
        return False

    session_result, evaluations = scoring_service.compute_session_scores(windows)
    if not session_result:
        return False

    writes = []
    res_ref = database.collection("session_results").document(session_id)
    session_result["captured_at"] = server_timestamp()
    writes.append((res_ref, session_result))

    for seat_id, eval_data in evaluations.items():
        eval_ref = database.collection("session_evaluations").document(f"{session_id}_{seat_id}")
        eval_data["captured_at"] = server_timestamp()
        writes.append((eval_ref, eval_data))

    commit_writes(writes)
    return True


def process_active_sessions(database) -> int:
    sessions_ref = database.collection("sessions")
    count = 0
    for doc in sessions_ref.where("status", "in", ["running", "paused", "completed"]).stream():
        session_id = doc.id
        try:
            if process_session_scoring(database, session_id):
                count += 1
        except Exception as e:
            print(f"Lỗi tính điểm tiết {session_id}: {e}", flush=True)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description="Worker tính điểm tập trung từ session_windows.")
    parser.add_argument("--every", type=int, default=0, metavar="GIÂY", help="lặp lại sau mỗi chừng này giây")
    parser.add_argument("--session", metavar="ID", help="tính điểm lại cho một tiết cụ thể")
    args = parser.parse_args(argv)

    if args.session:
        success = process_session_scoring(db, args.session)
        print(f"Tiết {args.session}: " + ("thành công." if success else "không có windows hoặc lỗi."))
        return

    while True:
        count = process_active_sessions(db)
        print(f"Đã cập nhật scoring cho {count} tiết từ session_windows.", flush=True)
        if args.every <= 0:
            return
        time.sleep(args.every)


if __name__ == "__main__":
    main()
