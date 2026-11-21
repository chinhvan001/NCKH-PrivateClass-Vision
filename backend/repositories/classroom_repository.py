from firebase_config import db

class ClassroomRepository:
    @staticmethod
    def get_all_classrooms():
        docs = db.collection("classrooms").stream()
        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        return results

    @staticmethod
    def get_classroom_by_id(classroom_id):
        if not classroom_id:
            return None
        doc = db.collection("classrooms").document(str(classroom_id).strip()).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    @staticmethod
    def find_by_name(classroom_name):
        if not classroom_name:
            return []
        docs = db.collection("classrooms").where("classroom_name", "==", classroom_name).stream()
        results = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        return results

    @staticmethod
    def check_id_exists(classroom_id):
        if not classroom_id:
            return False
        return db.collection("classrooms").document(str(classroom_id).strip()).get().exists

    @staticmethod
    def create_classroom(classroom_data, classroom_id=None):
        if classroom_id:
            ref = db.collection("classrooms").document(classroom_id)
            ref.set(classroom_data)
        else:
            ref = db.collection("classrooms").document()
            ref.set(classroom_data)
        doc = ref.get()
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    @staticmethod
    def update_classroom(classroom_id, classroom_data):
        ref = db.collection("classrooms").document(classroom_id)
        ref.update(classroom_data)
        doc = ref.get()
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    @staticmethod
    def delete_classroom(classroom_id):
        db.collection("classrooms").document(classroom_id).delete()

    @staticmethod
    def is_classroom_linked(classroom_id):
        classes_ref = db.collection("classes").where("classroom_id", "==", classroom_id).limit(1).stream()
        return next(classes_ref, None) is not None
