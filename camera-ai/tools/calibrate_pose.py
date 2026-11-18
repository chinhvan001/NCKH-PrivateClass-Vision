"""Hieu chinh camera AI bang SCB-Dataset va video lop hoc. Frame chi nam trong RAM; chi ghi JSON so lieu tong hop.

scb:   ty le hoc sinh co nhan SCB duoc phat hien theo imgsz/tile/conf, theo 2 tieu chi: IoU >= 0.5, va "pose dung
       duoc" (trung diem 2 vai tin cay nam trong box hoc sinh: dung cach edge node gan ghe). Kem phan bo
       head_drop_ratio theo hanh vi (gio tay / doc / viet) de chot nguong cui dau. Moi box SCB la 1 hoc sinh nhung
       khong phai ai cung duoc gan nhan: chi do duoc recall, khong do duoc precision.
video: chay detector o tan so edge (mac dinh 5 Hz) tren video: toc do GPU, do lien tuc cua tung vi tri ngoi,
       keypoint, khoang cach giua hoc sinh (nguong noi chuyen), roi chay EngagementEngine that de dem canh bao.

    python tools/calibrate_pose.py scb --dataset D:\\SCB-Dataset --output reports/calibration_scb.json
    python tools/calibrate_pose.py video --video D:\\Videos\\lop.mov --output reports/calibration_video.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detection.pose_detector import PersonPose, PoseDetector  # noqa: E402
from src.engagement.back_turn import BackTurnDetector  # noqa: E402
from src.engagement.posture import (  # noqa: E402
    MIN_KEYPOINT_CONFIDENCE,
    compute_face_visibility_score,
    compute_head_drop_ratio,
)
from src.engagement.posture_monitor import PostureThresholds  # noqa: E402
from src.engagement.side_conversation import SideConversationDetector  # noqa: E402
from src.evaluation.person_detection import BoundingBox, evaluate_boxes  # noqa: E402
from src.pipeline.alert_manager import AlertManager  # noqa: E402
from src.pipeline.engagement_pipeline import EngagementEngine  # noqa: E402
from src.privacy import wipe_image  # noqa: E402
from src.seating.seat_grid import Seat, SeatGrid  # noqa: E402

CONF_LEVELS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5)  # detector chay o muc thap nhat, loc lai theo tung muc
HEAD_LEVELS = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
# Moi box la 1 hoc sinh. Bo Discuss (box ca nhom), BlackBoard/Screen (do vat), Teacher (khong phai hoc sinh).
STUDENT_SUBSETS = {
    "SCB5-Handrise-Read-write-2024-9-17": ("hand-raising", "read", "write"),
    "SCB5-Stand-2024-9-17": ("stand",),
    "SCB5-Talk-2024-9-17": ("talk",),
}


def detector_for(model: str, spec: str) -> PoseDetector:
    """spec "960:960" = imgsz 960 + tile 960; "1280" = imgsz 1280, khong chia o."""
    size, _, tile = spec.partition(":")
    return PoseDetector(
        model,
        min_confidence=CONF_LEVELS[0],
        image_size=int(size),
        max_detections=300,
        tile_size=int(tile) if tile else None,
    )


def ok(person: PersonPose, *names: str) -> bool:
    return all((kp := person.get_keypoint(name)) is not None and kp[2] >= MIN_KEYPOINT_CONFIDENCE for name in names)


def shoulders(person: PersonPose) -> tuple[float, float, float] | None:
    """(x, y) trung diem 2 vai va do rong vai, hoac None neu vai khong tin cay (edge node khong gan ghe duoc)."""
    if not ok(person, "left_shoulder", "right_shoulder"):
        return None
    left, right = person.get_keypoint("left_shoulder"), person.get_keypoint("right_shoulder")
    return (left[0] + right[0]) / 2, (left[1] + right[1]) / 2, math.dist(left[:2], right[:2])


def quantiles(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return {
        f"p{round(q * 100)}": round(ordered[min(len(ordered) - 1, int(q * len(ordered)))], 3)
        for q in (0.1, 0.25, 0.5, 0.75, 0.9)
    }


def share(values: list[float], below: float) -> float | None:
    return round(sum(value < below for value in values) / len(values), 3) if values else None


def timed_detect(detector: PoseDetector, image) -> tuple[list[PersonPose], float]:
    if not getattr(detector, "_calibration_warm", False):
        detector.detect(image)  # lan goi dau nap CUDA kernel: khong tinh vao thoi gian
        detector._calibration_warm = True
    started = time.perf_counter()
    people = detector.detect(image)
    return people, (time.perf_counter() - started) * 1000


def kept(people: list[PersonPose], conf: float) -> list[PersonPose]:
    return [person for person in people if person.confidence >= conf]


# ----------------------------------------------------------------------------------------------------------------
# SCB-Dataset
# ----------------------------------------------------------------------------------------------------------------


def read_truth(label_path: Path, width: int, height: int, names: tuple[str, ...]) -> list[tuple[BoundingBox, str]]:
    truth = []
    for line in label_path.read_text(encoding="utf-8").splitlines() if label_path.exists() else []:
        values = line.split()
        if len(values) < 5:
            continue
        cls = int(values[0])
        cx, cy, w, h = (float(value) for value in values[1:5])
        box = BoundingBox((cx - w / 2) * width, (cy - h / 2) * height, (cx + w / 2) * width, (cy + h / 2) * height)
        truth.append((box, names[cls] if cls < len(names) else str(cls)))
    return truth


def match_usable(people: list[PersonPose], truth: list[tuple[BoundingBox, str]]) -> dict[int, PersonPose]:
    """{chi so GT: pose}: pose (conf giam dan) co trung diem vai tin cay ghep voi GT chua ghep chua diem do."""
    matched: dict[int, PersonPose] = {}
    for person in sorted(people, key=lambda item: item.confidence, reverse=True):
        mid = shoulders(person)
        if mid is None:
            continue
        inside = [
            ((box.x2 - box.x1) * (box.y2 - box.y1), index)
            for index, (box, _) in enumerate(truth)
            if index not in matched and box.x1 <= mid[0] <= box.x2 and box.y1 <= mid[1] <= box.y2
        ]
        if inside:
            matched[min(inside)[1]] = person
    return matched


def size_bucket(box: BoundingBox) -> str:
    height = box.y2 - box.y1
    return "small_lt64px" if height < 64 else "medium_64_128px" if height < 128 else "large_ge128px"


def best_head_threshold(down: list[float], up: list[float]) -> dict[str, float] | None:
    """Nguong tach "nhin xuong ban" (doc/viet) voi "ngang dau" (gio tay) tot nhat theo Youden J = TPR - FPR."""
    if not down or not up:
        return None
    best = max(
        ((share(down, level / 100) - share(up, level / 100), level / 100) for level in range(5, 151, 5)),
        key=lambda item: item[0],
    )
    return {
        "threshold": best[1],
        "youden_j": round(best[0], 3),
        "read_write_below": share(down, best[1]),
        "hand_raising_below": share(up, best[1]),
    }


def run_scb(args: argparse.Namespace) -> dict:
    rng = random.Random(args.seed)
    detectors = {spec: detector_for(args.model, spec) for spec in args.configs}
    for detector in detectors.values():
        detector.open()
    counts = {spec: {conf: Counter() for conf in CONF_LEVELS} for spec in args.configs}
    times = defaultdict(list)
    posture = {spec: defaultdict(lambda: defaultdict(list)) for spec in args.configs}
    images = 0
    for subset in args.subsets:
        names = STUDENT_SUBSETS[subset]
        paths = sorted((args.dataset / subset / "images" / "val").glob("*.jpg"))
        for path in sorted(rng.sample(paths, min(args.per_subset, len(paths)))):
            image = cv2.imread(str(path))
            if image is None:
                continue
            height, width = image.shape[:2]
            truth = read_truth(args.dataset / subset / "labels" / "val" / f"{path.stem}.txt", width, height, names)
            images += 1
            for spec, detector in detectors.items():
                people, elapsed = timed_detect(detector, image)
                times[spec].append(elapsed)
                for conf in CONF_LEVELS:
                    found = kept(people, conf)
                    usable = match_usable(found, truth)
                    counter = counts[spec][conf]
                    counter["gt"] += len(truth)
                    counter["detections"] += len(found)
                    counter["iou50"] += evaluate_boxes(
                        [BoundingBox(*p.bbox) for p in found], [b for b, _ in truth]
                    ).true_positive
                    counter["usable"] += len(usable)
                    for index, (box, _) in enumerate(truth):
                        counter[f"gt_{size_bucket(box)}"] += 1
                        counter[f"usable_{size_bucket(box)}"] += index in usable
                    if abs(conf - args.posture_conf) < 1e-9:
                        for index, person in usable.items():
                            label = posture[spec][truth[index][1]]
                            label["n"].append(1)
                            label["nose"].append(ok(person, "nose"))
                            label["hips"].append(ok(person, "left_hip", "right_hip"))
                            ratio = compute_head_drop_ratio(person)
                            if ratio is not None:
                                label["head_drop_ratio"].append(ratio)
                            visibility = compute_face_visibility_score(person)
                            if visibility is not None:
                                label["face_visibility"].append(visibility)
            wipe_image(image)
            del image

    def detection_report(spec: str) -> dict:
        report = {"ms_per_image": round(statistics.mean(times[spec]), 1), "by_confidence": {}}
        for conf, counter in counts[spec].items():
            gt = counter["gt"] or 1
            report["by_confidence"][str(conf)] = {
                "recall_iou50": round(counter["iou50"] / gt, 3),
                "recall_usable_pose": round(counter["usable"] / gt, 3),
                "detections_per_labelled_student": round(counter["detections"] / gt, 2),
                "usable_by_size": {
                    bucket: round(counter[f"usable_{bucket}"] / counter[f"gt_{bucket}"], 3)
                    for bucket in ("small_lt64px", "medium_64_128px", "large_ge128px")
                    if counter[f"gt_{bucket}"]
                },
            }
        return report

    def posture_report(spec: str) -> dict:
        labels = posture[spec]
        report = {
            label: {
                "students": len(values["n"]),
                "nose_visible": round(statistics.mean(values["nose"]), 3),
                "hips_visible": round(statistics.mean(values["hips"]), 3),
                "head_drop_ratio": quantiles(values["head_drop_ratio"]),
                "head_drop_ratio_below": {str(level): share(values["head_drop_ratio"], level) for level in HEAD_LEVELS},
                "face_visibility": quantiles(values["face_visibility"]),
            }
            for label, values in sorted(labels.items())
        }
        down = labels["read"]["head_drop_ratio"] + labels["write"]["head_drop_ratio"]
        report["best_head_threshold_read_write_vs_hand_raising"] = best_head_threshold(
            down, labels["hand-raising"]["head_drop_ratio"]
        )
        return report

    return {
        "dataset": "SCB-Dataset (SCB5), val split",
        "subsets": args.subsets,
        "images": images,
        "model": Path(args.model).name,
        "note": "Moi box SCB la 1 hoc sinh co nhan hanh vi; hoc sinh khong co nhan khong tinh: chi do recall.",
        "detection": {spec: detection_report(spec) for spec in args.configs},
        "posture_at_confidence": args.posture_conf,
        "posture": {spec: posture_report(spec) for spec in args.configs},
    }


# ----------------------------------------------------------------------------------------------------------------
# Video
# ----------------------------------------------------------------------------------------------------------------


def video_frames(path: Path, hz: float, max_seconds: float):
    """(giay, anh) o tan so ~hz nhu edge node (10 fps, suy luan moi 2 frame = 5 Hz); frame bo qua khong giai ma."""
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"Khong mo duoc video: {path.name}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 15.0
    step = max(1, round(fps / hz))
    index = 0
    try:
        while index / fps <= max_seconds:
            if index % step:
                if not capture.grab():
                    break
            else:
                read, image = capture.read()
                if not read:
                    break
                yield index / fps, image
            index += 1
    finally:
        capture.release()


def cluster_positions(frames: list[list[PersonPose]], conf: float, radius: float) -> list[tuple[float, float, float]]:
    """Gom trung diem vai qua cac frame thanh vi tri ngoi: [(x, y, ty le frame co nguoi o do)]."""
    clusters: list[list] = []  # [tong x, tong y, so diem, tap frame]
    for frame_index, people in enumerate(frames):
        for person in kept(people, conf):
            mid = shoulders(person)
            if mid is None:
                continue
            nearest = min(clusters, key=lambda c: math.dist((c[0] / c[2], c[1] / c[2]), mid[:2]), default=None)
            if nearest is not None and math.dist((nearest[0] / nearest[2], nearest[1] / nearest[2]), mid[:2]) <= radius:
                nearest[0] += mid[0]
                nearest[1] += mid[1]
                nearest[2] += 1
                nearest[3].add(frame_index)
            else:
                clusters.append([mid[0], mid[1], 1, {frame_index}])
    total = max(1, len(frames))
    return [(c[0] / c[2], c[1] / c[2], len(c[3]) / total) for c in clusters]


def duplicate_pairs(people: list[PersonPose], shoulder_width: float) -> int:
    """Cap pose trong cung frame co trung diem vai cach nhau < nua do rong vai: 1 nguoi bi dem 2 lan."""
    mids = [mid[:2] for person in people if (mid := shoulders(person))]
    return sum(math.dist(a, b) < shoulder_width / 2 for i, a in enumerate(mids) for b in mids[i + 1 :])


def merge_positions(groups: list[list[tuple[float, float]]], radius: float) -> list[tuple[float, float]]:
    merged: list[tuple[float, float]] = []
    for group in groups:
        for point in group:
            if all(math.dist(point, other) > radius for other in merged):
                merged.append(point)
    return merged


def seats_from(positions: list[tuple[float, float]], shoulder_width: float) -> SeatGrid:
    """O ghe gia lap quanh moi vi tri on dinh (thay o admin ve tren web): nua canh = nua khoang cach ghe gan nhat."""
    seats = []
    for index, (x, y) in enumerate(sorted(positions, key=lambda p: (round(p[1] / shoulder_width), p[0]))):
        nearest = min((math.dist((x, y), other) for other in positions if other != (x, y)), default=2 * shoulder_width)
        half = min(nearest / 2, 1.5 * shoulder_width)
        seats.append(Seat(f"S{index + 1:02d}", x, y, (x - half, y - half, x + half, y + half)))
    return SeatGrid(seats)


def run_engine(
    frames: list[tuple[float, list[PersonPose]]],
    grid: SeatGrid,
    conf: float,
    head_threshold: float,
    conversation_px: float,
) -> dict:
    engine = EngagementEngine(
        grid,
        posture_thresholds=PostureThresholds(head_drop_ratio_threshold=head_threshold),
        back_turn_detector=BackTurnDetector(),
        side_conversation_detector=SideConversationDetector(max_pair_distance=conversation_px),
    )
    alerts = AlertManager("calibration")
    alert_counts = Counter()
    timeline = []  # "phut:giay ghe loai" de doi chieu voi video
    seconds = Counter()
    for timestamp, people in frames:
        result = engine.process(timestamp, kept(people, conf))
        for alert in alerts.update(timestamp, result.alert_candidates):
            alert_counts[alert.type] += 1
            timeline.append(f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d} {alert.seat_id} {alert.type}")
    end = frames[-1][0] if frames else 0.0
    for window in engine.take_window(end):
        seconds.update(window.seconds)
    total = sum(seconds.values()) or 1
    return {
        "head_drop_ratio_threshold": head_threshold,
        "conversation_max_distance_px": conversation_px,
        "alerts": dict(sorted(alert_counts.items())),
        "alert_timeline": timeline,
        "posture_time_share": {
            state: round(seconds[state] / total, 3) for state in ("normal", "slumping", "head_drop")
        },
        "seat_status_at_end": dict(Counter(state.status for state in engine.seat_states(end))),
    }


def run_video(args: argparse.Namespace) -> dict:
    detectors = {spec: detector_for(args.model, spec) for spec in args.configs}
    for detector in detectors.values():
        detector.open()
    frames: dict[str, list[tuple[float, list[PersonPose]]]] = defaultdict(list)
    times = defaultdict(list)
    size = None
    for timestamp, image in video_frames(args.video, args.hz, args.max_seconds):
        size = image.shape[1::-1]
        for spec, detector in detectors.items():
            people, elapsed = timed_detect(detector, image)
            frames[spec].append((timestamp, people))
            times[spec].append(elapsed)
        wipe_image(image)
        del image

    widths = [
        mid[2]
        for spec in args.configs
        for _, people in frames[spec]
        for p in kept(people, args.pose_conf)
        if (mid := shoulders(p))
    ]
    shoulder_width = statistics.median(widths) if widths else 40.0
    radius = 0.6 * shoulder_width
    positions = {
        spec: {conf: cluster_positions([people for _, people in frames[spec]], conf, radius) for conf in CONF_LEVELS}
        for spec in args.configs
    }
    stable = {
        spec: {conf: [(x, y) for x, y, seen in items if seen >= 0.5] for conf, items in by_conf.items()}
        for spec, by_conf in positions.items()
    }
    # Vi tri tham chieu: hop cac vi tri on dinh cua moi cau hinh o nguong dang dung (khong co ground truth cho video)
    reference = merge_positions([stable[spec][args.pose_conf] for spec in args.configs], radius)
    neighbour = [min(math.dist(p, q) for q in reference if q != p) for p in reference] if len(reference) > 1 else []

    def config_report(spec: str) -> dict:
        report = {
            "ms_per_frame": quantiles(times[spec]),
            "max_inference_hz": round(1000 / statistics.mean(times[spec]), 1),
            "by_confidence": {},
        }
        for conf in CONF_LEVELS:
            counts = [len(kept(people, conf)) for _, people in frames[spec]]
            usable = [p for _, people in frames[spec] for p in kept(people, conf) if shoulders(p)]
            ratios = [r for p in usable if (r := compute_head_drop_ratio(p)) is not None]
            covered = sum(any(math.dist(ref, own) <= radius for own in stable[spec][conf]) for ref in reference)
            duplicates = [duplicate_pairs(kept(people, conf), shoulder_width) for _, people in frames[spec]]
            report["by_confidence"][str(conf)] = {
                "people_per_frame": quantiles(counts),
                "stable_positions": len(stable[spec][conf]),
                "duplicate_pairs_per_frame": round(statistics.mean(duplicates), 2) if duplicates else None,
                "reference_positions_covered": round(covered / len(reference), 3) if reference else None,
                "mean_presence_of_stable_positions": (
                    round(statistics.mean(seen for _, _, seen in positions[spec][conf] if seen >= 0.5), 3)
                    if stable[spec][conf]
                    else None
                ),
                "nose_visible": round(statistics.mean(ok(p, "nose") for p in usable), 3) if usable else None,
                "hips_visible": (
                    round(statistics.mean(ok(p, "left_hip", "right_hip") for p in usable), 3) if usable else None
                ),
                "head_drop_ratio": quantiles(ratios),
                "head_drop_ratio_below": {str(level): share(ratios, level) for level in HEAD_LEVELS},
            }
        return report

    first = frames[args.configs[0]]
    grid = seats_from(reference, shoulder_width) if reference else None
    return {
        "video": args.video.name,
        "frame_size": size,
        "inference_hz": args.hz,
        "frames": len(first),
        "seconds": round(first[-1][0], 1) if first else 0,
        "model": Path(args.model).name,
        "median_shoulder_width_px": round(shoulder_width, 1),
        "reference_positions": len(reference),
        "neighbour_distance_px": quantiles(neighbour),
        "neighbour_distance_in_shoulder_widths": quantiles([d / shoulder_width for d in neighbour]),
        "configs": {spec: config_report(spec) for spec in args.configs},
        "engine": {
            "pose_confidence": args.pose_conf,
            "seats": len(reference),
            "runs": (
                {
                    spec: [
                        run_engine(frames[spec], grid, args.pose_conf, head, px)
                        for head in args.head_thresholds
                        for px in args.conversation_px
                    ]
                    for spec in args.configs
                }
                if grid
                else {}
            ),
        },
        "note": "Khong co ground truth cho video: vi tri tham chieu la hop cac vi tri on dinh cua moi cau hinh.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hieu chinh camera AI bang SCB-Dataset va video lop hoc.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scb", "video"):
        command = sub.add_parser(name)
        command.add_argument("--model", default="models/yolov8n-pose.pt")
        command.add_argument("--configs", nargs="+", default=["640", "960", "1280", "960:960"], help="imgsz[:tile]")
        command.add_argument("--output", type=Path, required=True)
    scb = sub.choices["scb"]
    scb.add_argument("--dataset", type=Path, required=True)
    scb.add_argument("--subsets", nargs="+", default=list(STUDENT_SUBSETS), choices=list(STUDENT_SUBSETS))
    scb.add_argument("--per-subset", type=int, default=300)
    scb.add_argument("--seed", type=int, default=0)
    scb.add_argument("--posture-conf", type=float, default=0.2, choices=CONF_LEVELS)
    video = sub.choices["video"]
    video.add_argument("--video", type=Path, required=True)
    video.add_argument("--hz", type=float, default=5.0)
    video.add_argument("--max-seconds", type=float, default=3600.0)
    video.add_argument("--pose-conf", type=float, default=0.2, choices=CONF_LEVELS)
    video.add_argument("--head-thresholds", nargs="+", type=float, default=[0.4])
    video.add_argument("--conversation-px", nargs="+", type=float, default=[260.0])
    args = parser.parse_args()
    report = run_scb(args) if args.command == "scb" else run_video(args)
    report["privacy"] = "Chi so lieu tong hop: khong frame, preview, toa do hay keypoint cua tung nguoi."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
