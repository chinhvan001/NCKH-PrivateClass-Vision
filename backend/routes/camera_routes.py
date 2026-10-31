import os
import re
from urllib.parse import quote, urlsplit

from flask import Blueprint, Response, jsonify, request
from firebase_admin import firestore
from firebase_config import db
from routes.test_helpers import json_value, require_admin, server_timestamp
from services import monitoring_service


camera_bp = Blueprint("camera_bp", __name__)

# Camera theo sơ đồ đã chốt: cameras/{camera_id} giữ tên phòng, tên camera, IP, cổng (để hiển thị); camera_id
# là camera_id trong cấu hình camera AI, cũng là ID heartbeat edge_nodes/{camera_id} mà camera AI gửi 10 s/lần
# (tình trạng camera lấy từ đây). Lớp camera theo dõi là classes2/{lớp}.camera_id. URL RTSP (kèm tài khoản,
# mật khẩu) nằm riêng ở camera_configs/{camera_id}: Rules chặn mọi client, API không bao giờ trả URL; chỉ
# camera AI đó đọc.
CAMERAS = "cameras"
CAMERA_CONFIGS = "camera_configs"
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


def edge_summary(heartbeat, class_names):
    return {
        "online": monitoring_service.is_online(heartbeat),
        "status": heartbeat.get("status"),
        "class_id": heartbeat.get("class_id"),
        "class_name": class_names.get(heartbeat.get("class_id"), ""),
        "session_id": heartbeat.get("session_id"),
        "fps": heartbeat.get("fps"),
        "camera_ok": heartbeat.get("camera_ok"),
        "updated_at": json_value(heartbeat.get("updated_at")),
    }


def build_camera_data(camera_id, data, edge, class_id=None, class_names=None):
    """data: cameras/{camera_id}, None khi camera AI gửi heartbeat nhưng chưa được thêm trên web."""
    declared = data is not None
    data = data or {}
    rtsp_port = data.get("rtsp_port", "")

    return {
        "id": camera_id,
        "camera_id": camera_id,
        "camera_name": camera_id,  # camera_id trong cấu hình camera AI, khóa của seat_regions
        "name": str(data.get("camera_name") or camera_id).strip(),
        "declared": declared,
        "room_name": data.get("room_name") or "",
        "ip_address": data.get("ip_address", ""),
        "rtsp_port": str(rtsp_port) if rtsp_port else "",
        # lớp có classes2.camera_id là camera này; URL RTSP không bao giờ trả về
        "configured": class_id is not None,
        "class_id": class_id,
        "class_name": (class_names or {}).get(class_id, ""),
        "snapshot": snapshot_enabled() and declared and class_id is not None,
        "status": "online" if edge and edge["online"] else "offline",
        "edge": edge,
    }


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

        if not camera_id or "/" in camera_id:
            return error("Thiếu tên camera (trùng camera_id trong cấu hình camera AI, không chứa '/').", 400)

        if not room_name:
            return error("Thiếu phòng học.", 400)

        source, problem = rtsp_source(data)

        if problem:
            return error(problem, 400)

        problem = class_problem(class_id, camera_id)

        if problem:
            return error(*problem)

        if db.collection(CAMERAS).document(camera_id).get().exists:
            return error("Tên camera này đã được dùng.", 409)

        if any(db.collection(CAMERAS).where("room_name", "==", room_name).limit(1).stream()):
            return error("Phòng học này đã có camera.", 409)

        camera = {"camera_name": camera_id, "room_name": room_name, **camera_fields(data, uid)}
        db.collection(CAMERAS).document(camera_id).set(camera)
        db.collection(CAMERA_CONFIGS).document(camera_id).set(
            {"source": source, "updated_at": server_timestamp(), "updated_by": uid}
        )
        link_class(camera_id, class_id)

        return jsonify({
            "success": True,
            "message": "Thêm camera thành công. Camera AI nhận lớp trong vòng 1 phút.",
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

        config_ref = db.collection(CAMERA_CONFIGS).document(camera_id)
        config_doc = config_ref.get()
        # URL cũ chỉ đọc ở đây để giữ tài khoản, mật khẩu admin không nhập lại; không trả về
        current = ((config_doc.to_dict() or {}).get("source") or "") if config_doc.exists else ""
        source, problem = rtsp_source(data, current)

        if problem:
            return error(problem, 400)

        class_id = str(data.get("class_id") or "").strip()
        problem = class_problem(class_id, camera_id)

        if problem:
            return error(*problem)

        fields = camera_fields(data, uid)
        camera_ref.update(fields)
        # Camera AI đọc lại lớp giữa các tiết và URL mỗi lần mở camera
        config_ref.set({"source": source, "updated_at": server_timestamp(), "updated_by": uid})
        link_class(camera_id, class_id)

        return jsonify({
            "success": True,
            "message": "Đã lưu camera. Camera AI áp dụng từ tiết giám sát tiếp theo.",
            "camera": build_camera_data(camera_id, {**(camera_doc.to_dict() or {}), **fields}, None, class_id),
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

        heartbeats = {doc.id: doc.to_dict() or {} for doc in db.collection("edge_nodes").stream()}
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

            heartbeat = heartbeats.pop(doc.id, None)
            edge = edge_summary(heartbeat, class_names) if heartbeat is not None else None
            cameras.append(build_camera_data(doc.id, data, edge, class_of_camera.get(doc.id), class_names))

        # Camera AI đang gửi heartbeat nhưng chưa được thêm trên trang camera
        for camera_id, heartbeat in heartbeats.items():
            edge = edge_summary(heartbeat, class_names)
            cameras.append(build_camera_data(camera_id, None, edge, class_of_camera.get(camera_id), class_names))

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

        # Bỏ lớp và URL RTSP (có mật khẩu): camera AI chuyển về "chờ thêm camera trên web"
        link_class(camera_id, None)
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
        config_doc = db.collection(CAMERA_CONFIGS).document(camera_id).get()
        source = ((config_doc.to_dict() or {}).get("source") or "") if config_doc.exists else ""

        if not source or not db.collection(CAMERAS).document(camera_id).get().exists:
            return error("Không tìm thấy camera hoặc camera chưa được thêm.", 404)

        class_id = camera_class(camera_id)
        sessions = db.collection("sessions").where("class_id", "==", class_id).stream() if class_id else []
        if any((doc.to_dict() or {}).get("status") in monitoring_service.LIVE_STATUSES for doc in sessions):
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
