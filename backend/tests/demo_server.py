"""Demo web admin + camera AI trên một máy, không cần Firebase, camera hay model.

Backend chạy trên FakeFirestore (như conftest.py), EdgeRuntime thật của camera-ai chạy trong một thread
với camera và pose giả lập, job báo cáo phụ huynh chạy 15 s/lần. Dữ liệu Firestore chỉ nằm trong RAM; file hai
bên trao đổi (edge-data/) nằm trong một thư mục tạm, xóa khi tắt demo.

    camera-ai/venv/Scripts/python backend/tests/demo_server.py
    cd frontend; npm run dev        # rồi mở http://localhost:5173/api/demo-login

--video lop.mp4: YOLO thật nhận diện trên video thay cho pose giả lập (cần camera-ai/models/yolov8n-pose.pt).
CAM-1 phát video đó: vẽ ô ghế trên ảnh lấy từ video trước khi bắt đầu tiết 11B2.

Script, không phải test (pytest chỉ chạy test_*.py).
"""

import argparse
import atexit
import json
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
import numpy as np

import conftest  # thay firebase_admin bằng FakeFirestore, thêm backend và camera-ai vào sys.path
import fake_firestore
from services import edge_store
from src.capture import CaptureConfig, CaptureWorker, Frame
from src.config import LocalPipelineConfig
from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose
from src.main import edge_runtime, pose_detector, web_sessions
from src.privacy.alert_event import make_alert_event
from src.privacy.session_output import SeatEvaluation, SeatResult, SessionResult
from src.sync import LocalSink
from test_local_config import valid_config

DB, TOKENS = conftest.DB, conftest.TOKENS
MODEL = conftest.ROOT / "camera-ai" / "models" / "yolov8n-pose.pt"
VN = ZoneInfo("Asia/Ho_Chi_Minh")
ROWS, COLUMNS = 3, 4
CYCLE_SEC = 180
STUDENTS = {
    "S01": ("an", "Nguyễn Văn An"),
    "S02": ("binh", "Trần Thị Bình"),
    "S03": ("chi", "Phạm Minh Chi"),
    "S04": ("dung", "Lý Quốc Dũng"),
    "S05": ("giang", "Hoàng Thu Giang"),
    "S06": ("hieu", "Đỗ Trung Hiếu"),
    "S08": ("khanh", "Vũ Ngọc Khánh"),
    "S09": ("lan", "Bùi Phương Lan"),
    "S10": ("minh", "Đặng Quang Minh"),
    "S11": ("nga", "Ngô Thanh Nga"),
}
# Vị trí ghế trong ảnh 1280x720 (vai của học sinh giả lập); ô ghế vẽ sẵn cho CAM-1 bao quanh các điểm này
SEAT_XY = {
    f"S{(row - 1) * COLUMNS + column:02d}": (200.0 + (column - 1) * 200, 150.0 + (row - 1) * 180)
    for row in range(1, ROWS + 1)
    for column in range(1, COLUMNS + 1)
}

# Backend (Flask đa luồng), edge và job cùng dùng một FakeFirestore không thread-safe
LOCK = threading.RLock()


def locked(fn):
    def wrapper(*args, **kwargs):
        with LOCK:
            return fn(*args, **kwargs)

    return wrapper


for cls, name in [
    (fake_firestore.FakeFirestore, "_write"),
    (fake_firestore.FakeFirestore, "_snapshots"),
    (fake_firestore.FakeDocument, "get"),
    (fake_firestore.FakeDocument, "update"),
    (fake_firestore.FakeCollection, "_snapshots"),
]:
    setattr(cls, name, locked(getattr(cls, name)))


