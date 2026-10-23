from flask import Blueprint, jsonify, request
from utils.auth import (
    verify_request_token,
    get_current_user,
    is_admin_user,
)
from google.cloud import firestore
import subprocess
from firebase_config import db


camera_bp = Blueprint("camera_bp", __name__)


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

def build_camera_data(doc):
    data = doc.to_dict()

    camera_name = data.get("camera_name", "")
    ip_address = data.get("ip_address", "")
    rtsp_port = data.get("rtsp_port", "")
    rtsp_url = data.get("rtsp_url", "")

    is_configured = all([
        camera_name,
        ip_address,
        rtsp_port,
        rtsp_url,
    ])

    return {
        "id": doc.id,
        "camera_id": doc.id,

        "name": camera_name,
        "camera_name": camera_name,

        "room_id": doc.id,
        "classroom_name": data.get("classroom_name", ""),

        "ip_address": ip_address,
        "rtsp_port": str(rtsp_port) if rtsp_port else "",
        "rtsp_url": rtsp_url,

        "status": data.get("status", "offline"),

        "is_configured": is_configured,
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
        rtsp_url = data.get("rtsp_url")

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

        if not rtsp_url:
            return jsonify({
                "success": False,
                "message": "Thiếu RTSP URL."
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


        classroom_ref.update({
            "camera_name": camera_name,
            "ip_address": ip_address,
            "rtsp_port": str(rtsp_port),
            "rtsp_url": rtsp_url,
            "status": "offline",
        })

        updated_doc = classroom_ref.get()

        camera_data = build_camera_data(updated_doc)

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

        classroom_docs = db.collection("classrooms").stream()

        cameras = []

        for doc in classroom_docs:
            data = doc.to_dict()

            has_camera_data = any([
                data.get("camera_name"),
                data.get("ip_address"),
                data.get("rtsp_port"),
                data.get("rtsp_url"),
            ])

            if not has_camera_data:
                continue

            cameras.append(
                build_camera_data(doc)
            )

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
    "/api/admin/cameras/test-connection",
    methods=["POST"]
)
def test_camera_connection():
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

        rtsp_url = data.get("rtsp_url")

        if not rtsp_url:
            return jsonify({
                "success": False,
                "message": "Thiếu RTSP URL."
            }), 400

        ffprobe_path = r"D:\Tools\ffmpeg\bin\ffprobe.exe"

        command = [
            ffprobe_path,
            "-v",
            "error",
            "-rtsp_transport",
            "tcp",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            rtsp_url,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return jsonify({
                "success": True,
                "connected": False,
                "status": "offline",
                "message": "Không thể kết nối đến RTSP stream.",
            }), 200

        return jsonify({
            "success": True,
            "connected": True,
            "status": "online",
            "message": "Kết nối RTSP thành công.",
            "stream_info": result.stdout,
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": True,
            "connected": False,
            "status": "offline",
            "message": "Kiểm tra RTSP quá thời gian cho phép.",
        }), 200

    except Exception as e:
        print("Test camera connection error:", e)

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

@camera_bp.route(
    "/api/admin/cameras/<camera_id>/configure",
    methods=["PUT"]
)
def configure_camera(camera_id):
    classroom_ref = None

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

        classroom_data = classroom_doc.to_dict()

        rtsp_url = classroom_data.get("rtsp_url")

        if not rtsp_url:
            return jsonify({
                "success": False,
                "message": "Phòng học chưa có RTSP URL."
            }), 400


        ffprobe_path = r"D:\Tools\ffmpeg\bin\ffprobe.exe"

        command = [
            ffprobe_path,
            "-v",
            "error",
            "-rtsp_transport",
            "tcp",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            rtsp_url,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:

            classroom_ref.update({
                "status": "offline",
            })

            return jsonify({
                "success": False,
                "connected": False,
                "status": "offline",
                "message": "Không thể kết nối đến RTSP stream.",
            }), 400

        classroom_ref.update({
            "status": "online",
        })

        return jsonify({
            "success": True,
            "connected": True,
            "status": "online",
            "message": "Cấu hình camera thành công.",
            "camera": {
                "camera_id": camera_id,
                "status": "online",
            },
        }), 200

    except subprocess.TimeoutExpired:

        if classroom_ref:
            classroom_ref.update({
                "status": "offline",
            })

        return jsonify({
            "success": False,
            "connected": False,
            "status": "offline",
            "message": "Kiểm tra RTSP quá thời gian cho phép.",
        }), 400

    except Exception as e:

        print("Configure camera error:", e)

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