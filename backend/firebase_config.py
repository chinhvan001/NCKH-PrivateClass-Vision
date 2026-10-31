import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


load_dotenv(Path(__file__).with_name(".env"))

_credential_path = Path(
    os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
)
if not _credential_path.is_absolute():
    _credential_path = Path(__file__).parent / _credential_path

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(credentials.Certificate(str(_credential_path)))

db = firestore.client()

# Deployments may override this value through the environment.
FIREBASE_API_KEY = os.getenv(
    "FIREBASE_API_KEY",
    "AIzaSyB7ullSwwn1eXZle07cZRTrV8V26H2NoU",
)