def seed(video=None):
    today = datetime.now(VN).date().isoformat()
    DB.document("admins/admin-1").set({"email": "admin@example.com", "full_name": "Admin", "is_active": True})
    TOKENS["admin-token"] = {"uid": "admin-1"}
    DB.document("teachers/t1").set(
        {"full_name": "Lê Thu Hà", "email": "ha@example.com", "subject": ["Toán"], "is_active": True}
    )
    seat_map = {}
    for seat in SEAT_XY:
        index = int(seat[1:]) - 1
        student_id = STUDENTS.get(seat, (None,))[0]
        seat_map[seat] = {
            "seat_id": seat,
            "row": index // COLUMNS + 1,
            "column": index % COLUMNS + 1,
            "student_id": student_id,
            "status": "occupied" if student_id else "empty",
        }
    for student_id, name in STUDENTS.values():
        DB.document(f"students2/{student_id}").set({"full_name": name, "is_active": True})
    for class_id, name, subject, rows, columns, seats in [
        ("CLASS-1", "11B2", "Toán", ROWS, COLUMNS, seat_map),
        ("CLASS-2", "11B3", "Văn", 2, 2, {}),
    ]:
        DB.document(f"classes2/{class_id}").set(
            {
                "class_name": name,
                "teacher_id": "t1",
                "school_year": "2026-2027",
                "subject": subject,
                "row_count": rows,
                "column_count": columns,
                "status": "active",
                "seat_map": seats,
            }
        )
    for session_id, class_id, subject, period, start, end, room in [
        ("s1", "CLASS-1", "Toán", 1, "07:00", "07:45", "P201"),
        ("s2", "CLASS-2", "Văn", 2, "07:55", "08:40", "P202"),
    ]:
        DB.document(f"sessions/{session_id}").set(
            {
                "class_id": class_id,
                "teacher_id": "t1",
                "subject": subject,
                "session_date": today,
                "session_type": "morning",
                "period": period,
                "start_time": start,
                "end_time": end,
                "room": room,
                "status": "scheduled",
            }
        )
    # CAM-1 còn rtsp_url kiểu cũ (có mật khẩu): mở trang Quản lý camera là backend xóa nó đi
    DB.document("cameras/CAM-1").set(
        {
            "camera_name": "CAM-1",
            "room_name": "P201",
            "ip_address": "192.168.1.103",
            "rtsp_port": "554",
            "rtsp_url": "rtsp://admin:matkhau@192.168.1.103:554/stream",
        }
    )
    DB.document("cameras/CAM-2").set(
        {"camera_name": "CAM-2", "room_name": "P202", "ip_address": "192.168.1.104", "rtsp_port": "554"}
    )
    # Như admin đã thêm CAM-1 ở "Thêm camera": lớp 11B2 nhận camera_id, URL RTSP chỉ nằm trong file trên máy
    # (trang camera không bao giờ trả URL)
    DB.document("classes2/CLASS-1").update({"camera_id": "CAM-1"})
    edge_store.save_camera("CAM-1", "frontal", str(video) if video else "rtsp://admin:matkhau@192.168.1.103:554/stream")
    # Ô ghế như admin đã vẽ ở "Xác định chỗ ngồi" (ảnh /api/demo/snapshot.png), quanh vai học sinh giả lập.
    # Với --video thì không khớp người trong video: admin vẽ lại trên ảnh lấy từ video.
    if not video:
        DB.document("seat_regions/CAM-1").set(
            {
                "class_id": "CLASS-1",
                "image_width": 1280,
                "image_height": 720,
                "seats": {seat: [x - 90, y - 80, x + 90, y + 80] for seat, (x, y) in SEAT_XY.items()},
                "updated_by": "admin-1",
            }
        )
    scores =[45, 82, 78, 91, 88, 70, 85, 93, 76, 89]
    past_session("h1", 2, dict(zip(STUDENTS, scores)), "completed")
    past_session("h2", 1, dict(zip(STUDENTS, [score - 8 for score in scores])), "incomplete")


