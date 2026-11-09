import time
from threading import Lock
from firebase_admin import firestore
from firebase_config import db

class ClassRepository:
    _teacher_cache = {}
    _student_cache = {}
    _cache_lock = Lock()
    _CACHE_TTL = 60  # seconds

    @classmethod
    def get_teacher_info(cls, teacher_id):
        if not teacher_id:
            return None
        current_time = time.time()
        with cls._cache_lock:
            cached = cls._teacher_cache.get(teacher_id)
            if cached and current_time < cached[1]:
                return cached[0]

        teacher_doc = db.collection("teachers").document(teacher_id).get()
        if teacher_doc.exists:
            info = teacher_doc.to_dict() or {}
            with cls._cache_lock:
                cls._teacher_cache[teacher_id] = (info, current_time + cls._CACHE_TTL)
            return info

        user_doc = db.collection("users").document(teacher_id).get()
        if user_doc.exists:
            info = user_doc.to_dict() or {}
            with cls._cache_lock:
                cls._teacher_cache[teacher_id] = (info, current_time + cls._CACHE_TTL)
            return info

        with cls._cache_lock:
            cls._teacher_cache[teacher_id] = (None, current_time + cls._CACHE_TTL)
        return None

    @classmethod
    def teacher_exists(cls, teacher_id):
        return cls.get_teacher_info(teacher_id) is not None

    @classmethod
    def get_teacher_name(cls, teacher_id):
        if not teacher_id:
            return "Chưa có giáo viên"
        teacher = cls.get_teacher_info(teacher_id)
        if teacher:
            return (
                teacher.get("full_name")
                or teacher.get("display_name")
                or teacher.get("name")
                or teacher.get("email")
                or "Chưa có giáo viên"
            )
        return "Chưa có giáo viên"

    @classmethod
    def get_student_by_id(cls, student_id):
        if not student_id:
            return None
        current_time = time.time()
        with cls._cache_lock:
            cached = cls._student_cache.get(student_id)
            if cached and current_time < cached[1]:
                return cached[0]

        student_doc = db.collection("students2").document(student_id).get()
        if student_doc.exists:
            data = student_doc.to_dict() or {}
            data["id"] = student_doc.id
            with cls._cache_lock:
                cls._student_cache[student_id] = (data, current_time + cls._CACHE_TTL)
            return data

        with cls._cache_lock:
            cls._student_cache[student_id] = (None, current_time + cls._CACHE_TTL)
        return None

    @classmethod
    def invalidate_teacher_cache(cls, teacher_id=None):
        with cls._cache_lock:
            if teacher_id:
                cls._teacher_cache.pop(teacher_id, None)
            else:
                cls._teacher_cache.clear()

    @classmethod
    def invalidate_student_cache(cls, student_id=None):
        with cls._cache_lock:
            if student_id:
                cls._student_cache.pop(student_id, None)
            else:
                cls._student_cache.clear()

    @staticmethod
    def get_classes(filters=None):
        query = db.collection("classes2")
        if filters:
            for field in ("status", "teacher_id", "school_year"):
                val = filters.get(field)
                if val:
                    query = query.where(field, "==", val)
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append((doc.id, data))
        return results

    @staticmethod
    def get_class_by_id(class_id):
        if not class_id:
            return None, None
        ref = db.collection("classes2").document(class_id)
        doc = ref.get()
        if not doc.exists:
            return None, None
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return ref, data

    @staticmethod
    def find_by_name(class_name):
        duplicate = db.collection("classes2").where("class_name", "==", class_name).limit(1).stream()
        return next(duplicate, None)

    @staticmethod
    def create_class(class_data):
        ref = db.collection("classes2").document()
        class_data["created_at"] = firestore.SERVER_TIMESTAMP
        class_data["updated_at"] = firestore.SERVER_TIMESTAMP
        ref.set(class_data)
        doc = ref.get()
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return ref.id, data

    @staticmethod
    def update_class(class_id, update_data):
        ref = db.collection("classes2").document(class_id)
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP
        ref.update(update_data)
        doc = ref.get()
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    @staticmethod
    def update_seat_map(class_id, seat_map):
        ref = db.collection("classes2").document(class_id)
        ref.update({
            "seat_map": seat_map,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    @staticmethod
    def soft_delete_class(class_id):
        ref = db.collection("classes2").document(class_id)
        ref.update({
            "status": "inactive",
            "updated_at": firestore.SERVER_TIMESTAMP
        })

    @staticmethod
    def get_class_members(class_id):
        docs = db.collection("class_members").where("class_id", "==", class_id).stream()
        members = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            members.append(data)
        return members
