"""
capture_test.py — Script capture co ban cho module camera-ai
--------------------------------------------------------------
Muc dich: Doc khung hinh (frame) tu webcam va hien thi thu, de xac nhan
moi truong (OpenCV, camera, driver) hoat dong dung truoc khi bat dau
xay dung module capture/ chinh thuc o Sprint 2.
 
Cach chay:
    python capture_test.py
 
Phim tat khi cua so dang mo:
    q hoac ESC  -> thoat chuong trinh
 
Cau hinh nhanh qua bien moi truong (tuy chon, doc tu .env neu co):
    CAMERA_SOURCE   -> chi so camera (mac dinh 0) hoac duong dan RTSP/IP camera
    CAMERA_WIDTH    -> do rong khung hinh mong muon (vd 1280)
    CAMERA_HEIGHT   -> do cao khung hinh mong muon (vd 720)
"""
 
import os
import sys
import time
 
import cv2
 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv chua duoc cai, van chay duoc voi gia tri mac dinh
    pass
 
 
def get_camera_source():
    """Doc CAMERA_SOURCE tu bien moi truong; tra ve int neu la webcam noi bo,
    hoac string neu la duong dan/RTSP URL cua IP camera."""
    raw = os.getenv("CAMERA_SOURCE", "0")
    try:
        return int(raw)
    except ValueError:
        return raw  # vi du: rtsp://... hoac duong dan file video
 
 
def open_camera(source):
    """Mo camera va tra ve VideoCapture object. Nem RuntimeError neu that bai."""
    cap = cv2.VideoCapture(source)
 
    width = os.getenv("CAMERA_WIDTH")
    height = os.getenv("CAMERA_HEIGHT")
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
 
    if not cap.isOpened():
        raise RuntimeError(
            f"Khong mo duoc camera voi source={source!r}. "
            "Kiem tra lai CAMERA_SOURCE, quyen truy cap camera, "
            "hoac camera co dang bi ung dung khac chiem dung khong."
        )
    return cap
 
 
def main():
    source = get_camera_source()
    print(f"[INFO] Dang mo camera voi source = {source!r} ...")
 
    try:
        cap = open_camera(source)
    except RuntimeError as e:
        print(f"[LOI] {e}")
        sys.exit(1)
 
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Camera da mo thanh cong. Do phan giai: {actual_w}x{actual_h}")
    print("[INFO] Nhan 'q' hoac ESC trong cua so hien thi de thoat.")
 
    prev_time = time.time()
    fps_display = 0.0
 
    try:
        while True:
            ret, frame = cap.read()
 
            if not ret or frame is None:
                print("[CANH BAO] Khong doc duoc frame — thu lai...")
                time.sleep(0.1)
                continue
 
            # Tinh FPS thuc te de kiem tra hieu nang doc camera
            now = time.time()
            elapsed = now - prev_time
            prev_time = now
            if elapsed > 0:
                fps_display = 0.9 * fps_display + 0.1 * (1.0 / elapsed)
 
            # Ve thong tin overlay len khung hinh de kiem tra truc quan
            cv2.putText(
                frame,
                f"FPS: {fps_display:.1f}  |  {actual_w}x{actual_h}  |  q/ESC de thoat",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
 
            cv2.imshow("camera-ai - Capture Test (Sprint 1)", frame)
 
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 27 = phim ESC
                print("[INFO] Nguoi dung yeu cau thoat.")
                break
 
    except KeyboardInterrupt:
        print("\n[INFO] Da nhan Ctrl+C, dang thoat...")
 
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Da giai phong camera va dong cua so hien thi.")
 
 
if __name__ == "__main__":
    main()