"""Tao tap de nguoi kiem duyet gan nhan person tu SCB, khong sao chep anh goc.

Nhan tao ra la *proposal*, khong phai ground truth. Chi sau khi nguoi kiem
duyet sua/chap nhan thi moi duoc dat vao ``ground_truth``.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detection.person_detector import PersonDetector

SCENES = (
    "SCB5-Discuss-2024-9-17",
    "SCB5-Talk-2024-9-17",
    "SCB5-Handrise-Read-write-2024-9-17",
    "SCB5-Stand-2024-9-17",
    "SCB5-Teacher-2024-9-17",
    "SCB5-BlackBoard-Sreen-Teacher",
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tao manifest va proposal person de duyet thu cong.")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/person_gt_review"))
    parser.add_argument("--per-scene", type=int, default=12)
    parser.add_argument("--model", default="models/yolo11s.pt")
    parser.add_argument("--seed", type=int, default=20260925)
    return parser.parse_args()


def to_yolo(box: tuple[float, float, float, float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    box_width, box_height = max(0.0, x2 - x1), max(0.0, y2 - y1)
    return (
        f"0 {(x1 + x2) / 2 / width:.8f} {(y1 + y2) / 2 / height:.8f} {box_width / width:.8f} {box_height / height:.8f}"
    )


def main() -> int:
    args = arguments()
    if args.per_scene < 2:
        raise ValueError("--per-scene phai >= 2 de co calibration va locked test.")
    randomizer = random.Random(args.seed)
    output = args.output.resolve()
    proposal_root = output / "proposals"
    manifest_path = output / "manifest.jsonl"
    rows = []
    with PersonDetector(model_path=args.model, min_confidence=0.05, image_size=960) as detector:
        for scene in SCENES:
            images_dir = args.dataset / scene / "images" / "val"
            choices = sorted(images_dir.glob("*.jpg"))
            if not choices:
                continue
            sampled = randomizer.sample(choices, min(args.per_scene, len(choices)))
            for index, image_path in enumerate(sampled):
                image = cv2.imread(str(image_path))
                if image is None:
                    continue
                height, width = image.shape[:2]
                boxes = detector.detect(image)
                relative = Path(scene) / "images" / "val" / image_path.name
                label_path = proposal_root / scene / "labels" / "val" / image_path.with_suffix(".txt").name
                label_path.parent.mkdir(parents=True, exist_ok=True)
                label_path.write_text(
                    "\n".join(to_yolo(box.bbox, width, height) for box in boxes) + ("\n" if boxes else ""),
                    encoding="utf-8",
                )
                rows.append(
                    {
                        "image": relative.as_posix(),
                        "proposal": label_path.relative_to(output).as_posix(),
                        "scene": scene,
                        "split": "calibration" if index % 3 else "locked_test",
                        "proposal_count": len(boxes),
                        "status": "needs_human_review",
                        "identity_fields": None,
                    }
                )
                del image
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"Da tao {len(rows)} proposal de duyet: {manifest_path}")
    print("Khong co anh goc nao duoc copy; proposal khong phai ground truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