def past_session(session_id, days_ago, scores, monitoring_status):
    """Tiết đã giám sát những ngày trước, như edge node đã ghi. "incomplete": edge mất kết nối giữa tiết."""
    day = (datetime.now(VN) - timedelta(days=days_ago)).replace(hour=7, minute=0, second=0, microsecond=0)
    started, ended = day.astimezone(timezone.utc), (day + timedelta(minutes=45)).astimezone(timezone.utc)
    observed = 2700 if monitoring_status == "completed" else 1200
    DB.document(f"sessions/{session_id}").set(
        {
            "class_id": "CLASS-1",
            "teacher_id": "t1",
            "subject": "Toán",
            "session_date": day.date().isoformat(),
            "session_type": "morning",
            "period": 1,
            "start_time": "07:00",
            "end_time": "07:45",
            "room": "P201",
            "status": "completed",
            "started_at": started,
            "ended_at": ended,
        }
    )
    for seat, student in STUDENTS.items():  # bản chốt ghế lúc tiết bắt đầu
        row, column = divmod(int(seat[1:]) - 1, COLUMNS)
        DB.document(f"sessions/{session_id}/monitored_students/{seat}").set(
            {"student_id": student[0], "row": row + 1, "column": column + 1}
        )
    sink = LocalSink(edge_store.ROOT, "CAM-1")  # ghi như camera AI ghi
    seats = tuple(SeatResult(seat, score, 0, "focused" if score >= 60 else "drowsy") for seat, score in scores.items())
    sink.set_result(SessionResult(session_id, "CAM-1", ended, monitoring_status, seats))
    sink.set_evaluations(
        SeatEvaluation(session_id, seat, ended, score, score, 2 if seat == "S01" else 0, observed)
        for seat, score in scores.items()
    )
    for index in range(2):
        sink.add_alert(make_alert_event(session_id, "S01", "head_drop", 300 + index * 600, 40))


def report_loop():
    from services import report_service

    while True:
        with LOCK:
            built = report_service.build_pending_reports()
            DB.reads.clear()  # FakeFirestore ghi lại mọi lần đọc/ghi cho test; demo chạy lâu thì đầy RAM
            DB.commits.clear()
        if built:
            print("Báo cáo phụ huynh đã tạo:", built, flush=True)
        time.sleep(15)


def person(x, y, head_drop=False, turn=0.0, face=True):
    """Skeleton giả: chỉ mũi, vai, hông, cổ tay. turn: mũi lệch ngang (quay sang bạn bên cạnh)."""
    points = [(0.0, 0.0, 0.0)] * 17
    values = {
        "nose": (x + turn, y + (-4.0 if head_drop else -50.0), 0.95 if face else 0.0),
        "left_shoulder": (x - 20.0, y, 0.95),
        "right_shoulder": (x + 20.0, y, 0.95),
        "left_hip": (x - 20.0, y + 60.0, 0.95),
        "right_hip": (x + 20.0, y + 60.0, 0.95),
        "left_wrist": (x - 15.0, y + 30.0, 0.95),
        "right_wrist": (x + 15.0, y + 30.0, 0.95),
    }
    for name, point in values.items():
        points[COCO_KEYPOINT_NAMES.index(name)] = point
    return PersonPose(points, (x - 35.0, y - 60.0, x + 35.0, y + 80.0), 0.9)


class Classroom:
    """Pose giả thay YOLO. Kịch bản tính từ lúc camera bật, lặp mỗi CYCLE_SEC giây: S01 luôn cúi đầu;
    S08 rời chỗ ở giây 20-80 (edge báo "away" sau 30 s); S02 và S03 quay sang nhau ở giây 90-120;
    S06 quay lưng ở giây 130-160."""

    def __init__(self):
        self.start = self.last = 0.0

    def detect(self, image_bgr):
        now = time.time()
        if now - self.last > 5:  # camera vừa bật (bắt đầu hoặc tiếp tục tiết): chạy kịch bản từ đầu
            self.start = now
        self.last = now
        phase = (now - self.start) % CYCLE_SEC
        talking = 90 <= phase < 120
        return [
            person(
                x,
                y,
                head_drop=seat == "S01",
                turn={"S02": 15.0, "S03": -15.0}.get(seat, 0.0) if talking else 0.0,
                face=not (seat == "S06" and 130 <= phase < 160),
            )
            for seat, (x, y) in SEAT_XY.items()
            if seat in STUDENTS and not (seat == "S08" and 20 <= phase < 80)
        ]


