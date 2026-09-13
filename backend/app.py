from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.camera_routes import camera_bp


app = Flask(__name__)

CORS(app)


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(camera_bp)


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