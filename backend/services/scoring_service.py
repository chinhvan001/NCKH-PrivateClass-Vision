"""Service tính điểm tập trung và trạng thái ghế từ window 10 s của camera AI (edge-data/sessions/{s}/windows.jsonl)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

# Tới khi chuyển hẳn (tuần 4, camera-ai/docs/plan_to_2026-12-13.md), điểm backend tính ghi vào hai file bóng trong
# thư mục của tiết để so với result.json/evaluations.json của camera AI; khi chuyển thì đổi sang hai file đó.
RESULTS = "shadow_result.json"
EVALUATIONS = "shadow_evaluations.json"
SLUMP_CREDIT = 0.5
AWAY_THRESHOLD_SEC = 30.0
BEHAVIOUR_HOLD_SEC = 5.0


def compute_score_from_durations(n: float, s: float, h: float, slump_credit: float = SLUMP_CREDIT) -> int | None:
    total = n + s + h
    if total <= 0:
        return None
    score = 100.0 * (n + slump_credit * s) / total
    return max(0, min(100, round(score)))


def compute_session_scores(windows: list[dict]) -> tuple[dict | None, dict[str, dict]]:
    if not windows:
        return None, {}

    # Theo thời điểm ghi: run là mã ngẫu nhiên mỗi lần camera AI chạy lại, sắp theo run có thể đặt run cũ sau run mới
    earliest = datetime.min.replace(tzinfo=timezone.utc)
    sorted_windows = sorted(windows, key=lambda w: (w.get("captured_at") or earliest, w.get("seq", 0)))
    last_w = sorted_windows[-1]
    session_id, camera_id = last_w.get("session_id"), last_w.get("camera_id")
    latest_captured_at = last_w.get("captured_at")
    latest_monitoring_status = last_w.get("monitoring_status", "running")
    latest_run = last_w.get("run")

    latest_run_end_sec = max((float(w.get("end_sec", 0.0)) for w in sorted_windows if w.get("run") == latest_run), default=0.0)

    seat_totals = defaultdict(lambda: {"normal": 0.0, "slumping": 0.0, "head_drop": 0.0})
    seat_last_seen, seat_last_state, seat_last_beh, seat_alerts = {}, {}, {}, defaultdict(Counter)

    run_windows = [w for w in sorted_windows if w.get("run") == latest_run]
    recent_windows = run_windows[-6:] if len(run_windows) >= 6 else run_windows
    recent_totals = defaultdict(lambda: {"normal": 0.0, "slumping": 0.0, "head_drop": 0.0})

    for w in sorted_windows:
        for seat_id, s_data in w.get("seats", {}).items():
            n, s, h = float(s_data.get("normal_sec", 0)), float(s_data.get("slumping_sec", 0)), float(s_data.get("head_drop_sec", 0))
            seat_totals[seat_id]["normal"] += n
            seat_totals[seat_id]["slumping"] += s
            seat_totals[seat_id]["head_drop"] += h
            seat_last_seen[seat_id] = float(s_data.get("last_seen_sec", seat_last_seen.get(seat_id, 0)))
            seat_last_state[seat_id] = s_data.get("last_state", "normal")
            if s_data.get("last_behaviour_sec") is not None:
                seat_last_beh[seat_id] = float(s_data["last_behaviour_sec"])
            for a_type, count in s_data.get("alerts", {}).items():
                seat_alerts[seat_id][a_type] += int(count)

    for w in recent_windows:
        for seat_id, s_data in w.get("seats", {}).items():
            recent_totals[seat_id]["normal"] += float(s_data.get("normal_sec", 0))
            recent_totals[seat_id]["slumping"] += float(s_data.get("slumping_sec", 0))
            recent_totals[seat_id]["head_drop"] += float(s_data.get("head_drop_sec", 0))

    all_seats = set(seat_totals.keys()) | set(seat_last_seen.keys())
    result_map, evaluations = {}, {}

    for seat_id in sorted(all_seats):
        totals = seat_totals[seat_id]
        obs_sec = round(totals["normal"] + totals["slumping"] + totals["head_drop"])
        avg_conc = compute_score_from_durations(totals["normal"], totals["slumping"], totals["head_drop"])

        last_seen = seat_last_seen.get(seat_id, 0.0)
        last_state = seat_last_state.get(seat_id, "normal")
        last_beh = seat_last_beh.get(seat_id)
        alerts_counter = seat_alerts[seat_id]

        if latest_run_end_sec - last_seen > AWAY_THRESHOLD_SEC:
            status = "away"
        elif last_state == "head_drop":
            status = "drowsy"
        elif last_state == "slumping" or (last_beh is not None and latest_run_end_sec - last_beh <= BEHAVIOUR_HOLD_SEC):
            status = "distracted"
        else:
            status = "focused"

        rec = recent_totals[seat_id]
        concentration = None if status == "away" else compute_score_from_durations(rec["normal"], rec["slumping"], rec["head_drop"])

        result_map[seat_id] = {
            "concentration": concentration,
            "interaction": alerts_counter.get("side_conversation", 0),
            "status": status,
        }
        evaluations[seat_id] = {
            "session_id": session_id,
            "seat_id": seat_id,
            "captured_at": latest_captured_at or datetime.now(timezone.utc),
            "concentration": concentration,
            "avg_concentration": avg_conc,
            "distraction": sum(alerts_counter.values()),
            "observed_sec": obs_sec,
        }

    session_result = {
        "session_id": session_id,
        "camera_id": camera_id,
        "captured_at": latest_captured_at or datetime.now(timezone.utc),
        "monitoring_status": latest_monitoring_status,
        "result_map": result_map,
    }
    return session_result, evaluations
