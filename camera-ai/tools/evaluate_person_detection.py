"""Do person detection tren anh gan nhan COCO hoac YOLO, khong luu raw frame."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detection.person_detector import PersonDetector
from src.evaluation.person_detection import BoundingBox, DetectionMetrics, combine_metrics, evaluate_boxes

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Danh gia person detector voi ground truth COCO/YOLO.")
    parser.add_argument("--images", required=True, type=Path, help="Thu muc anh SCB-Dataset.")
    parser.add_argument("--annotations", required=True, type=Path, help="COCO .json hoac thu muc label YOLO.")
    parser.add_argument("--format", choices=("auto", "coco", "yolo"), default="auto")
    parser.add_argument("--model", default="models/yolo11s.pt")
    parser.add_argument("--confidence", type=float, default=0.15)
    parser.add_argument("--match-iou", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("reports/person_detection_metrics.json"))
    return parser.parse_args()


def _box_from_xywh(x: float, y: float, width: float, height: float) -> BoundingBox:
    return BoundingBox(x, y, x + width, y + height)


def load_coco_labels(path: Path) -> dict[str, list[BoundingBox]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    person_ids = {item["id"] for item in payload.get("categories", []) if item.get("name", "").lower() == "person"}
    if not person_ids:
        raise ValueError("COCO annotation khong co category name='person'.")
    names = {item["id"]: Path(item["file_name"]).as_posix() for item in payload.get("images", [])}
    # Giu ca anh khong co person: prediction tren cac anh nay van la false positive.
    labels: dict[str, list[BoundingBox]] = {name: [] for name in names.values()}
    for annotation in payload.get("annotations", []):
        if annotation.get("category_id") in person_ids and not annotation.get("iscrowd", 0):
            x, y, width, height = annotation["bbox"]
            if width > 0 and height > 0:
                labels[names[annotation["image_id"]]].append(_box_from_xywh(x, y, width, height))
    return labels


def load_yolo_labels(images_root: Path, labels_root: Path) -> dict[str, list[BoundingBox]]:
    labels: dict[str, list[BoundingBox]] = {}
    for image_path in images_root.rglob("*"):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        relative = image_path.relative_to(images_root)
        label_path = labels_root / relative.with_suffix(".txt")
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        height, width = image.shape[:2]
        boxes: list[BoundingBox] = []
        if label_path.exists():
            for line in label_path.read_text(encoding="utf-8").splitlines():
                values = line.split()
                if len(values) < 5 or values[0] != "0":
                    continue
                _, center_x, center_y, box_width, box_height = map(float, values[:5])
                box_width *= width
                box_height *= height
                boxes.append(
                    _box_from_xywh(
                        center_x * width - box_width / 2, center_y * height - box_height / 2, box_width, box_height
                    )
                )
        labels[relative.as_posix()] = boxes
    return labels


def density_bucket(count: int) -> str:
    return "low_1_5" if count <= 5 else "medium_6_15" if count <= 15 else "crowd_16_plus"


def main() -> int:
    args = parse_args()
    label_format = (
        "coco"
        if args.format == "auto" and args.annotations.suffix.lower() == ".json"
        else ("yolo" if args.format == "auto" else args.format)
    )
    labels = (
        load_coco_labels(args.annotations)
        if label_format == "coco"
        else load_yolo_labels(args.images, args.annotations)
    )
    image_paths = {
        path.relative_to(args.images).as_posix(): path
        for path in args.images.rglob("*")
        if path.suffix.lower() in IMAGE_EXTENSIONS
    }
    missing = sorted(set(labels) - set(image_paths))
    if missing:
        raise ValueError(f"{len(missing)} anh co nhan khong tim thay trong --images; vi du: {missing[0]}")
    if not labels:
        raise ValueError("Khong co nhan person de danh gia.")

    by_angle: dict[str, list[DetectionMetrics]] = defaultdict(list)
    by_density: dict[str, list[DetectionMetrics]] = defaultdict(list)
    all_metrics: list[DetectionMetrics] = []
    with PersonDetector(model_path=args.model, min_confidence=args.confidence) as detector:
        for relative, truth in sorted(labels.items()):
            image = cv2.imread(str(image_paths[relative]))
            if image is None:
                raise ValueError(f"Khong doc duoc anh: {relative}")
            predictions = [BoundingBox(*box.bbox) for box in detector.detect(image)]
            metric = evaluate_boxes(predictions, truth, args.match_iou)
            all_metrics.append(metric)
            by_angle[Path(relative).parent.as_posix() or "root"].append(metric)
            by_density[density_bucket(len(truth))].append(metric)
            del image, predictions

    def serialize(items: list[DetectionMetrics]) -> dict[str, float | int]:
        result = combine_metrics(items)
        return {
            "images": len(items),
            "tp": result.true_positive,
            "fp": result.false_positive,
            "fn": result.false_negative,
            "precision": round(result.precision, 4),
            "recall_detection_success": round(result.recall, 4),
            "f1": round(result.f1, 4),
        }

    report = {
        "dataset_images": len(all_metrics),
        "ground_truth_format": label_format,
        "model": Path(args.model).name,
        "confidence": args.confidence,
        "match_iou": args.match_iou,
        "overall": serialize(all_metrics),
        "by_camera_angle": {name: serialize(items) for name, items in sorted(by_angle.items())},
        "by_density": {name: serialize(items) for name, items in sorted(by_density.items())},
        "privacy": "Chi luu metric tong hop; khong luu raw frame, preview, bbox hay biometric identifier.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    overall = report["overall"]
    print(
        f"Images={overall['images']} | precision={overall['precision']:.2%} | "
        f"recall={overall['recall_detection_success']:.2%} | F1={overall['f1']:.2%}"
    )
    print(f"Bao cao metric an danh: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
