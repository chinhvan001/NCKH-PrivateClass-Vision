from google.cloud import firestore
from firebase_admin import firestore as admin_firestore

db = admin_firestore.client()

class EvaluationRepository:
    @staticmethod
    def get_classes_overview():
        classes_ref = db.collection('classes2').stream()
        classes_data = {c.id: c.to_dict() for c in classes_ref}
        return classes_data

    @staticmethod
    def get_session_results_by_classes(class_ids):
        if not class_ids:
            return []

        session_ids = []
        session_to_class = {} 
        chunk_size = 30

        for i in range(0, len(class_ids), chunk_size):
            chunk = class_ids[i:i + chunk_size]
            sessions_ref = db.collection('sessions').where('class_id', 'in', chunk).stream()
            for s in sessions_ref:
                session_ids.append(s.id)
                session_to_class[s.id] = s.to_dict().get('class_id')

        if not session_ids:
            return []

        results = []
        for i in range(0, len(session_ids), chunk_size):
            chunk = session_ids[i:i + chunk_size]
            docs = db.collection('session_results').where('session_id', 'in', chunk).stream()
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                data['class_id'] = session_to_class.get(data.get('session_id'))
                results.append(data)

        return results

    @staticmethod
    def get_class_detail_data(class_id):
        class_doc = db.collection('classes2').document(class_id).get()
        if not class_doc.exists:
            return None
        class_data = class_doc.to_dict()
        class_data['id'] = class_doc.id

        members_ref = db.collection('class_members').where('class_id', '==', class_id).stream()
        student_ids = []
        member_map = {}
        for m in members_ref:
            m_data = m.to_dict()
            if m_data.get('status') == 'active':
                s_id = m_data.get('student_id')
                if s_id:
                    student_ids.append(s_id)
                    member_map[s_id] = m_data

        students_info = {}
        if student_ids:
            chunk_size = 30
            for i in range(0, len(student_ids), chunk_size):
                chunk = student_ids[i:i + chunk_size]
                s_docs = db.collection('students2').where(firestore.FieldPath.document_id(), 'in', chunk).stream()
                for s_doc in s_docs:
                    students_info[s_doc.id] = s_doc.to_dict()

        sessions_ref = db.collection('sessions').where('class_id', '==', class_id).stream()
        session_ids = [s.id for s in sessions_ref]

        session_results = []
        if session_ids:
            for i in range(0, len(session_ids), chunk_size):
                chunk = session_ids[i:i + chunk_size]
                res_docs = db.collection('session_results').where('session_id', 'in', chunk).stream()
                for r in res_docs:
                    session_results.append(r.to_dict())

        return {
            "class_info": class_data,
            "student_ids": student_ids,
            "students_info": students_info,
            "session_results": session_results
        }

    @staticmethod
    def get_session_by_id(session_id):
        doc = db.collection('sessions').document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def save_session_result(result_data):
        session_id = result_data.get('session_id')
        student_id = result_data.get('student_id')

        existing = EvaluationRepository.get_session_result_by_student(session_id, student_id)
        if existing:
            doc_id = existing['id']
            db.collection('session_results').document(doc_id).update(result_data)
            return doc_id
        else:
            ref = db.collection('session_results').document()
            ref.set(result_data)
            return ref.id

    @staticmethod
    def get_session(session_id):
        doc = db.collection('sessions').document(session_id).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_session_result_by_student(session_id, student_id):
        docs = db.collection('session_results')\
            .where('session_id', '==', session_id)\
            .where('student_id', '==', student_id)\
            .limit(1).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id 
            return data
        return None

    @staticmethod
    def upsert_session_result(doc_id, data):
        if doc_id:
            db.collection('session_results').document(doc_id).set(data, merge=True)
        else:
            db.collection('session_results').add(data)

    @staticmethod
    def get_all_results_for_session(session_id):
        docs = db.collection('session_results').where('session_id', '==', session_id).stream()
        return [doc.to_dict() for doc in docs]
        
    @staticmethod
    def get_student_info(student_id):
        doc = db.collection('students2').document(student_id).get()
        if doc.exists:
            return doc.to_dict()

        doc = db.collection('users').document(student_id).get()
        return doc.to_dict() if doc.exists else {}