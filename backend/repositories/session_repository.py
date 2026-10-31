from firebase_admin import firestore
from routes.test_helpers import db, server_timestamp

class SessionRepository:
    @staticmethod
    def get_all_sessions():
        return [
            {"id": doc.id, **(doc.to_dict() or {})}
            for doc in db.collection("sessions").stream()
        ]

    @staticmethod
    def get_all_classes():
        return [
            {"id": doc.id, **(doc.to_dict() or {})}
            for doc in db.collection("classes2").stream()
        ]

    @staticmethod
    def get_all_teachers():
        teachers = []
        for col_name in ["teachers", "users"]:
            try:
                docs = db.collection(col_name).stream()
                for doc in docs:
                    data = doc.to_dict() or {}
                    teachers.append({
                        "id": doc.id,
                        "name": data.get("full_name") or data.get("name") or data.get("email") or doc.id,
                        "subject": data.get("subject") or data.get("subjects") or ""
                    })
                if teachers:
                    break
            except Exception:
                pass
        return teachers

    @staticmethod
    def get_all_rooms():
        rooms_set = set()
        try:
            for doc in db.collection("sessions").stream():
                room = doc.to_dict().get("room")
                if room:
                    rooms_set.add(room)
            for doc in db.collection("classes2").stream():
                room = doc.to_dict().get("room") or doc.to_dict().get("name")
                if room:
                    rooms_set.add(room)
        except Exception:
            pass
        
        if not rooms_set:
            rooms_set = {"301", "302", "303", "401", "402", "Lab 1", "Lab 2"}
            
        return [{"id": r, "name": r} for r in sorted(rooms_set)]

    @staticmethod
    def get_session_by_id(session_id):
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        return doc_ref, doc

    @staticmethod
    def create_batch_sessions(sessions_payloads):
        batch = db.batch()
        created_ids = []
        for payload in sessions_payloads:
            doc_ref = db.collection("sessions").document()
            payload["created_at"] = server_timestamp()
            payload["status"] = "scheduled"
            batch.set(doc_ref, payload)
            created_ids.append(doc_ref.id)
        batch.commit()
        return created_ids

    @staticmethod
    def get_class_exists(class_id):
        return db.collection("classes2").document(class_id).get().exists

    @staticmethod
    def get_teacher_exists(teacher_id):
        return (
            db.collection("teachers").document(teacher_id).get().exists or
            db.collection("users").document(teacher_id).get().exists
        )