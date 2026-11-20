import time
from threading import Lock
from firebase_config import db

class AuthRepository:
    _admin_cache = {}
    _cache_lock = Lock()
    _CACHE_TTL = 60  # seconds

    @classmethod
    def get_admin_by_uid(cls, uid):
        if not uid:
            return None, None
        uid = str(uid).strip()
        if not uid:
            return None, None

        current_time = time.time()
        with cls._cache_lock:
            cached = cls._admin_cache.get(uid)
            if cached:
                data, expiry = cached
                if current_time < expiry:
                    return uid, data
                del cls._admin_cache[uid]

        try:
            admin_ref = db.collection("admins").document(uid)
            admin_doc = admin_ref.get()
            if not admin_doc.exists:
                return None, None

            admin_data = admin_doc.to_dict() or {}
            with cls._cache_lock:
                cls._admin_cache[uid] = (admin_data, current_time + cls._CACHE_TTL)

            return admin_ref.id, admin_data
        except Exception as error:
            print("AuthRepository get_admin_by_uid error:", error)
            return None, None

    @classmethod
    def invalidate_admin_cache(cls, uid=None):
        with cls._cache_lock:
            if uid:
                cls._admin_cache.pop(uid, None)
            else:
                cls._admin_cache.clear()
