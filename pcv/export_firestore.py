import firebase_admin
from firebase_admin import credentials, firestore
import json

# Dùng service account key - tải từ Firebase Console
# Project Settings > Service accounts > Generate new private key
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Danh sách collection cần export
collections = [
    "students",
    "monitoring_sessions", 
    "supervised_students",
    "parents",
    "enrollments",
    "classes",
    "classrooms",
    "teachers",
]

result = {}

for col_name in collections:
    print(f"Đang export {col_name}...")
    docs = db.collection(col_name).stream()
    result[col_name] = {}
    for doc in docs:
        result[col_name][doc.id] = doc.to_dict()

# Lưu ra file JSON
with open("firestore_export.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)

print("✅ Export xong! File: firestore_export.json")
