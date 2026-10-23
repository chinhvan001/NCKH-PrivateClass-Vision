"""Backend chạy trên FakeFirestore của camera-ai: không cần firebase_admin thật, credential hay mạng.

firebase_admin và dotenv luôn được thay bằng module giả trước khi import backend, kể cả khi máy có
SDK thật, để test không bao giờ ghi vào project Firebase thật.
"""

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "camera-ai"), str(ROOT / "camera-ai" / "tests")]

import fake_firestore  # noqa: E402

DB = fake_firestore.FakeFirestore()
TOKENS = {}  # Firebase ID token -> token đã giải mã


def _verify_id_token(token):
    if token not in TOKENS:
        raise ValueError("Invalid ID token.")
    return TOKENS[token]


def _module(name, **attributes):
    module = types.ModuleType(name)
    module.__dict__.update(attributes)
    sys.modules[name] = module
    return module


_firebase_admin = _module("firebase_admin", get_app=lambda *args: None, initialize_app=lambda *args, **kwargs: None)
_firebase_admin.firestore = _module(
    "firebase_admin.firestore",
    client=lambda app=None: DB,
    SERVER_TIMESTAMP=fake_firestore.SERVER_TIMESTAMP,
    DELETE_FIELD=fake_firestore.DELETE_FIELD,
    Query=types.SimpleNamespace(ASCENDING="ASCENDING", DESCENDING="DESCENDING"),
)
_firebase_admin.credentials = _module("firebase_admin.credentials", Certificate=lambda path: None)
_firebase_admin.auth = _module("firebase_admin.auth", verify_id_token=_verify_id_token)
_module("dotenv", load_dotenv=lambda *args, **kwargs: None)


@pytest.fixture
def db():
    DB.__init__()  # giữ nguyên object: các module backend đã giữ tham chiếu tới nó
    TOKENS.clear()
    return DB


@pytest.fixture
def client(db):
    from app import app

    app.testing = True
    return app.test_client()


@pytest.fixture
def admin(db):
    """Header Authorization của admin admins/admin-1 đã đăng nhập."""
    db.document("admins/admin-1").set({"email": "admin@example.com", "is_active": True})
    TOKENS["admin-token"] = {"uid": "admin-1"}
    return {"Authorization": "Bearer admin-token"}
