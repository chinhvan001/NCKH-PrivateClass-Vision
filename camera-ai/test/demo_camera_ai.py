"""Demo truc quan cho pipeline camera-ai.

Vi du:
    python test/demo_camera_ai.py video.mp4 --seats config/seat_grid.json

File calibration co dang:
    {"seats": [{"seat_id": "A1", "center_x": 120, "center_y": 340}]}

Nhan q hoac ESC de dung. Co the ghi ket qua bang --output annotated.mp4.
Demo khong nhan dien danh tinh; moi nguoi chi duoc gan vao mot vi tri cho ngoi.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cv2

# Cho phep chay ca tu camera-ai/ lan tu thu muc repository goc.
CAMERA_AI_ROOT = Path(__file__).resolve().parents[1]
if str(CAMERA_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(CAMERA_AI_ROOT))

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seating.seat_grid import SeatGrid
    from src.detection.pose_detector import PersonPose


# Thu tu keypoint theo COCO-Pose.
SKELETON_EDGES: Tuple[Tuple[int, int], ...] = (
    (0, 1), (0, 2), (1, 3), (2, 4),
    (0, 5), (0, 6), (5, 6),
    (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
)


@dataclass
class StudentState:
    """Trang thai hien thi va tich luy cho mot seat (hoac mot detection)."""

    smoother_head: RollingSmoother
    smoother_torso: RollingSmoother
    baseline: BaselineEstablisher
    posture: PostureMonitor
    engagement: SeatEngagementTracker


def _shoulder_midpoint(person: PersonPose) -> Optional[Tuple[float, float]]:
    left = person.get_keypoint("left_shoulder")
    right = person.get_keypoint("right_shoulder")
    if left is None and right is None:
        return None
    if left is None or left[2] < 0.3:
        return (right[0], right[1]) if right is not None and right[2] >= 0.3 else None
    if right is None or right[2] < 0.3:
        return left[0], left[1]
    return (left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0


def _assign_to_seats(
    people: Iterable[PersonPose],
    grid: SeatGrid,
    max_distance: Optional[float],
) -> Dict[str, PersonPose]:
    """Gan nearest-centroid va loai trung seat trong mot frame."""
    choices: Dict[str, Tuple[PersonPose, float]] = {}
    for person in people:
        midpoint = _shoulder_midpoint(person)
        if midpoint is None:
            continue
        seat = grid.find_nearest_seat(*midpoint)
        if seat is None:
            continue
        distance = grid.distance_to(seat, *midpoint)
        if max_distance is not None and distance > max_distance:
            continue
        current = choices.get(seat.seat_id)
        if current is None or distance < current[1]:
            choices[seat.seat_id] = person, distance
    return {seat_id: person for seat_id, (person, _) in choices.items()}


def _state_for(states: Dict[str, StudentState], key: str) -> StudentState:
    if key not in states:
        states[key] = StudentState(
            smoother_head=RollingSmoother(window_sec=3.0),
            smoother_torso=RollingSmoother(window_sec=3.0),
            baseline=BaselineEstablisher(calibration_duration_sec=5.0),
            posture=PostureMonitor(),
            engagement=SeatEngagementTracker(seat_id=key),
        )
    return states[key]


def _draw_skeleton(image, person: PersonPose, color: Tuple[int, int, int]) -> None:
    points = person.keypoints
    for first, second in SKELETON_EDGES:
        x1, y1, c1 = points[first]
        x2, y2, c2 = points[second]
        if c1 >= 0.3 and c2 >= 0.3:
            cv2.line(image, (round(x1), round(y1)), (round(x2), round(y2)), color, 2)
    for x, y, confidence in points:
        if confidence >= 0.3:
            cv2.circle(image, (round(x), round(y)), 3, color, -1)


def _put_text(image, text: str, origin: Tuple[int, int], color=(255, 255, 255), scale=0.5):
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1)


def _status_color(status: str) -> Tuple[int, int, int]:
    if status == "HEAD_DROP":
        return 0, 0, 255
    if status == "SLUMPING":
        return 0, 165, 255
    return 0, 200, 0


def process_video(args: argparse.Namespace) -> None:
    # Import sau khi parse CLI de `--help` van hoat dong tren may chua cai
    # model/inference dependencies.
    from seating.seat_grid import SeatGrid
    from src.detection.pose_detector import PoseDetector
    from src.engagement.engagement_score import SeatEngagementTracker
    from src.engagement.posture import compute_head_drop_ratio, compute_torso_vector_angle
    from src.engagement.posture_monitor import (
        BaselineEstablisher,
        PostureMonitor,
        RollingSmoother,
    )

    grid = SeatGrid.from_json_file(args.seats) if args.seats else SeatGrid(seats=[])
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise RuntimeError(f"Khong mo duoc video: {args.video}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    writer = None
    states: Dict[str, StudentState] = {}
    detector = PoseDetector(args.model, min_confidence=args.confidence)

    try:
        detector.open()
        if args.output:
            width = round(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            writer = cv2.VideoWriter(
                str(args.output),
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError(f"Khong tao duoc file output: {args.output}")

        frame_index = 0
        while True:
            ok, image = capture.read()
            if not ok:
                break
            timestamp = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if timestamp <= 0:
                timestamp = frame_index / fps
            frame_index += 1

            people = detector.detect(image)
            assigned = _assign_to_seats(people, grid, args.max_distance) if grid.seats else {}
            visible: List[Tuple[str, PersonPose]] = (
                list(assigned.items())
                if assigned
                else [(f"person-{index + 1}", person) for index, person in enumerate(people)]
            )

            for label, person in visible:
                state = _state_for(states, label)
                head = state.smoother_head.add(timestamp, compute_head_drop_ratio(person))
                torso = compute_torso_vector_angle(person)
                state.baseline.add_sample(timestamp, torso)
                deviation = (
                    None
                    if not state.baseline.is_ready or torso is None
                    else state.smoother_torso.add(
                        timestamp, torso - (state.baseline.baseline_angle or 0.0)
                    )
                )
                head_event, slump_event = state.posture.update(timestamp, head, deviation)
                state.engagement.update(timestamp, head_event, slump_event)
                status = "HEAD_DROP" if head_event else "SLUMPING" if slump_event else "NORMAL"
                color = _status_color(status)

                _draw_skeleton(image, person, color)
                x1, y1, x2, y2 = (round(value) for value in person.bbox)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                score = state.engagement.compute_score().score
                score_text = "--" if score is None else f"{score:.0f}"
                _put_text(image, f"{label} | {status} | score {score_text}", (x1, max(18, y1 - 8)), color)
                metrics = f"head={head:.2f}" if head is not None else "head=--"
                _put_text(image, metrics, (x1, min(image.shape[0] - 8, y2 + 18)), color, 0.45)

            if grid.seats:
                occupied = set(assigned)
                for seat in grid.seats:
                    color = (0, 200, 0) if seat.seat_id in occupied else (120, 120, 120)
                    cv2.circle(image, (round(seat.center_x), round(seat.center_y)), 12, color, 2)
                    _put_text(image, seat.seat_id, (round(seat.center_x) + 14, round(seat.center_y) + 5), color, 0.45)

            _put_text(image, f"people={len(people)} | frame={frame_index} | q/ESC: thoat", (10, 24))
            if writer is not None:
                writer.write(image)
            cv2.imshow("camera-ai - classroom analysis", image)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        detector.close()
        capture.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hien thi skeleton, seat va trang thai hoc sinh.")
    parser.add_argument("video", type=Path, help="Duong dan video lop hoc.")
    parser.add_argument("--seats", type=Path, help="File calibration seat grid JSON (tuy chon).")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    parser.add_argument("--confidence", type=float, default=0.35, help="Nguong confidence detection.")
    parser.add_argument("--max-distance", type=float, default=None, help="Khoang cach gan seat toi da (pixel).")
    parser.add_argument("--output", type=Path, help="Ghi video da ve overlay ra file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.video.is_file():
        print(f"Khong tim thay video: {args.video}", file=sys.stderr)
        return 2
    try:
        process_video(args)
    except ModuleNotFoundError as error:
        print(
            f"Thieu dependency '{error.name}'. Hay cai camera-ai/requirements.txt "
            "va ultralytics truoc khi chay demo.",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
