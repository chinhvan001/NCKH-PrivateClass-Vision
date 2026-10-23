from firebase_admin import firestore

class DashboardRepository:
    @staticmethod
    def get_db():
        return firestore.client()

    @classmethod
    def get_all_teachers(cls):
        db = cls.get_db()
        try:
            docs = db.collection("teachers").stream()
            return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]
        except Exception as e:
            print("Error fetching teachers in dashboard:", e)
            return []

    @classmethod
    def get_all_classes(cls):
        db = cls.get_db()
        try:
            docs = db.collection("classes2").stream()
            return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]
        except Exception as e:
            print("Error fetching classes in dashboard:", e)
            return []

    @classmethod
    def get_all_sessions(cls):
        db = cls.get_db()
        try:
            docs = db.collection("sessions").stream()
            return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]
        except Exception as e:
            print("Error fetching sessions in dashboard:", e)
            return []