"""Cat video lop thanh clip ~2 s, moi clip 1 hoc sinh 1 hanh dong, chay nhan dien tung clip, tao trang danh gia.

Chi de nguoi danh gia xem tren may local. Clip ghi ra thu muc --output (de ngoai repo, khong commit, khong
dang len dau), can --allow-persistent-output. anonymize_preview() pixelate ca khung xuong 32x24 thi khong con
thay hanh dong, nen o day vung DAU cua moi nguoi phat hien duoc bi pixelate (tinh tu vai va keypoint dau), than
nguoi giu nguyen de danh gia tu the.

Buoc 1 (5 Hz, nhu edge node): tim vi tri ngoi on dinh, gan nhan hanh dong tung frame bang dung nguong cua he thong,
chon cac doan 2 s 1 nguoi duoc thay >= 80% frame va 1 hanh dong chiem >= 70%, chia deu theo hanh dong.
Buoc 2 (moi frame cua tung doan): chay lai detector tren khung day du (imgsz 1280 nhu edge node), nhan dien nguoi
o ghe do, ghi clip da lam mo dau va ket qua; index.html de danh dau Dung/Sai va xuat CSV.

    python tools/cut_action_clips.py --video lop.mov --output D:\\Videos\\lop_clips --allow-persistent-output
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detection.pose_detector import PersonPose  # noqa: E402
from src.engagement.back_turn import BackTurnDetector  # noqa: E402
from src.engagement.hand_activity import HandActivityMonitor  # noqa: E402
from src.engagement.posture import (  # noqa: E402
    compute_ear_eye_offset,
    compute_eye_distance_ratio,
    compute_head_drop_ratio,
    compute_head_turn_ratio,
    compute_torso_vector_angle,
)
from src.engagement.posture_monitor import (  # noqa: E402
    FrontalBaseline,
    FrontalPose,
    PostureThresholds,
    is_head_down,
    is_slumped_over,
)
from src.privacy import wipe_image  # noqa: E402
from tools.calibrate_pose import (  # noqa: E402
    cluster_positions,
    detector_for,
    kept,
    seats_from,
    shoulders,
    video_frames,
)

# Nguong va luat cua EngagementEngine (posture_monitor), khong dat lai o day: clip cham dung cai edge node chay
THRESHOLDS = PostureThresholds()
BACK_TURN = BackTurnDetector().max_face_visibility
POSE_CONF = 0.2
LABELS = {
    "binh_thuong": "Ngồi bình thường",
    "cui_dau": "Gục / cúi hẳn xuống (hệ thống: buồn ngủ)",
    "cui_dau_viet": "Cúi xuống bàn: đọc / viết (so với lúc nhìn thẳng; vừa cúi vừa quay ngang vẫn tính là cúi; "
    "hệ thống: không phải buồn ngủ)",
    "quay_dau": "Quay đầu sang bên (so với lúc nhìn thẳng của ghế)",
    "quay_lung": "Không thấy mặt (quay lưng / quay đi)",
    "nghieng_nguoi": "Nghiêng / lệch người (thân lệch > 15°, đầu không cúi)",
}
OUT_WIDTH, OUT_HEIGHT = 360, 432


def signals(person: PersonPose, torso_baseline: float | None, frontal: FrontalPose | None) -> dict:
    """Tin hieu cua 1 frame, so voi tu the nhin thang cua ghe (edge node: FrontalBaseline chay dan; o day tinh tren
    ca video cua ghe, gia tri ma FrontalBaseline hoi tu toi)."""
    turn = compute_head_turn_ratio(person)
    angle = compute_torso_vector_angle(person)
    head = compute_head_drop_ratio(person)
    return {
        "face_visibility": BackTurnDetector._face_visibility_if_shoulders_visible(person),
        "head_drop_ratio": head,
        "head_turn_ratio": None if turn is None else turn - (frontal.turn if frontal else 0.0),
        "torso_deviation": None if torso_baseline is None or angle is None else angle - torso_baseline,
        "head_down": is_head_down(head, compute_ear_eye_offset(person), frontal, THRESHOLDS),
    }


def frame_label(values: dict) -> str:
    """Hanh dong tuc thoi cua 1 frame theo dung luat cua EngagementEngine: quay lung > gục > cui xuong ban > quay dau
    > nghieng nguoi > binh thuong (cui xuong ban xet truoc quay dau: so voi moc nhin thang, quay dau khong lam ty so
    cui dau giam)."""
    if values["face_visibility"] is not None and values["face_visibility"] <= BACK_TURN:
        return "quay_lung"
    turn, deviation = values["head_turn_ratio"], values["torso_deviation"]
    if is_slumped_over(values["head_drop_ratio"], deviation, THRESHOLDS):
        return "cui_dau"
    if values["head_down"]:
        return "cui_dau_viet"
    if turn is not None and abs(turn) >= THRESHOLDS.head_turn_ratio_threshold:
        return "quay_dau"
    if deviation is not None and abs(deviation) > THRESHOLDS.torso_deviation_threshold_deg:
        return "nghieng_nguoi"
    return "binh_thuong"


def clip_label(labels: list[str]) -> tuple[str, float]:
    """Hanh dong chiem nhieu frame nhat va ty le cua no."""
    if not labels:
        return "khong_thay_nguoi", 0.0
    label, count = Counter(labels).most_common(1)[0]
    return label, count / len(labels)


def seat_person(people: list[PersonPose], seat) -> PersonPose | None:
    """Nguoi cua ghe: trung diem vai trong o ghe, gan tam nhat (nhu SeatTracker gan ghe)."""
    inside = [
        (math.dist(mid[:2], (seat.center_x, seat.center_y)), index)
        for index, person in enumerate(people)
        if (mid := shoulders(person)) and seat.contains(mid[0], mid[1])
    ]
    return people[min(inside)[1]] if inside else None


# ----------------------------------------------------------------------------------------------------------------
# Buoc 1: chon doan
# ----------------------------------------------------------------------------------------------------------------


def seat_tracks(frames, grid) -> tuple[dict, dict]:
    """{ghe: [(giay, nguoi | None)]} o 5 Hz va {ghe: (goc than thuong ngay, tu the nhin thang)}."""
    tracks = defaultdict(list)
    for timestamp, people in frames:
        for seat in grid.seats:
            tracks[seat.seat_id].append((timestamp, seat_person(people, seat)))
    bases = {}
    for seat_id, track in tracks.items():
        angles = [a for _, p in track if p and (a := compute_torso_vector_angle(p)) is not None]
        frontal = FrontalBaseline(max_samples=max(25, len(track)))
        for _, person in track:
            if person is not None:
                frontal.add(
                    compute_eye_distance_ratio(person),
                    compute_head_turn_ratio(person),
                    compute_head_drop_ratio(person),
                    compute_ear_eye_offset(person),
                )
        bases[seat_id] = (statistics.median(angles) if angles else None, frontal.value)
    return tracks, bases


def reviewed_windows(path: Path) -> list[dict]:
    """Doan da cham o lan truoc (CSV xuat tu index.html): ghe, giay bat dau, hanh dong thuc te."""
    with path.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    windows = []
    for row in rows:
        minutes, seconds = row["time"].split(":")
        windows.append(
            {
                "seat": row["seat"],
                "start": int(minutes) * 60 + float(seconds),
                "truth": row["hanh_dong_thuc_te"],
                "old_ratio": (
                    float(row["head_drop_ratio"]) if row.get("head_drop_ratio") not in (None, "", "None") else None
                ),
            }
        )
    return windows


def candidate_windows(tracks, bases, args, exclude: list[dict]) -> list[dict]:
    """Nhieu doan nhat co the: truot tung --step giay, lay doan 2 s dau tien hop le (thay nguoi >= --min-seen, 1 hanh
    dong >= --min-share), cac doan cung ghe khong chong nhau va khong chong doan da cham."""
    windows = []
    for seat_id, track in tracks.items():
        done = [w["start"] for w in exclude if w["seat"] == seat_id]
        end, start = track[-1][0], 0.0
        while start + args.seconds <= end:
            if any(abs(start - other) < args.seconds for other in done):
                start = round(start + args.step, 2)
                continue
            inside = [(t, p) for t, p in track if start <= t < start + args.seconds]
            seen = [p for _, p in inside if p is not None]
            if inside and len(seen) / len(inside) >= args.min_seen:
                label, share = clip_label([frame_label(signals(p, *bases[seat_id])) for p in seen])
                if share >= args.min_share:
                    windows.append({"seat": seat_id, "start": round(start, 2), "label": label})
                    start = round(start + args.seconds, 2)
                    continue
            start = round(start + args.step, 2)
    return windows


def pick(windows: list[dict], total: int, seed: int) -> list[dict]:
    """total <= 0: lay het. Con lai chia deu cho cac hanh dong; hanh dong hiem lay het, phan con lai cho hanh dong
    nhieu."""
    if total <= 0:
        return sorted(windows, key=lambda w: (w["start"], w["seat"]))
    rng = random.Random(seed)
    groups = defaultdict(list)
    for window in windows:
        groups[window["label"]].append(window)
    for items in groups.values():
        rng.shuffle(items)
    chosen, remaining = [], total
    for index, (label, items) in enumerate(sorted(groups.items(), key=lambda item: len(item[1]))):
        quota = math.ceil(remaining / (len(groups) - index))
        chosen += items[:quota]
        remaining -= min(quota, len(items))
    return sorted(chosen, key=lambda w: (w["start"], w["seat"]))


# ----------------------------------------------------------------------------------------------------------------
# Buoc 2: cat clip va nhan dien tung clip
# ----------------------------------------------------------------------------------------------------------------


class ClipWriter:
    """Ghi H.264 qua ffmpeg (stdin): trinh duyet phat duoc, khong co file trung gian chua frame goc."""

    def __init__(self, ffmpeg: str, path: Path, fps: float) -> None:
        command = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24"]
        command += ["-s", f"{OUT_WIDTH}x{OUT_HEIGHT}", "-r", f"{fps:.3f}", "-i", "-", "-c:v", "libx264"]
        command += ["-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
        self._process = subprocess.Popen(command, stdin=subprocess.PIPE)

    def write(self, image) -> None:
        self._process.stdin.write(image.tobytes())

    def close(self) -> None:
        self._process.stdin.close()
        if self._process.wait():
            raise RuntimeError("ffmpeg loi khi ghi clip.")


def head_box(person: PersonPose) -> tuple[int, int, int, int]:
    """O vuong phu ca dau, ke ca khi mat quay di (tam tu keypoint dau, hoac tren vai)."""
    head = [kp for kp in person.keypoints[:5] if kp[2] >= 0.2]
    mid = shoulders(person)
    x1, y1, x2, y2 = person.bbox
    size = mid[2] if mid else (x2 - x1) * 0.5
    if head:
        cx, cy = statistics.mean(kp[0] for kp in head), statistics.mean(kp[1] for kp in head)
    elif mid:
        cx, cy = mid[0], mid[1] - 0.7 * size
    else:
        cx, cy = (x1 + x2) / 2, y1 + 0.15 * (y2 - y1)
    half = max(20.0, 0.75 * size)
    return int(cx - half), int(cy - half), int(cx + half), int(cy + half)


SKELETON = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (0, 5), (0, 6)]


def render(image, crop, everyone: list[PersonPose], target: PersonPose | None, blur: bool = True):
    x1, y1, x2, y2 = crop
    view = image[y1:y2, x1:x2].copy()
    for person in everyone if blur else ():  # lam mo dau moi nguoi phat hien duoc, khong chi nguoi cua clip
        hx1, hy1, hx2, hy2 = head_box(person)
        hx1, hy1, hx2, hy2 = max(0, hx1 - x1), max(0, hy1 - y1), min(x2 - x1, hx2 - x1), min(y2 - y1, hy2 - y1)
        if hx2 - hx1 > 2 and hy2 - hy1 > 2:
            roi = view[hy1:hy2, hx1:hx2]
            small = cv2.resize(roi, (5, 5), interpolation=cv2.INTER_AREA)
            roi[:] = cv2.resize(small, (hx2 - hx1, hy2 - hy1), interpolation=cv2.INTER_NEAREST)
    if target is not None:
        points = [(int(x - x1), int(y - y1), c) for x, y, c in target.keypoints]
        for a, b in SKELETON:
            if points[a][2] >= 0.3 and points[b][2] >= 0.3:
                cv2.line(view, points[a][:2], points[b][:2], (0, 220, 255), 2, cv2.LINE_AA)
        for index in (5, 6, 7, 8, 9, 10, 11, 12):
            if points[index][2] >= 0.3:
                cv2.circle(view, points[index][:2], 4, (0, 255, 0), -1, cv2.LINE_AA)
    out = cv2.resize(view, (OUT_WIDTH, OUT_HEIGHT), interpolation=cv2.INTER_AREA)
    wipe_image(view)
    return out


def crop_for(seat, shoulder_width: float, frame_size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = int(3.0 * shoulder_width), int(3.6 * shoulder_width)
    x1 = int(min(max(0, seat.center_x - width / 2), frame_size[0] - width))
    y1 = int(min(max(0, seat.center_y - 0.4 * height), frame_size[1] - height))
    return x1, y1, x1 + width, y1 + height


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 3) if values else None


def cut_and_recognise(args, clips, grid, shoulder_width, bases, ffmpeg=None) -> list[dict]:
    """Nhan dien lai tung frame cua moi doan (15 fps, khung day du nhu edge node). ffmpeg=None: chi cham, khong
    ghi clip (cham lai cac doan da danh gia)."""
    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS) or 15.0
    size = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    seats = {seat.seat_id: seat for seat in grid.seats}
    for number, clip in enumerate(clips, 1):
        clip["id"] = f"{number:03d}"
        clip["file"] = (
            f"clips/{clip['id']}_{clip['seat']}_{int(clip['start'] // 60):02d}m{int(clip['start'] % 60):02d}s.mp4"
        )
        clip["first"], clip["last"] = round(clip["start"] * fps), round((clip["start"] + args.seconds) * fps)
        clip["crop"] = crop_for(seats[clip["seat"]], shoulder_width, size)
        clip["state"] = {
            "labels": [],
            "values": defaultdict(list),
            "conf": [],
            "frames": 0,
            "hands": HandActivityMonitor(),
        }
    if ffmpeg:
        (args.output / "clips").mkdir(parents=True, exist_ok=True)
    detector = detector_for(args.model, str(args.image_size))
    detector.open()
    writers, index, last = {}, 0, max(clip["last"] for clip in clips)
    try:
        while index < last:
            active = [clip for clip in clips if clip["first"] <= index < clip["last"]]
            if not active:
                capture.grab()
                index += 1
                continue
            read, image = capture.read()
            if not read:
                break
            everyone = detector.detect(image)
            people = kept(everyone, POSE_CONF)
            for clip in active:
                state = clip["state"]
                target = seat_person(people, seats[clip["seat"]])
                state["frames"] += 1
                if target is not None:
                    values = signals(target, *bases[clip["seat"]])
                    state["labels"].append(frame_label(values))
                    for key, value in values.items():
                        if value is not None:
                            state["values"][key].append(value)
                    state["conf"].append(target.confidence)
                    state["hands_active"] = state["hands"].update(index / fps, target)
                if not ffmpeg:
                    continue
                if clip["id"] not in writers:
                    writers[clip["id"]] = ClipWriter(ffmpeg, args.output / clip["file"], fps)
                writers[clip["id"]].write(render(image, clip["crop"], everyone, target, not args.no_face_blur))
                if index + 1 == clip["last"]:
                    writers.pop(clip["id"]).close()
            wipe_image(image)
            del image
            index += 1
    finally:
        capture.release()
        for writer in writers.values():
            writer.close()
    results = []
    for clip in clips:
        state = clip["state"]
        hands = state.get("hands_active")
        label, share = clip_label(state["labels"])
        results.append(
            {
                "id": clip["id"],
                "file": clip["file"],
                "seat": clip["seat"],
                "time": f"{int(clip['start'] // 60):02d}:{clip['start'] % 60:04.1f}",
                "predicted": label,
                "predicted_text": LABELS.get(label, "Không thấy người ở ghế"),
                "label_share": round(share, 2),
                "frames_with_person": f"{len(state['labels'])}/{state['frames']}",
                "pose_confidence": median(state["conf"]),
                "hands_active": hands,
                "head_drop_ratio": median(state["values"]["head_drop_ratio"]),
                "face_visibility": median(state["values"]["face_visibility"]),
                "head_turn_ratio": median(state["values"]["head_turn_ratio"]),
                "torso_deviation_deg": median(state["values"]["torso_deviation"]),
                "frame_labels": dict(Counter(state["labels"])),
                **({"truth": clip["truth"]} if "truth" in clip else {}),
            }
        )
    return results


def write_review(output: Path, results: list[dict], meta: dict) -> None:
    columns = ["id", "file", "seat", "time", "predicted", "predicted_text", "label_share", "frames_with_person"]
    columns += ["pose_confidence", "hands_active", "head_drop_ratio", "face_visibility", "head_turn_ratio"]
    columns += ["torso_deviation_deg"]
    with (output / "results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns + ["danh_gia (dung/sai)", "hanh_dong_thuc_te", "ghi_chu"])
        for row in results:
            writer.writerow([row[column] for column in columns] + ["", "", ""])
    (output / "results.json").write_text(
        json.dumps({"meta": meta, "clips": results}, ensure_ascii=False, indent=1), "utf-8"
    )
    page = (Path(__file__).with_name("clip_review_template.html")).read_text(encoding="utf-8")
    payload = json.dumps({"meta": meta, "labels": LABELS, "clips": results}, ensure_ascii=False).replace("</", "<\\/")
    (output / "index.html").write_text(page.replace("/*DATA*/null", payload), encoding="utf-8")


def rescore(args, grid, shoulder_width, bases, reviewed) -> dict:
    """Cham lai cac doan da danh gia bang luat hien tai (khong ghi clip) va so voi hanh dong thuc te nguoi cham chon."""
    results = cut_and_recognise(args, [dict(window) for window in reviewed], grid, shoulder_width, bases)
    judged = [row for row in results if row.get("truth")]
    per_label = {}
    for label in sorted({row["predicted"] for row in judged} | {row["truth"] for row in judged}):
        predicted = [row for row in judged if row["predicted"] == label]
        actual = [row for row in judged if row["truth"] == label]
        per_label[label] = {
            "predicted": len(predicted),
            "correct": sum(row["truth"] == label for row in predicted),
            "actual": len(actual),
            "found": sum(row["predicted"] == label for row in actual),
        }
    # Cung ghe voi lan truoc? Ty so cui dau tho (khong phu thuoc luat) phai gan nhu cu.
    drift = [
        abs(row["head_drop_ratio"] - window["old_ratio"])
        for row, window in zip(results, reviewed)
        if row["head_drop_ratio"] is not None and window.get("old_ratio") is not None
    ]
    hits = sum(row["predicted"] == row["truth"] for row in judged)
    return {
        "clips": len(judged),
        "correct": hits,
        "accuracy": round(hits / len(judged), 3) if judged else None,
        "per_label": per_label,
        "confusion": dict(Counter(f"{row['truth']} -> {row['predicted']}" for row in judged).most_common()),
        "same_seat_check_mean_abs_head_ratio_diff": round(statistics.mean(drift), 3) if drift else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cat video lop thanh clip 1 nguoi 1 hanh dong de danh gia nhan dien.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Thu muc NGOAI repo; clip co hinh hoc sinh.")
    parser.add_argument("--allow-persistent-output", action="store_true", help="Bat buoc: dong y ghi clip ra dia.")
    parser.add_argument("--review", type=Path, help="CSV da cham lan truoc: cham lai cac doan do, khong cat lai.")
    parser.add_argument(
        "--merge-reviewed",
        action="store_true",
        help="Cat ca cac doan trong --review vao cung bo (dien san hanh dong thuc te da cham de xem lai).",
    )
    parser.add_argument(
        "--no-face-blur",
        action="store_true",
        help="Khong che dau: CHI cho video thanh vien da dong y quay, de doi chieu dung/sai; khong chia se ra ngoai.",
    )
    parser.add_argument("--model", default="models/yolov8n-pose.pt")
    parser.add_argument("--image-size", type=int, default=1280)
    parser.add_argument("--clips", type=int, default=0, help="So clip toi da, chia deu theo hanh dong; 0: tat ca.")
    parser.add_argument("--seconds", type=float, default=2.0)
    parser.add_argument("--step", type=float, default=0.2, help="Buoc truot tim doan (giay).")
    parser.add_argument("--min-seen", type=float, default=0.8, help="Ty le frame phai thay nguoi trong doan.")
    parser.add_argument("--min-share", type=float, default=0.7, help="Ty le frame cua hanh dong chinh.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if not args.allow_persistent_output:
        parser.error("Clip chua hinh hoc sinh: them --allow-persistent-output de xac nhan ghi ra dia.")
    if ROOT.parent in args.output.resolve().parents or args.output.resolve() == ROOT.parent:
        parser.error("--output phai nam ngoai repo: clip khong duoc vao git.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("Can ffmpeg tren PATH de ghi clip H.264.")

    detector = detector_for(args.model, str(args.image_size))
    detector.open()
    frames = []
    for timestamp, image in video_frames(args.video, 5.0, 1e9):
        frames.append((timestamp, kept(detector.detect(image), POSE_CONF)))
        wipe_image(image)
        del image
    widths = [mid[2] for _, people in frames for p in people if (mid := shoulders(p))]
    shoulder_width = statistics.median(widths)
    positions = [
        (x, y)
        for x, y, seen in cluster_positions([p for _, p in frames], POSE_CONF, 0.6 * shoulder_width)
        if seen >= 0.5
    ]
    grid = seats_from(positions, shoulder_width)
    tracks, bases = seat_tracks(frames, grid)
    args.output.mkdir(parents=True, exist_ok=True)

    reviewed = reviewed_windows(args.review) if args.review else []
    previous = rescore(args, grid, shoulder_width, bases, reviewed) if reviewed else None
    if previous:
        (args.output / "rescore.json").write_text(json.dumps(previous, ensure_ascii=False, indent=1), "utf-8")
        print("Cham lai cac doan da danh gia:", json.dumps(previous, ensure_ascii=False, indent=1))

    windows = candidate_windows(tracks, bases, args, reviewed)
    clips = pick(windows, args.clips, args.seed)
    if args.merge_reviewed:  # doan da cham dot truoc vao cung bo, giu hanh dong thuc te de xem lai
        clips = sorted(clips + [dict(window) for window in reviewed], key=lambda w: (w["start"], w["seat"]))
    found = dict(Counter(w["label"] for w in windows))
    print(f"{len(grid.seats)} ghe, {len(windows)} doan moi hop le {found}, cat {len(clips)}")
    results = cut_and_recognise(args, clips, grid, shoulder_width, bases, ffmpeg)
    meta = {
        "video": args.video.name,
        "run": datetime.now().isoformat(timespec="seconds"),
        "seconds_per_clip": args.seconds,
        "image_size": args.image_size,
        "pose_confidence": POSE_CONF,
        "thresholds": {
            "head_down_ratio_without_frontal": THRESHOLDS.head_drop_ratio_threshold,
            "desk_head_drop_vs_frontal": THRESHOLDS.desk_head_drop,
            "desk_ear_rise_vs_frontal": THRESHOLDS.desk_ear_rise,
            "slumped_head_ratio": THRESHOLDS.slumped_head_ratio_threshold,
            "head_turn_ratio_vs_frontal": THRESHOLDS.head_turn_ratio_threshold,
            "torso_deviation_deg": THRESHOLDS.torso_deviation_threshold_deg,
            "face_visibility_back_turn": BACK_TURN,
        },
        "seats": len(grid.seats),
        "seat_frontal_head_turn": {seat: round(f.turn, 3) for seat, (_, f) in sorted(bases.items()) if f},
        "excluded_reviewed_windows": 0 if args.merge_reviewed else len(reviewed),
        "reviewed_windows_in_set": len(reviewed) if args.merge_reviewed else 0,
        "face_blur": not args.no_face_blur,
        "previous_review_rescored": previous and {k: previous[k] for k in ("clips", "correct", "accuracy")},
        "candidate_windows": found,
        "predicted": dict(Counter(r["predicted"] for r in results)),
    }
    write_review(args.output, results, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"Mo {args.output / 'index.html'} de danh gia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
