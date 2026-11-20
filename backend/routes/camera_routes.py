import os
import re
from urllib.parse import quote, urlsplit

from flask import Blueprint, Response, jsonify, request
from firebase_admin import firestore
from firebase_config import db
from routes.test_helpers import json_value, require_admin, server_timestamp
from services import edge_store, monitoring_service


camera_bp = Blueprint("camera_bp", __name__)

# Camera theo sơ đồ đã chốt: cameras/{camera_id} giữ tên phòng, tên camera, IP, cổng, góc (để hiển thị); camera_id
# là tên camera camera AI dùng, cũng là tên file heartbeat camera AI ghi 10 s/lần (tình trạng camera lấy từ đây).
# Lớp camera theo dõi là classes2/{lớp}.camera_id. URL RTSP (kèm tài khoản, mật khẩu) không lên Firestore: nó nằm
# trong edge-data/cameras/{camera_id}.json trên máy chạy cả web và camera AI (services/edge_store.py); API không
# bao giờ trả URL.
CAMERAS = "cameras"
CAMERA_CONFIGS = "camera_configs"  # nơi lưu URL trước đây: chỉ còn đọc để chuyển sang file, rồi xóa
# IPv4 hoặc tên máy: không cho chèn "user:pass@", cổng hay đường dẫn vào URL
HOST = re.compile(r"[A-Za-z0-9.-]{1,253}")
STREAM_TIMEOUT_MS = 10000  # như camera AI: OpenCV mặc định chờ ~90 s khi camera không trả lời


def snapshot_enabled():
    """Xem ảnh camera để test, tắt mặc định: CAMERA_SNAPSHOT=1 trong backend/.env. Đây là ngoại lệ với quy
    tắc "khung hình không rời edge node" (camera-ai/docs/cloud_data_compliance_checklist.md §3.14)."""
    return os.getenv("CAMERA_SNAPSHOT") == "1"


def grab_jpeg(source):
    """Một khung hình JPEG (bytes) từ URL RTSP, None nếu không lấy được. Chỉ trong RAM: không ghi đĩa,
    khung hình bị xóa sau khi mã hóa, camera đóng ngay."""
    import cv2  # chỉ cần khi bật CAMERA_SNAPSHOT (opencv-python-headless)

    timeouts = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, STREAM_TIMEOUT_MS, cv2.CAP_PROP_READ_TIMEOUT_MSEC, STREAM_TIMEOUT_MS]
    capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG, timeouts)
    try:
        ok, frame = capture.read() if capture.isOpened() else (False, None)
        if not ok or frame is None:
            return None
        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame[:] = 0
        return jpeg.tobytes() if ok else None
    finally:
        capture.release()


def rtsp_source(data, current=""):
    """(URL RTSP camera AI dùng, None) hoặc (None, lỗi). Tài khoản, mật khẩu được mã hóa %, nên
    @ : / # trong mật khẩu không làm hỏng URL hay lọt vào log của camera AI. current: URL đang lưu (sửa
    camera): đường dẫn để trống thì giữ đường dẫn cũ, tài khoản và mật khẩu cùng để trống thì giữ cả hai, chỉ
    khi IP và cổng không đổi: không thì ai sửa được camera trỏ nó sang máy khác là lấy được mật khẩu."""
    host = str(data.get("ip_address") or "").strip()
    if not HOST.fullmatch(host):
        return None, "Địa chỉ IP không hợp lệ."
    port = str(data.get("rtsp_port") or "").strip()
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        return None, "RTSP port phải là số từ 1 đến 65535."
    old = urlsplit(current)
    path = str(data.get("stream_path") or "").strip() or old.path + (f"?{old.query}" if old.query else "")
    if any(char.isspace() for char in path):
        return None, "Đường dẫn luồng không được chứa khoảng trắng."
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    if username or password:
        auth = f"{quote(username, safe='')}:{quote(password, safe='')}@"
    else:
        userinfo = old.netloc.rpartition("@")[0]  # đã mã hóa %: @ cuối cùng tách tài khoản khỏi host
        if userinfo and (old.hostname, old.port) != (host.lower(), int(port)):
            return None, "Đổi địa chỉ IP hoặc cổng thì nhập lại tài khoản và mật khẩu camera."
        auth = f"{userinfo}@" if userinfo else ""
    return f"rtsp://{auth}{host}:{int(port)}/{path.lstrip('/')}", None


def error(message, status):
    return jsonify({"success": False, "message": message}), status


def camera_class(camera_id):
    """ID lớp có classes2.camera_id là camera này, hoặc None."""
    for doc in db.collection("classes2").where("camera_id", "==", camera_id).limit(1).stream():
        return doc.id
    return None


