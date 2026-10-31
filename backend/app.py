import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Nếu chưa có quyền Admin, tự động bật bảng yêu cầu quyền Administrator
if not is_admin():
    # Khởi động lại chính script hiện tại với quyền Administrator
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    except Exception as e:
        print(f"Không thể cấp quyền Admin: {e}")
    sys.exit()

from flask import Flask, jsonify
from flask_cors import CORS


from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.camera_routes import camera_bp
from routes.class_routes import class_bp
from routes.session_routes import session_bp
from routes.classroom_routes import classroom_bp
from routes.evaluation_routes import evaluation_bp
from routes.student_routes import student_bp
from routes.dashboard_routes import dashboard_bp
from routes.ldlplayer_routes import ld_blueprint

app = Flask(__name__)

CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(camera_bp)
app.register_blueprint(class_bp)
app.register_blueprint(session_bp)
app.register_blueprint(classroom_bp)
app.register_blueprint(evaluation_bp)
app.register_blueprint(student_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(ld_blueprint)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "PrivateClass Vision API is running"
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "API endpoint không tồn tại."
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "message": "HTTP method không được hỗ trợ."
    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error."
    }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )