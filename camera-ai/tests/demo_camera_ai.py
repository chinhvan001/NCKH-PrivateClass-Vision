"""Demo truc quan cho pipeline camera-ai.

Vi du:
    python tests/demo_camera_ai.py video.mp4 --seats config/seat_grid.json

File calibration co dang:
    {"seats": [{"seat_id": "A1", "center_x": 120, "center_y": 340}]}

Nhan q hoac ESC de dung. Co the ghi ket qua bang --output "./annotated.mp4" --allow-persistent-output
Demo khong nhan dien danh tinh; moi nguoi chi duoc gan vao mot vi tri cho ngoi.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

import cv2

# Cho phep chay ca tu camera-ai/ lan tu thu muc repository goc.
CAMERA_AI_ROOT = Path(__file__).resolve().parents[1]
if str(CAMERA_AI_ROOT) not in sys.path:
    sys.path.insert(0, str(CAMERA_AI_ROOT))

from typing import TYPE_CHECKING

from src.detection.pose_detector import PoseDetector
from src.detection.person_detector import PersonBox, PersonDetector
from src.engagement.side_conversation import SideConversationDetector, SideConversationEvent
from src.engagement.back_turn import BackTurnDetector, BackTurnEvent
from src.pipeline import EngagementEngine
from src.seating.seat_grid import SeatGrid
from src.privacy import anonymize_preview, append_anonymized_record, wipe_image

if TYPE_CHECKING:
    from src.detection.pose_detector import PersonPose


# Thu tu keypoint theo COCO-Pose.
SKELETON_EDGES: Tuple[Tuple[int, int], ...] = (
    (0, 1),
    (0, 2),
    (1, 3),
    (2, 4),
    (0, 5),
    (0, 6),
    (5, 6),
    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),
    (5, 11),
    (6, 12),
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
)


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


def _draw_person_coverage(image, people: Iterable[PersonBox]) -> None:
    """Ve box coverage; box nay khong co pose nen khong tinh engagement."""
    for person in people:
        x1, y1, x2, y2 = (round(value) for value in person.bbox)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 1)


def _put_text(image, text: str, origin: Tuple[int, int], color=(255, 255, 255), scale=0.5):
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1)


def _status_color(status: str) -> Tuple[int, int, int]:
    if status == "HEAD_DROP":
        return 0, 0, 255
    if status == "SLUMPING":
        return 0, 165, 255
    return 0, 200, 0


def _draw_side_conversation(image, events: Iterable[SideConversationEvent], assigned: Dict[str, PersonPose]) -> None:
    """Ve canh bao quan sat cho cap quay ve phia nhau (khong ket luan co loi noi)."""
    for event in events:
        first, second = assigned.get(event.first_seat_id), assigned.get(event.second_seat_id)
        if first is None or second is None:
            continue
        first_x = round((first.bbox[0] + first.bbox[2]) / 2)
        first_y = round(first.bbox[1])
        second_x = round((second.bbox[0] + second.bbox[2]) / 2)
        second_y = round(second.bbox[1])
        color = (255, 0, 255)
        cv2.line(image, (first_x, first_y), (second_x, second_y), color, 2)
        midpoint = ((first_x + second_x) // 2, max(22, (first_y + second_y) // 2 - 8))
        _put_text(
            image,
            f"CANH BAO TUONG TAC RIENG {event.first_seat_id}<->{event.second_seat_id} {event.duration_sec:.0f}s",
            midpoint,
            color,
            0.42,
        )


def _draw_back_turn(image, events: Iterable[BackTurnEvent], assigned: Dict[str, PersonPose]) -> None:
    """Hien thi canh bao mat khong huong camera; khong khang dinh quay lung."""
    for event in events:
        person = assigned.get(event.seat_id)
        if person is None:
            continue
        x1, y1, _, _ = (round(value) for value in person.bbox)
        _put_text(
            image,
            f"MAT KHONG HUONG CAMERA {event.seat_id} {event.duration_sec:.0f}s",
            (x1, max(40, y1 - 26)),
            (0, 165, 255),
            0.42,
        )


def process_video(args: argparse.Namespace) -> None:
    grid = SeatGrid.from_json_file(args.seats) if args.seats else SeatGrid(seats=[])
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise RuntimeError(f"Khong mo duoc video: {args.video}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    writer = None
    # Cung logic engagement voi pipeline headless (src/pipeline); demo chi ve.
    engine = (
        EngagementEngine(
            grid,
            max_seat_distance=args.max_distance,
            side_conversation_detector=(
                SideConversationDetector(
                    max_pair_distance=args.conversation_max_distance,
                    min_duration_sec=args.conversation_duration,
                )
                if args.detect_side_conversation
                else None
            ),
            back_turn_detector=(
                BackTurnDetector(
                    max_face_visibility=args.back_turn_max_face_visibility,
                    min_duration_sec=args.back_turn_duration,
                )
                if args.detect_turning_back
                else None
            ),
        )
        if grid.seats
        else None
    )
    detector = PoseDetector(
        args.model,
        min_confidence=args.confidence,
        image_size=args.imgsz,
        iou_threshold=args.iou,
        max_detections=args.max_detections,
        tile_size=args.tile_size,
        tile_overlap=args.tile_overlap,
    )
    person_detector = PersonDetector(
        args.person_model,
        min_confidence=args.person_confidence,
        image_size=args.imgsz,
        iou_threshold=args.person_iou,
        max_detections=args.max_detections,
    )

    try:
        detector.open()
        person_detector.open()
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
            person_boxes = person_detector.detect(image)
            # Tu day tro di image chi duoc dung cho preview/debug; inference da
            # xong tren pixel goc trong RAM. An danh ca mat pose duoc va mat
            # pose bo sot (pixelate toan khung) truoc bat ky output nao.
            anonymize_preview(image, people)
            result = engine.process(timestamp, people) if engine is not None else None
            observations = result.observations if result is not None else []
            conversation_events = result.side_conversation_events if result is not None else []
            back_turn_events = result.back_turn_events if result is not None else []
            assigned = {observation.seat_id: observation.person for observation in observations}
            if engine is None:
                # Chua co --seats: chi ve skeleton, khong cham diem (khong co seat_id on dinh).
                for person in people:
                    _draw_skeleton(image, person, (200, 200, 200))

            for observation in observations:
                record = observation.record
                status = record.posture_state.upper()
                color = _status_color(status)
                person = observation.person

                _draw_skeleton(image, person, color)
                x1, y1, x2, y2 = (round(value) for value in person.bbox)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                score_text = "--" if record.engagement_score is None else f"{record.engagement_score:.0f}"
                _put_text(image, f"{observation.seat_id} | {status} | score {score_text}", (x1, max(18, y1 - 8)), color)
                if args.engagement_jsonl:
                    append_anonymized_record(args.engagement_jsonl, record)
                head = observation.head_drop_ratio
                metrics = f"head={head:.2f}" if head is not None else "head=--"
                _put_text(image, metrics, (x1, min(image.shape[0] - 8, y2 + 18)), color, 0.45)

            _draw_person_coverage(image, person_boxes)

            if grid.seats:
                occupied = set(assigned)
                for seat in grid.seats:
                    color = (0, 200, 0) if seat.seat_id in occupied else (120, 120, 120)
                    cv2.circle(image, (round(seat.center_x), round(seat.center_y)), 12, color, 2)
                    _put_text(image, seat.seat_id, (round(seat.center_x) + 14, round(seat.center_y) + 5), color, 0.45)

            _draw_side_conversation(image, conversation_events, assigned)
            _draw_back_turn(image, back_turn_events, assigned)

            _put_text(
                image,
                f"people={len(person_boxes)} | pose={len(people)} | frame={frame_index} | q/ESC: thoat",
                (10, 24),
            )
            if writer is not None:
                writer.write(image)
            cv2.imshow("camera-ai - classroom analysis", image)
            key = cv2.waitKey(1) & 0xFF
            # Khong de pixel cua frame cu luu trong bien local sau khi da trich
            # xuat pose/event. (Best-effort; Python khong dam bao wipe GPU/RAM.)
            wipe_image(image)
            del image
            if key in (ord("q"), 27):
                break
    finally:
        # Neu inference/GUI nem loi giua frame, frame hien tai van phai duoc
        # wipe truoc khi thoat pipeline.
        if "image" in locals():
            wipe_image(image)
        detector.close()
        person_detector.close()
        capture.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hien thi skeleton, seat va trang thai hoc sinh.")
    parser.add_argument("video", type=Path, help="Duong dan video lop hoc.")
    parser.add_argument("--seats", type=Path, help="File calibration seat grid JSON (tuy chon).")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Model YOLOv8-pose.")
    parser.add_argument(
        "--person-model",
        default="models/yolo11s.pt",
        help="Model object-detection class person de bao phu nguoi bi che/khuat.",
    )
    parser.add_argument("--confidence", type=float, default=0.20, help="Nguong confidence detection (CCTV xa: 0.20).")
    parser.add_argument("--person-confidence", type=float, default=0.15, help="Nguong person detector (CCTV: 0.15).")
    parser.add_argument(
        "--person-iou",
        type=float,
        default=0.70,
        help="Nguong NMS person detector (0.70 giu nguoi ngoi sat nhau).",
    )
    parser.add_argument("--imgsz", type=int, default=960, help="Kich thuoc input YOLO (mac dinh 960, thay vi 640).")
    parser.add_argument("--iou", type=float, default=0.50, help="Nguong IoU cho NMS (mac dinh 0.50).")
    parser.add_argument("--max-detections", type=int, default=100, help="So nguoi toi da moi khung hinh.")
    parser.add_argument(
        "--tile-size",
        type=int,
        default=960,
        help="Chia video thanh o vuong de bat nguoi o xa (0 de tat; mac dinh 960).",
    )
    parser.add_argument("--tile-overlap", type=float, default=0.20, help="Phan giao nhau giua cac o (0-<1).")
    parser.add_argument(
        "--detect-side-conversation",
        action="store_true",
        help="Canh bao cap ghe gan nhau quay mat ve nhau lien tuc (can --seats).",
    )
    parser.add_argument(
        "--conversation-max-distance",
        type=float,
        default=260.0,
        help="Khoang cach pixel toi da cua hai ghe de xet tuong tac rieng.",
    )
    parser.add_argument(
        "--conversation-duration",
        type=float,
        default=3.0,
        help="So giay lien tuc truoc khi hien canh bao tuong tac rieng.",
    )
    parser.add_argument(
        "--detect-turning-back",
        action="store_true",
        help="Canh bao khi vai ro nhung mat khong huong camera (can --seats; camera frontal).",
    )
    parser.add_argument(
        "--back-turn-duration",
        type=float,
        default=2.0,
        help="So giay mat khong huong camera truoc khi canh bao.",
    )
    parser.add_argument(
        "--back-turn-max-face-visibility",
        type=float,
        default=0.20,
        help="Nguong confidence mat toi da de coi la khong huong camera.",
    )
    parser.add_argument("--max-distance", type=float, default=None, help="Khoang cach gan seat toi da (pixel).")
    parser.add_argument(
        "--output",
        type=Path,
        help="Ghi video overlay ra file; bi chan mac dinh vi van chua pixel camera.",
    )
    parser.add_argument(
        "--allow-persistent-output",
        action="store_true",
        help="Xac nhan chi dung cho debug duoc phep ghi video overlay chua pixel camera.",
    )
    parser.add_argument(
        "--engagement-jsonl",
        type=Path,
        help="Xuat chi so engagement an danh (seat_id, diem, su kien); khong co pixel/keypoint/bbox.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.tile_size == 0:
        args.tile_size = None
    if args.tile_size is not None and args.tile_size < 0:
        print("--tile-size phai la 0 (tat) hoac so duong.", file=sys.stderr)
        return 2
    if args.output and not args.allow_persistent_output:
        print(
            "Privacy policy chan --output vi video overlay van chua pixel camera. "
            "Chi dung --allow-persistent-output cho debug duoc phep.",
            file=sys.stderr,
        )
        return 2
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
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
