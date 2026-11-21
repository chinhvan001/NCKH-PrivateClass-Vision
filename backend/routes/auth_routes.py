from flask import Blueprint, jsonify
from utils.auth import get_json_body
from services.auth_service import AuthService

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/api/auth/google", methods=["POST"])
def google_login():
    data = get_json_body()
    id_token = data.get("idToken")
    result, status_code = AuthService.google_login(id_token)
    return jsonify(result), status_code

@auth_bp.route("/api/auth/email-password", methods=["POST"])
def email_password_login():
    data = get_json_body()
    email = data.get("email")
    password = data.get("password")
    result, status_code = AuthService.email_password_login(email, password)
    return jsonify(result), status_code