def class_problem(class_id, camera_id):
    """(lỗi, mã) nếu không gắn được lớp class_id cho camera này, hoặc None."""
    if not class_id or "/" in class_id:
        return "Chọn lớp mà camera theo dõi.", 400
    doc = db.collection("classes2").document(class_id).get()
    if not doc.exists:
        return "Không tìm thấy lớp học.", 404
    linked = (doc.to_dict() or {}).get("camera_id")
    # 2 camera cùng lớp thì cả 2 camera AI cùng ghi kết quả của một tiết
    if linked and linked != camera_id and db.collection(CAMERAS).document(linked).get().exists:
        return "Lớp này đã có camera.", 409
    return None


def link_class(camera_id, class_id):
    """Camera theo dõi đúng lớp class_id (None: không lớp nào): bỏ camera_id ở lớp cũ, ghi vào lớp mới."""
    classes = db.collection("classes2")
    for doc in classes.where("camera_id", "==", camera_id).stream():
        if doc.id != class_id:
            classes.document(doc.id).update({"camera_id": firestore.DELETE_FIELD, "updated_at": server_timestamp()})
    if class_id:
        classes.document(class_id).update({"camera_id": camera_id, "updated_at": server_timestamp()})


def edge_summary(heartbeat, class_id, class_names):
    return {
        "online": monitoring_service.is_online(heartbeat),
        "status": heartbeat.get("status"),
        "class_id": class_id,
        "class_name": class_names.get(class_id, ""),
        "session_id": heartbeat.get("session_id"),
        "fps": heartbeat.get("fps"),
        "camera_ok": heartbeat.get("camera_ok"),
        "updated_at": json_value(heartbeat.get("updated_at")),
    }


def build_camera_data(camera_id, data, edge, class_id=None, class_names=None):
    """data: cameras/{camera_id}. Camera AI chạy một edge node cho mỗi camera thêm ở đây."""
    rtsp_port = data.get("rtsp_port", "")

    return {
        "id": camera_id,
        "camera_id": camera_id,
        "camera_name": camera_id,  # tên camera camera AI dùng, khóa của seat_regions và edge_nodes
        "name": str(data.get("camera_name") or camera_id).strip(),
        "room_name": data.get("room_name") or "",
        "ip_address": data.get("ip_address", ""),
        "rtsp_port": str(rtsp_port) if rtsp_port else "",
        "angle_type": data.get("angle_type") or "frontal",
        # lớp có classes2.camera_id là camera này; URL RTSP không bao giờ trả về
        "configured": class_id is not None,
        "class_id": class_id,
        "class_name": (class_names or {}).get(class_id, ""),
        "snapshot": snapshot_enabled() and class_id is not None,
        "status": "online" if edge and edge["online"] else "offline",
        "edge": edge,
    }


def current_source(camera_id):
    """URL đang lưu của camera; camera thêm trước khi URL chuyển khỏi Firestore thì lấy ở camera_configs."""
    stored = (edge_store.camera(camera_id) or {}).get("source")
    if stored:
        return stored
    config_doc = db.collection(CAMERA_CONFIGS).document(camera_id).get()
    return ((config_doc.to_dict() or {}).get("source") or "") if config_doc.exists else ""


def class_is_live(class_id):
    """Lớp đang có tiết running/paused: camera AI đang hoặc sắp giám sát."""
    sessions = db.collection("sessions").where("class_id", "==", class_id).stream() if class_id else []
    return any((doc.to_dict() or {}).get("status") in monitoring_service.LIVE_STATUSES for doc in sessions)


# Góc đặt camera: frontal (phía trước lớp, nhìn thẳng học sinh) hay top_down (từ trên cao). Camera AI chỉ
# báo quay lưng với frontal; đổi góc thì camera AI khởi động lại edge node của camera trong 30 giây.
ANGLE_TYPES = ("frontal", "top_down")


def camera_fields(data, uid):
    return {
        "ip_address": str(data.get("ip_address")).strip(),
        "rtsp_port": str(int(str(data.get("rtsp_port")).strip())),
        "updated_at": server_timestamp(),
        "updated_by": uid,
    }


