"""
benchmark_pose_fps.py -- Do FPS thuc te cua YOLOv8-pose tren CPU, o cac do
phan giai khac nhau, phuc vu task "Benchmark FPS YOLOv8-pose tren CPU".

============================================================================
QUAN TRONG -- BAT BUOC chay tren dung may tinh muc tieu:
============================================================================
Script nay PHAI duoc chay tren may tinh du dinh lap dat thuc te o truong (hoac
it nhat cung tam CPU/RAM). Sandbox dung de viet code nay KHONG cai duoc
ultralytics (loi het dung luong dia / Bus error khi import torch), nen script
duoi day CHUA duoc tu chay thu lan nao -- chi duoc kiem tra ky ve mat logic
(cu phap, luong xu ly). Ket qua do tren may ca nhan manh hon/yeu hon may
truong deu KHONG co gia tri tham khao dung.

============================================================================
QUAN TRONG -- nen dung ANH THAT co nhieu nguoi, khong chi anh gia lap:
============================================================================
YOLOv8-pose la model single-shot -- phan lon thoi gian la forward-pass qua
mang no-ron (phu thuoc do phan giai anh dau vao), phan con lai la buoc NMS
(loai bo box trung nhau) va hau xu ly (phu thuoc SO NGUOI thuc te duoc phat
hien). Anh gia lap (nhieu ngau nhien, khong co nguoi) chi do duoc phan
forward-pass, se cho FPS LAC QUAN HON thuc te khi that su co 30-40 hoc sinh
trong khung hinh. Neu chua co anh lop hoc that, hay it nhat dung mot anh co
nhieu nguoi (vi du anh dam dong tai tren mang) truyen qua --image.

Cach chay:
    pip install ultralytics
    python benchmark_pose_fps.py --image duong_dan_anh_lop_hoc.jpg
    python benchmark_pose_fps.py --image duong_dan_anh_lop_hoc.jpg --runs 30
    python benchmark_pose_fps.py                                    # anh gia lap, chi de test nhanh script chay duoc
"""

import argparse
import statistics
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

RESOLUTIONS = [(640, 480), (960, 720), (1280, 960)]


def generate_synthetic_image(width: int, height: int) -> np.ndarray:
    """Sinh anh ngau nhien -- CHI dung khi chua co anh that.

    Canh bao: anh nay KHONG co nguoi, nen chi phi NMS/postprocessing gan nhu
    bang 0 -- FPS do duoc se LAC QUAN HON dang ke so voi thuc te co 30-40
    nguoi trong khung hinh. Chi dung de kiem tra nhanh script chay duoc,
    KHONG dung de chot so lieu benchmark chinh thuc.
    """
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)


def load_or_generate_image(
    image_path: str, width: int, height: int
) -> Tuple[np.ndarray, bool]:
    """Doc anh that neu co duong dan, hoac sinh anh gia lap.

    Tra ve (anh, is_real_image) -- is_real_image=False nghia la anh gia lap,
    ket qua benchmark tuong ung can duoc doc voi canh bao ve muc do lac quan.
    """
    if image_path:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Khong tim thay anh tai '{image_path}'")
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Khong doc duoc anh tai '{image_path}' (file loi/sai dinh dang?)")
        img = cv2.resize(img, (width, height))
        return img, True
    return generate_synthetic_image(width, height), False


def benchmark_resolution(model, image: np.ndarray, n_warmup: int, n_runs: int) -> Tuple[List[float], int]:
    """Chay warmup (khong tinh gio) roi do thoi gian inference qua n_runs lan.

    Tra ve (danh_sach_thoi_gian_giay, so_nguoi_phat_hien_o_lan_cuoi).
    """
    for _ in range(n_warmup):
        model.predict(source=image, verbose=False)

    times = []
    n_detected = 0
    for _ in range(n_runs):
        start = time.perf_counter()
        results = model.predict(source=image, verbose=False)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    if results and results[0].boxes is not None:
        n_detected = len(results[0].boxes)

    return times, n_detected


def main():
    parser = argparse.ArgumentParser(description="Benchmark FPS YOLOv8-pose tren CPU")
    parser.add_argument("--model", default="models/yolov8n-pose.pt", help="Duong dan model (mac dinh: models/yolov8n-pose.pt)")
    parser.add_argument(
        "--image", default=None,
        help="Duong dan anh that (KHUYEN NGHI MANH: dung anh lop hoc/anh dong nguoi). "
             "Neu bo trong, tu sinh anh gia lap KHONG CO NGUOI -- chi de test nhanh."
    )
    parser.add_argument("--runs", type=int, default=20, help="So lan chay moi do phan giai (mac dinh 20)")
    parser.add_argument("--warmup", type=int, default=3, help="So lan chay warmup, khong tinh vao ket qua (mac dinh 3)")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[LOI] Chua cai thu vien 'ultralytics'. Chay: pip install ultralytics")
        return

    print(f"Dang nap model tu '{args.model}' ...")
    try:
        model = YOLO(args.model)
    except Exception as e:
        print(f"[LOI] Khong nap duoc model: {e}")
        return

    if not args.image:
        print()
        print("[CANH BAO] Chua truyen --image -- se dung anh gia lap KHONG CO NGUOI.")
        print("Ket qua FPS se LAC QUAN HON thuc te. Nen chay lai voi anh lop hoc that")
        print("truoc khi chot so lieu vao bao cao benchmark chinh thuc.")
        print()

    print(f"{'Do phan giai':<15}{'FPS trung binh':<16}{'FPS thap nhat':<16}{'Thoi gian TB (ms)':<20}{'So nguoi phat hien':<20}{'Nguon anh'}")
    print("-" * 100)

    results_summary = []

    for width, height in RESOLUTIONS:
        image, is_real = load_or_generate_image(args.image, width, height)
        times, n_detected = benchmark_resolution(model, image, args.warmup, args.runs)

        fps_values = [1.0 / t for t in times]
        avg_fps = statistics.mean(fps_values)
        min_fps = min(fps_values)
        avg_ms = statistics.mean(times) * 1000

        source_label = "anh that" if is_real else "anh gia lap (KHONG co nguoi)"
        res_label = f"{width}x{height}"
        print(f"{res_label:<15}{avg_fps:<16.2f}{min_fps:<16.2f}{avg_ms:<20.1f}{n_detected:<20}{source_label}")

        results_summary.append({
            "resolution": res_label,
            "avg_fps": avg_fps,
            "min_fps": min_fps,
            "avg_ms": avg_ms,
            "n_detected": n_detected,
            "is_real_image": is_real,
        })

    print()
    print("=== Goi y de dien vao bao cao (bien an toan 20% duoi FPS thap nhat do duoc) ===")
    for r in results_summary:
        sustainable = r["min_fps"] * 0.8
        print(f"- {r['resolution']}: FPS trung binh {r['avg_fps']:.2f}  ->  "
              f"de xuat CAMERA_FPS xu ly: {sustainable:.1f}")

    if not any(r["is_real_image"] for r in results_summary):
        print()
        print("*** NHAC LAI: cac so lieu tren do bang anh gia lap KHONG CO NGUOI. ***")
        print("*** Chay lai voi --image tro toi anh lop hoc/dong nguoi that truoc khi chot so lieu. ***")


if __name__ == "__main__":
    main()