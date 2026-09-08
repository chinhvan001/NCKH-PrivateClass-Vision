import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore


cred = credentials.Certificate(
    "serviceAccountKey.json"
)

firebase_admin.initialize_app(cred)


db = firestore.client()


# Firebase Web API Key
FIREBASE_API_KEY = "AIzaSyB7ullSbw5n1eXZle07cZRTrV8V26H2NoU"


print("Firebase Admin SDK initialized successfully!")
print("Firestore connected successfully!")