class Camera:
    """CaptureWorker giả: khung xám, edge vẫn xóa khung sau mỗi lần suy luận như camera thật."""

    def __init__(self):
        self.buffer, self.is_alive, self.index = self, False, 0

    def start(self):
        self.is_alive = True

    def stop(self):
        self.is_alive = False

    def get(self, timeout=None):
        time.sleep(0.2)  # 5 khung hình/giây như camera thật, không chiếm hết CPU
        self.index += 1
        return Frame(np.full((720, 1280, 3), 128, np.uint8), time.time(), self.index)


def edge_loop(video=None):
    """Edge node của CAM-1 như python -m src.main chạy: tiết, ô ghế và kết quả qua thư mục chung với backend."""
    data = valid_config()
    data["sampling"]["inference_every_n_frames"] = 1
    data["schedule"]["windows"] = [
        {"days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"], "start": "00:00", "end": "23:59"}
    ]
    config = LocalPipelineConfig.from_dict(data)
    provider, capture = Classroom(), Camera
    if video:
        provider = pose_detector(str(MODEL), config.thresholds)
        provider.open()
        capture = partial(
            CaptureWorker,
            CaptureConfig(str(video), target_fps=config.sampling.capture_fps, live_video="://" not in str(video)),
        )
    edge_runtime(edge_store.ROOT, config, provider, capture).run(web_sessions(edge_store.ROOT, "CAM-1"))


FIREBASE_STUB = """import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const app = initializeApp({ apiKey: "demo", authDomain: "demo.firebaseapp.com", projectId: "demo" });

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
"""