@camera_bp.route("/api/admin/cameras", methods=["POST"])
def create_camera():
    try:
        uid, error_response = require_admin()

        if error_response:
            return error_response

        data = request.get_json(silent=True)

        if not data:
            return error("Request body không hợp lệ.", 400)

        camera_id = str(data.get("camera_name") or data.get("name") or "").strip()
        room_name = str(data.get("room_name") or "").strip()
        class_id = str(data.get("class_id") or "").strip()

        if not edge_store.valid_camera_id(camera_id):
            return error('Thiếu tên camera, hoặc tên có ký tự không dùng được (\\ / : * ? " < > |).', 400)

        if not room_name:
            return error("Thiếu phòng học.", 400)

        source, problem = rtsp_source(data)

        if problem:
            return error(problem, 400)

        angle = data.get("angle_type") or "frontal"

        if angle not in ANGLE_TYPES:
            return error("Góc đặt camera không hợp lệ.", 400)

        problem = class_problem(class_id, camera_id)

        if problem:
            return error(*problem)

        if db.collection(CAMERAS).document(camera_id).get().exists:
            return error("Tên camera này đã được dùng.", 409)

        if any(db.collection(CAMERAS).where("room_name", "==", room_name).limit(1).stream()):
            return error("Phòng học này đã có camera.", 409)

        camera = {"camera_name": camera_id, "room_name": room_name, "angle_type": angle, **camera_fields(data, uid)}
        edge_store.save_camera(camera_id, angle, source)
        db.collection(CAMERA_CONFIGS).document(camera_id).delete()  # URL lưu kiểu cũ, nếu camera từng được thêm
        db.collection(CAMERAS).document(camera_id).set(camera)
        link_class(camera_id, class_id)

        return jsonify({
            "success": True,
            "message": "Thêm camera thành công. Camera AI bắt đầu theo dõi camera này trong vòng 30 giây; "
            "hãy xác định chỗ ngồi trước tiết đầu tiên.",
            "camera": build_camera_data(camera_id, camera, None, class_id),
        }), 201

    except Exception as e:
        print("Create camera error:", e)

        return error(str(e), 500)


@camera_bp.route("/api/admin/cameras/<camera_id>", methods=["PUT"])
def update_camera(camera_id):
    """Sửa lớp, IP, cổng, đường dẫn luồng, tài khoản camera. Tên camera (camera_id của camera AI) và phòng
    giữ nguyên: muốn đổi thì xóa camera rồi thêm lại."""
    try:
        uid, error_response = require_admin()

        if error_response:
            return error_response

        data = request.get_json(silent=True) or {}
        camera_ref = db.collection(CAMERAS).document(camera_id)
        camera_doc = camera_ref.get()

        if not camera_doc.exists:
            return error("Không tìm thấy camera.", 404)

        # URL cũ chỉ đọc ở đây để giữ tài khoản, mật khẩu admin không nhập lại; không trả về
        current = current_source(camera_id)
        source, problem = rtsp_source(data, current)

        if problem:
            return error(problem, 400)

        stored = camera_doc.to_dict() or {}
        angle = data.get("angle_type") or stored.get("angle_type") or "frontal"

        if angle not in ANGLE_TYPES:
            return error("Góc đặt camera không hợp lệ.", 400)

        class_id = str(data.get("class_id") or "").strip()
        problem = class_problem(class_id, camera_id)

        if problem:
            return error(*problem)

        if angle != (stored.get("angle_type") or "frontal") and class_is_live(camera_class(camera_id)):
            return error("Lớp đang có tiết giám sát: đổi góc camera sau khi tiết kết thúc.", 409)

        fields = {**camera_fields(data, uid), "angle_type": angle}
        # Camera AI đọc lại URL mỗi lần mở camera; lớp mới có hiệu lực từ tiết bắt đầu sau
        edge_store.save_camera(camera_id, angle, source)
        db.collection(CAMERA_CONFIGS).document(camera_id).delete()  # URL lưu kiểu cũ trên Firestore
        camera_ref.update(fields)
        link_class(camera_id, class_id)

        return jsonify({
            "success": True,
            "message": "Đã lưu camera. Camera AI áp dụng từ tiết giám sát tiếp theo.",
            "camera": build_camera_data(camera_id, {**stored, **fields}, None, class_id),
        }), 200

    except Exception as e:
        print("Update camera error:", e)

        return error(str(e), 500)


