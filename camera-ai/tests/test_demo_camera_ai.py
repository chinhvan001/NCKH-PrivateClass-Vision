"""Smoke test cho demo_camera_ai.process_video: detector gia + chan GUI, khong
can model YOLO/webcam. Bao ve demo khoi lech logic voi pipeline headless."""

import json

import cv2
import numpy as np

import demo_camera_ai
from test_end_to_end_pipeline import _person


class FakePoseDetector:
    """Ca 2 seat cui dau tu frame 3. A1 tay tinh (ngu gat), A2 tay di chuyen (chep bai)."""

    def __init__(self, *args, **kwargs):
        self.calls = 0

    def open(self):
        pass

    def close(self):
        pass

    def detect(self, image_bgr):
        self.calls += 1
        head_drop = self.calls >= 3
        writing_dx = 20.0 if self.calls % 2 else -20.0
        return [_person(90.0, head_drop, wrist_dx=0.0), _person(230.0, head_drop, wrist_dx=writing_dx)]


class FakePersonDetector(FakePoseDetector):
    def detect(self, image_bgr):
        return []


def test_demo_uses_pipeline_engagement_logic(tmp_path, monkeypatch):
    video = tmp_path / "demo.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 2.0, (320, 240))
    for index in range(30):  # 15s: du cho lam muot 3s + sustained 5s mac dinh
        writer.write(np.full((240, 320, 3), index, dtype=np.uint8))
    writer.release()
    seats = tmp_path / "seats.json"
    seats.write_text(
        json.dumps(
            {
                "seats": [
                    {"seat_id": "A1", "center_x": 90, "center_y": 100},
                    {"seat_id": "A2", "center_x": 230, "center_y": 100},
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "engagement.jsonl"

    monkeypatch.setattr(demo_camera_ai, "PoseDetector", FakePoseDetector)
    monkeypatch.setattr(demo_camera_ai, "PersonDetector", FakePersonDetector)
    monkeypatch.setattr(cv2, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(cv2, "waitKey", lambda *args, **kwargs: -1)
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "sys.argv",
        ["demo_camera_ai.py", str(video), "--seats", str(seats), "--engagement-jsonl", str(output), "--tile-size", "0"],
    )

    assert demo_camera_ai.main() == 0

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    last = {record["seat_id"]: record for record in records}
    assert last["A1"]["posture_state"] == "head_drop"
    assert last["A1"]["head_drop_events"] == 1
    assert last["A2"]["posture_state"] == "normal"
    assert last["A2"]["engagement_score"] == 100.0
    allowed = {"seat_id", "observed_at_sec", "engagement_score", "posture_state", "head_drop_events", "slumping_events"}
    assert all(set(record) == allowed for record in records)
