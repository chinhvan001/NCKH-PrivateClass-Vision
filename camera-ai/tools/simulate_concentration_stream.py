"""
Script mô phỏng Camera-AI gửi dữ liệu hành vi học sinh định kỳ 3-5 giây sang Backend.
Phục vụ kiểm thử trực tiếp hệ thống End-to-End.
"""

import random
import time
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock cv2 nếu môi trường chạy thuần client không cài đặt opencv
if "cv2" not in sys.modules:
    try:
        import cv2
    except ImportError:
        from unittest.mock import MagicMock
        sys.modules["cv2"] = MagicMock()

from src.sync.concentration_client import ConcentrationHttpClient

BEHAVIORS = [
    "attentive",
    "attentive",
    "attentive",
    "slightly_distracted",
    "looking_down",
    "using_phone",
    "sleeping",
    "away_from_seat",
    "active_participating",
]

STUDENTS = [
    {"student_id": "HS001", "seat_id": "S01"},
    {"student_id": "HS002", "seat_id": "S02"},
    {"student_id": "HS003", "seat_id": "S03"},
    {"student_id": "HS004", "seat_id": "S04"},
    {"student_id": "HS005", "seat_id": "S05"},
]


def run_simulation(classroom_id: str = "CLASS_12A1", intervals: int = 5):
    client = ConcentrationHttpClient(backend_base_url="http://127.0.0.1:5000")
    print(f"[*] Bắt đầu mô phỏng gửi dữ liệu hành vi học sinh từ Camera-AI cho lớp {classroom_id}...")

    duration_counters = {s["student_id"]: 0.0 for s in STUDENTS}
    last_behaviors = {s["student_id"]: "attentive" for s in STUDENTS}

    for step in range(1, intervals + 1):
        interval_sec = random.uniform(3.0, 5.0)
        print(f"\n--- Đợt {step}/{intervals} (chu kỳ {interval_sec:.1f}s) ---")

        students_payload = []
        for s in STUDENTS:
            sid = s["student_id"]
            # 70% giữ nguyên hành vi, 30% đổi hành vi mới
            if random.random() < 0.3:
                chosen_behavior = random.choice(BEHAVIORS)
                last_behaviors[sid] = chosen_behavior
                duration_counters[sid] = interval_sec
            else:
                chosen_behavior = last_behaviors[sid]
                duration_counters[sid] += interval_sec

            students_payload.append({
                "student_id": sid,
                "seat_id": s["seat_id"],
                "behavior_state": chosen_behavior,
                "duration_counter": round(duration_counters[sid], 1),
            })

        print("Payload gửi đi:", students_payload)
        res = client.send_concentration_payload(classroom_id, students_payload)
        if res:
            print("[+] Backend phản hồi thành công:")
            data = res.get("data", {})
            print(f"    - Điểm TB: {data.get('average_score')}")
            for r in data.get("results", []):
                print(f"    - HS {r['student_id']}: {r['behavior_state']} ({r['duration_counter']}s) -> Điểm: {r['current_score']} (Delta: {r['delta']}, Multiplier: {r['multiplier']})")
        else:
            print("[-] Gửi thất bại hoặc backend chưa bật.")

        if step < intervals:
            time.sleep(1.0)


if __name__ == "__main__":
    run_simulation()
