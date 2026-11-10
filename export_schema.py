import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from google.cloud.firestore_v1.document import DocumentReference

# 1. Khởi tạo Firebase Admin
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def parse_val(v):
    if isinstance(v, DatetimeWithNanoseconds):
        return f"Timestamp ({v.isoformat()})"
    elif isinstance(v, DocumentReference):
        return f"DocumentReference -> {v.path}"
    elif isinstance(v, dict):
        # Duyệt đệ quy toàn bộ key bên trong Map (như seatmap, monitored_student)
        return {k: parse_val(val) for k, val in v.items()}
    elif isinstance(v, list):
        if not v:
            return ["Empty_List"]
        # Nếu là mảng các Map, gộp tất cả keys từ các object mẫu để tránh sót trường
        if isinstance(v[0], dict):
            merged_dict = {}
            for item in v:
                if isinstance(item, dict):
                    for k, val in item.items():
                        if k not in merged_dict:
                            merged_dict[k] = parse_val(val)
            return [merged_dict]
        return [f"{type(v[0]).__name__} (vd: {v[0]})"]
    else:
        return f"{type(v).__name__} (vd: {v})"

def export_schema():
    # Đảm bảo thư mục doc tồn tại
    os.makedirs("doc", exist_ok=True)
    
    collections = db.collections()
    schema = {}

    for col in collections:
        col_name = col.id
        schema[col_name] = {
            "type": "Collection",
            "sample_doc_ids": [],
            "fields": {}
        }
        
        # Quét 3-5 documents mẫu để gom đủ các trường (phòng trường hợp doc đầu bị thiếu field)
        docs = list(col.limit(5).stream())
        if not docs:
            schema[col_name]["status"] = "Collection rỗng"
            continue

        for doc in docs:
            schema[col_name]["sample_doc_ids"].append(doc.id)
            data = doc.to_dict()
            for k, v in data.items():
                # Nếu trường chưa có hoặc trường cũ đang là None, cập nhật giá trị mới
                if k not in schema[col_name]["fields"]:
                    schema[col_name]["fields"][k] = parse_val(v)

    output_path = "doc/firestore_schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"-> Xuất schema thành công ra file: {output_path}")

if __name__ == "__main__":
    export_schema()