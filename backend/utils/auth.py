from flask import request
from firebase_admin import auth

from firebase_config import db


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


def find_admin_by_uid(uid):

    if not uid:
        return None, None

    uid = str(uid).strip()

    if not uid:
        return None, None

    try:
        admin_ref = db.collection("admins").document(uid)
        admin_doc = admin_ref.get()

        if not admin_doc.exists:
            return None, None

        return admin_ref, admin_doc.to_dict()

    except Exception as error:
        print("Find admin by UID error:", error)
        return None, None


def get_current_user(decoded_token):

    if not decoded_token:
        return None, None

    uid = decoded_token.get("uid", "")

    if not uid:
        return None, None

    return find_admin_by_uid(uid)


def is_admin_user(user_data):

    if not user_data:
        return False

    is_active = user_data.get("is_active", True)

    return is_active is not False


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