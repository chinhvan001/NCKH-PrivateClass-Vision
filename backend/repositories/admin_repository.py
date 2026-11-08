from firebase_admin import auth
from firebase_config import db

class AdminRepository:
    @staticmethod
    def get_all_teachers():
        docs = db.collection("teachers").stream()
        teachers = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            teachers.append(data)
        return teachers

    @staticmethod
    def get_teacher_by_id(teacher_id):
        if not teacher_id:
            return None, None
        ref = db.collection("teachers").document(teacher_id)
        doc = ref.get()
        if not doc.exists:
            return None, None
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return ref, data

    @staticmethod
    def find_teacher_by_email(email):
        if not email:
            return None
        existing_teachers = (
            db.collection("teachers")
            .where("email", "==", email)
            .limit(1)
            .stream()
        )
        return next(existing_teachers, None)

    @staticmethod
    def create_teacher(teacher_data):
        doc_ref = db.collection("teachers").document()
        doc_ref.set(teacher_data)
        return doc_ref.id

    @staticmethod
    def update_teacher(teacher_id, update_data):
        ref = db.collection("teachers").document(teacher_id)
        ref.update(update_data)

    @staticmethod
    def delete_teacher(teacher_id, firebase_uid=None):
        if firebase_uid:
            try:
                auth.delete_user(firebase_uid)
            except auth.UserNotFoundError:
                pass
        db.collection("teachers").document(teacher_id).delete()

    @staticmethod
    def get_admin_by_uid(uid):
        if not uid:
            return None, None
        ref = db.collection("admins").document(uid)
        doc = ref.get()
        if not doc.exists:
            return None, None
        data = doc.to_dict() or {}
        return ref, data

    @staticmethod
    def update_admin_profile(uid, update_data):
        ref = db.collection("admins").document(uid)
        ref.update(update_data)

    @staticmethod
    def update_admin_password(uid, new_password):
        auth.update_user(uid, password=new_password)
