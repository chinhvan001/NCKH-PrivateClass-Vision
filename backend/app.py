from flask import Flask, jsonify, request
from flask_cors import CORS

from firebase_admin import auth
from firebase_admin import firestore

import firebase_config


app = Flask(__name__)

CORS(app)

db = firestore.client()

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "PrivateClass Vision API is running"
    })

@app.route("/api/auth/google", methods=['POST'])
def google_login():

    try:

        # authorization = request.headers.get("Authorization")

        # if not authorization:

        #     return jsonify({
        #         "success": False,
        #         "message": "Missing Authorization header"
        #     }), 401


        # if not authorization.startswith("Bearer "):

        #     return jsonify({
        #         "success": False,
        #         "message": "Invalid Authorization header"
        #     }), 401


        # id_token = authorization.split("Bearer ")[1]

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is empty"
            }), 400

        id_token = data.get("idToken")

        if not id_token:
            return jsonify({
                "success": False,
                "message": "Missing Firebase ID Token"
            }), 400


        decoded_token = auth.verify_id_token(id_token)


        uid = decoded_token["uid"]

        # print("================================")
        # print("Decoded Firebase Token:")
        # print(decoded_token)
        # print("================================")

        user_ref = db.collection("users").document(uid)

        user_doc = user_ref.get()

        if not user_doc.exists:
            print("User not found if Firestore: ", uid)

            return jsonify({
                "success": False,
                "message": "Tài khoản chưa được cấp quyền truy cập"
            }), 403

        user_data = user_doc.to_dict()

        print("Firestore user: ", user_data)


        role = user_data.get("role")

        if role != "admin":
            return jsonify({
                "status": False,
                "message": "Tài khoản không có quyền Admin",
                "role": role
            }), 403

        is_active = user_data.get("is_active")

        if is_active is False:
            return jsonify({
                "status": False,
                "message": "Tài khoản đã bị vô hiệu hóa"
            }), 403


        # uid = decoded_token.get("uid")
        # email = decoded_token.get("email")
        # name = decoded_token.get("name")


        # print("================================")
        # print("Google Login Successful")
        # print("UID:", uid)
        # print("Email:", email)
        # print("Name:", name)
        # print("================================")

        # users_ref = db.collection("users")

        # return jsonify({

        #     "success": True,

        #     "message": "Google login successful",

        #     "user": {
        #         "uid": uid,
        #         "email": email,
        #         "name": name
        #     }

        # }), 200

        return jsonify({
            "success": True,
            "message": "Admin login successful",
            "user": {
                "uid": uid,
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "role": user_data.get("role"),
                "is_active": user_data.get("is_active", True)
            }
        }), 200

    except Exception as error: 

        print("Google login error: ", error)

        return jsonify({

            "success": False,
            "message": "Google authentication failed"

        }), 401

# @app.route("/test-firestore", methods=['GET'])
# def test_firestore():

#     doc_ref = db.collection("test").document("connection")

#     doc_ref.set({
#         "message": "Flask connected to Firestore",
#         "status": "success"
#     })

#     return jsonify({
#         "message": "Firestore connection successful"
#     })


@app.route("/api/admin/users", methods=["GET"])
def get_admin_users():
    try:
        # =========================
        # 1. Lấy Authorization
        # =========================
        authorization = request.headers.get("Authorization")

        if not authorization:
            return jsonify({
                "success": False,
                "message": "Missing authorization header"
            }), 401

        if not authorization.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Invalid Authorization header"
            }), 401

        # =========================
        # 2. Lấy Firebase ID Token
        # =========================
        id_token = authorization.split("Bearer ", 1)[1]

        decoded_token = auth.verify_id_token(id_token)

        uid = decoded_token["uid"]

        # =========================
        # 3. Lấy tài khoản hiện tại
        # =========================
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                "success": False,
                "message": "Tài khoản không tồn tại"
            }), 403

        current_user = user_doc.to_dict()

        # =========================
        # 4. Kiểm tra quyền Admin
        # =========================
        current_role = current_user.get("role")

        if current_role not in ["admin", "super_admin"]:
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền quản lý tài khoản giáo viên"
            }), 403

        # =========================
        # 5. Kiểm tra tài khoản
        # =========================
        if current_user.get("is_active") is False:
            return jsonify({
                "success": False,
                "message": "Tài khoản đã bị vô hiệu hóa"
            }), 403

        # =========================
        # 6. Lấy tất cả teacher
        # =========================
        docs = db.collection("users").stream()

        users = []

        for doc in docs:
            user_data = doc.to_dict()

            # Chỉ lấy teacher
            if user_data.get("role") != "teacher":
                continue

            users.append({
                "id": doc.id,
                "uid": user_data.get("uid", doc.id),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "phone_number": user_data.get("phone_number"),
                "role": user_data.get("role"),
                "is_active": user_data.get("is_active", True),
                "subject": user_data.get("subject", []),
            })

        return jsonify({
            "success": True,
            "users": users,
            "total": len(users)
        }), 200

    except Exception as error:
        print("Get admin users error:", error)

        return jsonify({
            "success": False,
            "message": "Không thể lấy danh sách tài khoản giáo viên"
        }), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )