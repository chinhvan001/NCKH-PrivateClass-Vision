from flask import Blueprint, jsonify, request
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
)
from firebase_admin import firestore
from firebase_config import db
from routes.test_helpers import json_value
from services import monitoring_service


camera_bp = Blueprint("camera_bp", __name__)

# Camera khai báo trong classrooms/{phòng}: tên, IP, cổng. Địa chỉ RTSP (có mật khẩu) không bao giờ lưu
# trên web: nó nằm trong biến môi trường của camera AI (edge node, camera.source_env). Tình trạng camera
# lấy từ heartbeat edge_nodes/{camera_id} mà camera AI gửi 10 s/lần; camera_name là camera_id đó.
CAMERA_FIELDS = ("camera_name", "ip_address", "rtsp_port")


def authorize_admin():
    decoded_token = verify_request_token()

    if not decoded_token:
        return None, (
            jsonify({
                "success": False,
                "message": "Unauthorized."
            }),
            401,
        )

    _, current_user = get_current_user(decoded_token)

    if not current_user:
        return None, (
            jsonify({
                "success": False,
                "message": "Tài khoản không tồn tại."
            }),
            403,
        )

    if not is_admin_user(current_user):
        return None, (
            jsonify({
                "success": False,
                "message": "Bạn không có quyền truy cập."
            }),
            403,
        )

    return current_user, None


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


def build_camera_data(room_id, data, edge):
    camera_name = data.get("camera_name", "")
    rtsp_port = data.get("rtsp_port", "")

    return {
        "id": room_id or f"edge:{camera_name}",
        "camera_id": room_id,

        "name": camera_name,
        "camera_name": camera_name,

        "room_id": room_id,
        "classroom_name": data.get("classroom_name", ""),

        "ip_address": data.get("ip_address", ""),
        "rtsp_port": str(rtsp_port) if rtsp_port else "",

        "status": "online" if edge and edge["online"] else "offline",
        "edge": edge,
    }


@camera_bp.route("/api/admin/cameras", methods=["POST"])
def create_camera():
    try:
        _, error_response = authorize_admin()

        if error_response:
            return error_response

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body không hợp lệ."
            }), 400

        room_id = data.get("room_id")
        camera_name = data.get("camera_name") or data.get("name")
        ip_address = data.get("ip_address")
        rtsp_port = data.get("rtsp_port")

        if not room_id:
            return jsonify({
                "success": False,
                "message": "Thiếu mã phòng."
            }), 400

        if not camera_name:
            return jsonify({
                "success": False,
                "message": "Thiếu tên camera."
            }), 400

        if not ip_address:
            return jsonify({
                "success": False,
                "message": "Thiếu địa chỉ IP."
            }), 400

        if not rtsp_port:
            return jsonify({
                "success": False,
                "message": "Thiếu RTSP port."
            }), 400

        classroom_ref = db.collection("classrooms").document(room_id)
        classroom_doc = classroom_ref.get()

        if not classroom_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy phòng học."
            }), 404

        classroom_data = classroom_doc.to_dict()

        if classroom_data.get("camera_name"):
            return jsonify({
                "success": False,
                "message": "Phòng học này đã có camera."
            }), 409

        # rtsp_url (nếu client cũ còn gửi) không được lưu
        classroom_ref.update({
            "camera_name": camera_name,
            "ip_address": ip_address,
            "rtsp_port": str(rtsp_port),
            "rtsp_url": firestore.DELETE_FIELD,
        })

        updated_doc = classroom_ref.get()

        camera_data = build_camera_data(updated_doc.id, updated_doc.to_dict() or {}, None)

        return jsonify({
            "success": True,
            "message": "Thêm camera thành công.",
            "camera": camera_data,
        }), 201

    except Exception as e:
        print("Create camera error:", e)

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

@camera_bp.route("/api/admin/cameras", methods=["GET"])
def get_cameras():
    try:
        _, error_response = authorize_admin()

        if error_response:
            return error_response

        heartbeats = {doc.id: doc.to_dict() or {} for doc in db.collection("edge_nodes").stream()}
        class_names = {
            doc.id: (doc.to_dict() or {}).get("class_name", "")
            for doc in db.collection("classes2").select(["class_name"]).stream()
        }

        cameras = []

        for doc in db.collection("classrooms").stream():
            data = doc.to_dict() or {}

            if "rtsp_url" in data:
                # Dữ liệu cũ: xóa địa chỉ RTSP kèm mật khẩu khỏi Firestore
                db.collection("classrooms").document(doc.id).update({"rtsp_url": firestore.DELETE_FIELD})

            if not any(data.get(field) for field in CAMERA_FIELDS):
                continue

            heartbeat = heartbeats.pop(data.get("camera_name"), None)
            edge = edge_summary(heartbeat, class_names) if heartbeat is not None else None
            cameras.append(build_camera_data(doc.id, data, edge))

        # Camera AI đang gửi heartbeat nhưng chưa được khai báo trong phòng nào
        for camera_id, heartbeat in heartbeats.items():
            cameras.append(build_camera_data(None, {"camera_name": camera_id}, edge_summary(heartbeat, class_names)))

        return jsonify({
            "success": True,
            "cameras": cameras,
            "total": len(cameras),
        }), 200

    except Exception as e:
        print("Get cameras error:", e)

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

@camera_bp.route(
    "/api/admin/cameras/<camera_id>",
    methods=["DELETE"]
)
def delete_camera(camera_id):
    try:
        _, error_response = authorize_admin()

        if error_response:
            return error_response

        classroom_ref = db.collection(
            "classrooms"
        ).document(camera_id)

        classroom_doc = classroom_ref.get()

        if not classroom_doc.exists:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy phòng học."
            }), 404

        classroom_ref.update({
            "camera_name": firestore.DELETE_FIELD,
            "ip_address": firestore.DELETE_FIELD,
            "rtsp_port": firestore.DELETE_FIELD,
            "rtsp_url": firestore.DELETE_FIELD,
            "status": firestore.DELETE_FIELD,
        })

        return jsonify({
            "success": True,
            "message": "Xóa camera khỏi phòng thành công.",
            "camera_id": camera_id,
        }), 200

    except Exception as e:

        print("Delete camera error:", e)

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500
