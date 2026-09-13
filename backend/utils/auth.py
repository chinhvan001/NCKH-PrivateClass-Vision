from flask import request
from firebase_admin import auth

from firebase_config import db


ADMIN_ROLES = {"admin", "super_admin"}
TEACHER_ROLE = "teacher"


def verify_request_token():
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    id_token = authorization.split("Bearer ", 1)[1].strip()

    if not id_token:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token

    except Exception as error:
        print("Token verification error:", error)
        return None


def get_current_user(decoded_token):
    if not decoded_token:
        return None, None

    uid = decoded_token.get("uid")

    if not uid:
        return None, None

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return None, None

    return user_ref, user_doc.to_dict()


def is_admin_user(user_data):
    if not user_data:
        return False

    role = user_data.get("role")
    is_active = user_data.get("is_active", True)

    return (
        role in ADMIN_ROLES
        and is_active is not False
    )


def get_json_body():
    return request.get_json(silent=True) or {}


def normalize_subjects(subjects):
    if subjects is None:
        return []

    if not isinstance(subjects, list):
        return None

    return [
        str(subject).strip()
        for subject in subjects
        if str(subject).strip()
    ]
