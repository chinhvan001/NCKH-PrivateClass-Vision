"""Worker tính điểm tập trung từ window 10 s của camera AI (gói A, camera-ai/docs/plan_to_2026-12-13.md).

Window nằm trong edge-data/sessions/{s}/windows.jsonl trên máy chạy cả web và camera AI (services/edge_store.py).
Tới khi chuyển hẳn (tuần 4), worker ghi vào scoring_service.RESULTS/EVALUATIONS là hai file bóng cạnh đó, để so
với result.json/evaluations.json camera AI đang ghi mà không ghi đè lên nhau. Khi chuyển: đổi hai hằng số đó và
tắt phần ghi kết quả của camera AI.

Mỗi lượt chỉ tính các tiết đang giám sát và các tiết kết thúc từ ``since`` mà kết quả chưa chốt (chưa có window
cuối completed/incomplete). Lượt đầu nhìn lại LOOKBACK_DAYS ngày (worker có thể đã tắt một thời gian), các lượt
sau RECENT_END_SEC. Firestore chỉ được hỏi danh sách tiết: ít nhất 3 lượt đọc mỗi lượt tính (~900/ngày với 300 s).

    cd backend; python -m jobs.scoring_worker --every 300
"""

from __future__ import annotations

import argparse
import time
from datetime import timedelta

from routes.test_helpers import db
from services import edge_store, monitoring_service, scoring_service

RESULTS, EVALUATIONS = scoring_service.RESULTS, scoring_service.EVALUATIONS
FINAL_STATUSES = ("completed", "incomplete")  # monitoring_status của window cuối camera AI ghi khi hết tiết
LOOKBACK_DAYS = 7
RECENT_END_SEC = 600  # window cuối tới vài giây sau khi tiết kết thúc; 10 phút cho chắc


def process_session_scoring(session_id: str) -> str | None:
    """Tính lại điểm một tiết từ mọi window của nó (chạy lại vẫn ra cùng kết quả). Trả monitoring_status
    của window cuối, None khi tiết chưa có window."""
    windows = edge_store.windows(session_id)
    if not windows:
        return None

    session_result, evaluations = scoring_service.compute_session_scores(windows)
    if not session_result:
        return None

    now = monitoring_service.utc_now()
    edge_store.write_session_file(session_id, RESULTS, {**session_result, "captured_at": now})
    edge_store.write_session_file(
        session_id, EVALUATIONS, {seat_id: {**data, "captured_at": now} for seat_id, data in evaluations.items()}
    )
    return session_result["monitoring_status"]


def process_pending_sessions(database, since) -> int:
    """Tính điểm các tiết đang giám sát, và các tiết kết thúc từ ``since`` mà kết quả chưa chốt."""
    sessions = database.collection("sessions")
    pending = [
        doc.id for status in monitoring_service.LIVE_STATUSES for doc in sessions.where("status", "==", status).stream()
    ]
    for doc in sessions.where("ended_at", ">=", since).stream():
        if (edge_store.session_file(doc.id, RESULTS) or {}).get("monitoring_status") not in FINAL_STATUSES:
            pending.append(doc.id)

    count = 0
    for session_id in dict.fromkeys(pending):
        try:
            if process_session_scoring(session_id) is not None:
                count += 1
        except Exception as e:  # một tiết lỗi không chặn các tiết khác
            print(f"Lỗi tính điểm tiết {session_id}: {e}", flush=True)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description="Worker tính điểm tập trung từ window của camera AI.")
    parser.add_argument("--every", type=int, default=0, metavar="GIÂY", help="lặp lại sau mỗi chừng này giây")
    parser.add_argument("--session", metavar="ID", help="tính điểm lại cho một tiết cụ thể")
    args = parser.parse_args(argv)

    if args.session:
        status = process_session_scoring(args.session)
        print(f"Tiết {args.session}: " + (f"đã tính ({status})." if status else "chưa có window nào."))
        return

    since = monitoring_service.utc_now() - timedelta(days=LOOKBACK_DAYS)
    while True:
        count = process_pending_sessions(db, since)
        print(f"Đã tính điểm {count} tiết từ window của camera AI.", flush=True)
        if args.every <= 0:
            return
        time.sleep(args.every)
        # tiết kết thúc giữa hai lượt vẫn được tính, kể cả khi --every dài hơn RECENT_END_SEC
        since = monitoring_service.utc_now() - timedelta(seconds=max(RECENT_END_SEC, 2 * args.every))


if __name__ == "__main__":
    main()
