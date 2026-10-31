"""Test generator video minh hoa khong dung du lieu nguoi that."""

import json

import cv2

from tools.generate_synthetic_classroom import generate_video


def test_generator_creates_video_seats_and_scenario_labels(tmp_path):
    video = tmp_path / "classroom.mp4"
    seats = tmp_path / "seats.json"
    labels = tmp_path / "labels.jsonl"
    generate_video(video, seats, labels, width=320, height=240, fps=5, duration_sec=2, rows=2, columns=2)

    capture = cv2.VideoCapture(str(video))
    try:
        assert capture.isOpened()
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 10
    finally:
        capture.release()
    assert len(json.loads(seats.read_text(encoding="utf-8"))["seats"]) == 4
    records = [json.loads(line) for line in labels.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 10
    assert {record["scenario"] for record in records} == {"normal"}
