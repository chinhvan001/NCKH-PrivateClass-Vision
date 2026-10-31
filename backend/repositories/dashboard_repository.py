from firebase_admin import firestore

class DashboardRepository:
    @staticmethod
    def get_db():
        return firestore.client()

    @classmethod
    def get_all(cls, collection_name):
        try:
            docs = cls.get_db().collection(collection_name).stream()
            return [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]
        except Exception as e:
            print(f"Error fetching {collection_name} in dashboard:", e)
            return []