def main():
    parser = argparse.ArgumentParser(description="Demo web admin + camera AI, không cần Firebase hay camera.")
    parser.add_argument("--video", type=Path, help="Video lớp học thay cho camera và pose giả lập (YOLO thật).")
    parser.add_argument(
        "--camera-env", metavar="BIEN", help="Camera thật (YOLO thật): tên biến trong .env gốc chứa URL RTSP, vd CAMERA_SOURCE."
    )
    args = parser.parse_args()
    edge_store.ROOT = Path(tempfile.mkdtemp(prefix="edutrack-demo-"))  # không lẫn với edge-data/ thật
    atexit.register(shutil.rmtree, edge_store.ROOT, ignore_errors=True)
    video = args.video
    if args.camera_env:
        env = dict(
            line.strip().split("=", 1) for line in (conftest.ROOT / ".env").read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        )
        video = env.get(args.camera_env, "").strip().strip('"')  # URL có mật khẩu: không in, không ghi log
        if not video:
            raise SystemExit(f"Không có {args.camera_env} trong .env.")
        os.environ["CAMERA_SNAPSHOT"] = "1"
    elif video:
        if not video.is_file():
            raise SystemExit(f"Không tìm thấy video: {video}")
        video = video.resolve()
        os.environ["CAMERA_SNAPSHOT"] = "1"  # "Lấy ảnh từ camera" trả một khung của video để vẽ ô ghế
    seed(video)
    firebase_js = conftest.ROOT / "frontend" / "src" / "firebase.js"
    if not firebase_js.exists():  # file bị gitignore; frontend cần nó để chạy
        firebase_js.write_text(FIREBASE_STUB, encoding="utf-8")
        print(f"Đã tạo {firebase_js} giả cho demo (đăng nhập Google sẽ không chạy).")
    threading.Thread(target=report_loop, daemon=True).start()
    threading.Thread(target=edge_loop, args=(video,), daemon=True).start()
    if video:
        print(
            f"Camera AI dùng {args.camera_env or video} cho CAM-1. Trước khi bắt đầu tiết 11B2: Quản lý camera -> CAM-1 ->"
            " Xác định chỗ ngồi -> Lấy ảnh từ camera, vẽ ô cho từng chỗ ngồi rồi lưu.",
            flush=True,
        )

    from flask import Response, abort, jsonify

    from app import app
    from routes.test_helpers import json_document

    @app.get("/api/demo-login")
    def demo_login():
        """Đăng nhập admin không qua Firebase: mở qua Vite (localhost:5173) để lưu vào localStorage của frontend."""
        user = json.dumps(json.dumps({"name": "Admin", "email": "admin@example.com", "role": "admin"}))
        return (
            "<script>"
            f"localStorage.setItem('adminUser', {user});"
            "localStorage.setItem('idToken', 'admin-token');"
            "localStorage.setItem('sessionExpiresAt', String(Date.now() + 8 * 3600 * 1000));"
            "location.replace('/dashboard');"
            "</script>"
        )

    @app.get("/api/demo/db/<path:path>")
    def demo_db(path):
        """Xem "Firestore" của demo: đường dẫn collection (vd sessions) hoặc document."""
        try:
            if path.count("/") % 2 == 0:
                return jsonify([json_document(doc) for doc in DB.collection(path).stream()])
            doc = DB.document(path).get()
        except ValueError:
            abort(400)
        return jsonify(json_document(doc)) if doc.exists else abort(404)

    @app.get("/api/demo/edge/<path:path>")
    def demo_edge(path):
        """Xem file hai bên trao đổi (edge-data/), vd sessions/s1/result.json hoặc sessions/s1/alerts.jsonl."""
        target = (edge_store.ROOT / path).resolve()
        if edge_store.ROOT.resolve() not in target.parents or not target.is_file():
            abort(404)
        text = target.read_text(encoding="utf-8")  # nguyên nội dung file, thời gian giữ dạng ISO
        rows = [json.loads(line) for line in text.splitlines()] if target.suffix == ".jsonl" else json.loads(text)
        return jsonify(rows)

    @app.get("/api/demo/snapshot.png")
    def demo_snapshot():
        """Ảnh lớp trống vẽ bằng OpenCV (không phải ảnh camera), cùng góc với pose giả lập: tải về rồi chọn
        trong "Xác định chỗ ngồi" để thử vẽ ô."""
        image = np.full((720, 1280, 3), (226, 230, 233), np.uint8)
        cv2.rectangle(image, (440, 20), (840, 70), (70, 100, 70), -1)  # bảng
        for x, y in SEAT_XY.values():
            x, y = int(x), int(y)
            cv2.rectangle(image, (x - 75, y + 25), (x + 75, y + 65), (80, 120, 160), -1)  # bàn
            cv2.rectangle(image, (x - 25, y - 40), (x + 25, y + 20), (110, 110, 110), 3)  # lưng ghế
        return Response(cv2.imencode(".png", image)[1].tobytes(), mimetype="image/png")

    print("Frontend: cd frontend; npm run dev  ->  http://localhost:5173/api/demo-login", flush=True)
    print("Firestore: http://localhost:5173/api/demo/db/sessions (classes2, students2/an/reports...)", flush=True)
    print("Camera AI: http://localhost:5173/api/demo/edge/sessions/s1/result.json (alerts.jsonl...)", flush=True)
    print("Ảnh lớp trống để vẽ ô ghế: http://localhost:5173/api/demo/snapshot.png", flush=True)
    app.run(host="127.0.0.1", port=5000, threaded=True, use_reloader=False, load_dotenv=False)


if __name__ == "__main__":
    main()