@camera_bp.route("/api/admin/cameras", methods=["GET"])
def get_cameras():
    try:
        _, error_response = require_admin()

        if error_response:
            return error_response

        heartbeats = edge_store.heartbeats()
        class_names, class_of_camera = {}, {}
        for doc in db.collection("classes2").select(["class_name", "camera_id"]).stream():
            data = doc.to_dict() or {}
            class_names[doc.id] = data.get("class_name", "")
            if data.get("camera_id"):
                class_of_camera[data["camera_id"]] = doc.id

        cameras = []

        for doc in db.collection(CAMERAS).stream():
            data = doc.to_dict() or {}

            if "rtsp_url" in data:
                # Dữ liệu cũ: URL RTSP kèm mật khẩu không được nằm trong collection app đọc được
                db.collection(CAMERAS).document(doc.id).update({"rtsp_url": firestore.DELETE_FIELD})

            heartbeat, class_id = heartbeats.pop(doc.id, None), class_of_camera.get(doc.id)
            edge = edge_summary(heartbeat, class_id, class_names) if heartbeat is not None else None
            cameras.append(build_camera_data(doc.id, data, edge, class_id, class_names))

        return jsonify({
            "success": True,
            "cameras": cameras,
            "total": len(cameras),
        }), 200

    except Exception as e:
        print("Get cameras error:", e)

        return error(str(e), 500)


@camera_bp.route("/api/admin/cameras/<camera_id>", methods=["DELETE"])
def delete_camera(camera_id):
    try:
        _, error_response = require_admin()

        if error_response:
            return error_response

        camera_ref = db.collection(CAMERAS).document(camera_id)

        if not camera_ref.get().exists:
            return error("Không tìm thấy camera.", 404)

        # Bỏ lớp và URL RTSP (có mật khẩu): camera AI dừng edge node của camera
        link_class(camera_id, None)
        if edge_store.valid_camera_id(camera_id):
            edge_store.delete_camera(camera_id)
        db.collection(CAMERA_CONFIGS).document(camera_id).delete()
        camera_ref.delete()

        return jsonify({
            "success": True,
            "message": "Xóa camera thành công.",
            "camera_id": camera_id,
        }), 200

    except Exception as e:
        print("Delete camera error:", e)

        return error(str(e), 500)


@camera_bp.route("/api/admin/cameras/<camera_id>/snapshot", methods=["GET"])
def camera_snapshot(camera_id):
    """Một ảnh camera để test kết nối hoặc vẽ ô ghế. Chỉ khi bật CAMERA_SNAPSHOT, chỉ admin, không khi lớp
    đang có tiết giám sát; ảnh không lưu ở đâu, không cache, URL không bao giờ trả về."""
    if not snapshot_enabled():
        return error("Chưa bật xem ảnh camera (CAMERA_SNAPSHOT=1).", 404)

    _, error_response = require_admin()

    if error_response:
        return error_response

    try:
        source = (edge_store.camera(camera_id) or {}).get("source") or ""

        if not source or not db.collection(CAMERAS).document(camera_id).get().exists:
            return error("Không tìm thấy camera hoặc camera chưa được thêm.", 404)

        if class_is_live(camera_class(camera_id)):
            return error("Lớp đang có tiết giám sát: không xem ảnh camera trong giờ học.", 409)

        image = grab_jpeg(source)

    except ImportError:
        return error("Máy chủ chưa cài opencv-python-headless.", 501)

    except Exception as e:
        print("Camera snapshot error:", type(e).__name__)  # không in lỗi: có thể chứa URL kèm mật khẩu
        image = None

    if image is None:
        return error("Không lấy được hình từ camera. Kiểm tra IP, cổng, đường dẫn luồng, tài khoản và mật khẩu.", 502)

    return Response(image, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


# Xác định chỗ ngồi: ô chữ nhật của từng ghế trên ảnh chụp từ camera. Ảnh chỉ hiển thị trong trình duyệt
# của admin, server chỉ nhận tọa độ. camera_name là camera_id của camera AI.
@camera_bp.route("/api/admin/seat-regions/<camera_name>", methods=["GET"])
def get_seat_regions(camera_name):
    uid, auth_error = require_admin()
    if auth_error:
        return auth_error
    doc = db.collection("seat_regions").document(camera_name).get()
    data = json_value(doc.to_dict() or {}) if doc.exists else None
    return jsonify({"success": True, "seat_regions": data}), 200


@camera_bp.route("/api/admin/seat-regions/<camera_name>", methods=["PUT"])
def save_seat_regions(camera_name):
    uid, auth_error = require_admin()
    if auth_error:
        return auth_error
    ref = db.collection("seat_regions").document(camera_name)
    data, problem = monitoring_service.clean_seat_regions(request.get_json(silent=True) or {})
    if problem:
        return jsonify({"success": False, "message": problem}), 400
    if not data["seats"]:  # xóa hết ô: camera AI quay về 4 ghế góc trong cấu hình của nó
        ref.delete()
        return jsonify({"success": True, "seat_regions": None}), 200
    ref.set({**data, "updated_at": server_timestamp(), "updated_by": uid})
    return jsonify({"success": True, "seat_regions": json_value(ref.get().to_dict() or {})}), 200
