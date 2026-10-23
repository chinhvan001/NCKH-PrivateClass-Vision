from datetime import date, datetime

from flask import jsonify
from firebase_admin import firestore

from firebase_config import db
from utils.auth import (
    get_current_user,
    get_json_body,
    is_admin_user,
    verify_request_token,
)


def require_admin():
    decoded_token = verify_request_token()
    if not decoded_token:
        return None, (jsonify({"success": False, "message": "Unauthorized."}), 401)

    _, user_data = get_current_user(decoded_token)
    if not user_data:
        return None, (jsonify({"success": False, "message": "Tài khoản admin không tồn tại."}), 403)

    if not is_admin_user(user_data):
        return None, (jsonify({"success": False, "message": "Tài khoản admin đã bị vô hiệu hóa."}), 403)

    return decoded_token.get("uid"), None


def json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    return value


def json_document(doc):
    return {"id": doc.id, **json_value(doc.to_dict() or {})}


def get_document(collection_name, document_id):
    ref = db.collection(collection_name).document(document_id)
    doc = ref.get()
    return ref, doc


def required_string(data, field_name):
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        return None, f"{field_name} là bắt buộc."
    return value.strip(), None


def numeric_value(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def server_timestamp():
    return firestore.SERVER_TIMESTAMP


__all__ = [
    "db",
    "get_json_body",
    "get_document",
    "json_document",
    "json_value",
    "numeric_value",
    "required_string",
    "require_admin",
    "server_timestamp",
]