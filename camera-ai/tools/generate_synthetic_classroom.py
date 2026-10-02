"""Sinh video lop hoc gia lap bang hinh ve, khong dung nguoi/hoc sinh that.

Video nay dung de test capture, overlay, seat mapping, luong privacy va nhan
canh bao. Day KHONG phai dataset de danh gia do chinh xac YOLO: silhouette 2D
khong co texture nguoi that va co the khong duoc model phat hien nhu CCTV.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


def seat_layout(rows: int, columns: int, width: int, height: int) -> list[dict]:
    """Tao luoi ghe phoi canh nhe: hang sau nho hon va cao hon."""
    seats = []
    for row in range(rows):
        scale = 0.65 + 0.35 * (row + 1) / rows
        y = int(height * (0.30 + 0.58 * (row + 0.5) / rows))
        usable_width = int(width * 0.78 * scale)
        left = (width - usable_width) // 2
        for column in range(columns):
            x = int(left + usable_width * (column + 0.5) / columns)
            seats.append({"seat_id": f"R{row + 1}C{column + 1}", "center_x": x, "center_y": y})
    return seats


def _draw_room(frame: np.ndarray) -> None:
    height, width = frame.shape[:2]
    frame[:] = (210, 218, 226)
    cv2.rectangle(frame, (0, 0), (width, int(height * 0.16)), (65, 95, 125), -1)
    cv2.putText(
        frame, "SYNTHETIC CLASSROOM - NO REAL PEOPLE", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1
    )
    cv2.rectangle(
        frame, (int(width * 0.34), int(height * 0.05)), (int(width * 0.66), int(height * 0.13)), (55, 75, 70), -1
    )


def _draw_desk(frame: np.ndarray, x: int, y: int, scale: float) -> None:
    desk_width, desk_height = int(76 * scale), int(25 * scale)
    cv2.rectangle(frame, (x - desk_width // 2, y), (x + desk_width // 2, y + desk_height), (70, 105, 140), -1)
    cv2.line(
        frame,
        (x - desk_width // 3, y + desk_height),
        (x - desk_width // 2, y + desk_height + int(22 * scale)),
        (45, 65, 80),
        2,
    )
    cv2.line(
        frame,
        (x + desk_width // 3, y + desk_height),
        (x + desk_width // 2, y + desk_height + int(22 * scale)),
        (45, 65, 80),
        2,
    )


def _draw_silhouette(frame: np.ndarray, x: int, y: int, scale: float, pose: str) -> None:
    """Ve nguoi khong co dac diem mat; pose: forward/talk_left/talk_right/back."""
    head_radius = max(8, int(15 * scale))
    body_width, body_height = int(38 * scale), int(48 * scale)
    head_y = y - int(36 * scale)
    color = (60, 75, 90)
    # Dau la hinh tron phang, khong co mat, toc, mau da hoac chi tiet nhan dang.
    if pose == "back":
        cv2.circle(frame, (x, head_y), head_radius, (85, 95, 105), -1)
        cv2.line(frame, (x - head_radius // 2, head_y), (x + head_radius // 2, head_y), (65, 75, 85), 2)
    else:
        offset = -head_radius // 3 if pose == "talk_left" else head_radius // 3 if pose == "talk_right" else 0
        cv2.circle(frame, (x + offset, head_y), head_radius, (135, 145, 155), -1)
    cv2.rectangle(
        frame, (x - body_width // 2, y - int(18 * scale)), (x + body_width // 2, y + body_height // 2), color, -1
    )
    cv2.line(frame, (x - body_width // 2, y), (x - int(42 * scale), y + int(18 * scale)), color, max(2, int(4 * scale)))
    cv2.line(frame, (x + body_width // 2, y), (x + int(42 * scale), y + int(18 * scale)), color, max(2, int(4 * scale)))


def scenario_for_frame(frame_index: int, fps: int) -> str:
    second = frame_index / fps
    if 3 <= second < 7:
        return "side_conversation"
    if 7 <= second < 10:
        return "turning_back"
    return "normal"


def _poses_for_scenario(seats: list[dict], scenario: str) -> dict[str, str]:
    poses = {seat["seat_id"]: "forward" for seat in seats}
    if len(seats) >= 2 and scenario == "side_conversation":
        poses[seats[0]["seat_id"]] = "talk_right"
        poses[seats[1]["seat_id"]] = "talk_left"
    if seats and scenario == "turning_back":
        poses[seats[0]["seat_id"]] = "back"
    return poses


def generate_video(
    output: Path,
    seats_path: Path,
    labels_path: Path,
    *,
    width: int = 960,
    height: int = 540,
    fps: int = 15,
    duration_sec: int = 12,
    rows: int = 3,
    columns: int = 4,
) -> None:
    if min(width, height, fps, duration_sec, rows, columns) <= 0:
        raise ValueError("Kich thuoc, FPS, thoi luong, rows va columns phai > 0.")
    output.parent.mkdir(parents=True, exist_ok=True)
    seats_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    seats = seat_layout(rows, columns, width, height)
    seats_path.write_text(json.dumps({"seats": seats}, indent=2), encoding="utf-8")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Khong tao duoc video: {output}")
    try:
        with labels_path.open("w", encoding="utf-8") as labels:
            for frame_index in range(fps * duration_sec):
                frame = np.empty((height, width, 3), dtype=np.uint8)
                _draw_room(frame)
                scenario = scenario_for_frame(frame_index, fps)
                poses = _poses_for_scenario(seats, scenario)
                for seat in seats:
                    scale = 0.65 + 0.35 * int(seat["seat_id"].split("C")[0][1:]) / rows
                    bob = round(math.sin(frame_index / fps * 2.0 + seat["center_x"]) * scale)
                    _draw_desk(frame, seat["center_x"], seat["center_y"], scale)
                    _draw_silhouette(frame, seat["center_x"], seat["center_y"] + bob, scale, poses[seat["seat_id"]])
                cv2.putText(
                    frame, f"scenario: {scenario}", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1
                )
                writer.write(frame)
                labels.write(
                    json.dumps(
                        {
                            "frame_index": frame_index,
                            "timestamp_sec": round(frame_index / fps, 3),
                            "scenario": scenario,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    finally:
        writer.release()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tao video lop hoc minh hoa, khong dung nguoi that.")
    parser.add_argument("--output", type=Path, default=Path("synthetic_classroom.mp4"))
    parser.add_argument("--seats", type=Path, default=Path("synthetic_seats.json"))
    parser.add_argument("--labels", type=Path, default=Path("synthetic_labels.jsonl"))
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--duration", type=int, default=12, help="Thoi luong video (giay).")
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--columns", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        generate_video(
            args.output,
            args.seats,
            args.labels,
            width=args.width,
            height=args.height,
            fps=args.fps,
            duration_sec=args.duration,
            rows=args.rows,
            columns=args.columns,
        )
    except (RuntimeError, ValueError) as error:
        print(error)
        return 1
    print(f"Da tao video gia lap: {args.output}")
    print(f"Da tao seat grid: {args.seats}")
    print(f"Da tao ground truth scenario: {args.labels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
