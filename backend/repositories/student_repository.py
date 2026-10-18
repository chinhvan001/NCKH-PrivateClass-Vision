from google.cloud import firestore
from firebase_admin import firestore as admin_firestore

db = admin_firestore.client()

class StudentRepository:
    @staticmethod
    def get_all_students(filters=None):
        try:
            ref = db.collection('students2')
            docs = ref.stream()
            students = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                students.append(data)
            return students
        except Exception as e:
            print(f"Error fetching students: {e}")
            return []

    @staticmethod
    def get_all_classes():
        try:
            classes = []
            for col in ['classes2', 'classes', 'classrooms']:
                docs = db.collection(col).stream()
                for d in docs:
                    c_data = d.to_dict() or {}
                    classes.append({
                        "id": d.id,
                        "name": c_data.get("name") or c_data.get("class_name") or "Lớp học"
                    })
                if classes:
                    break
            return classes
        except Exception:
            return []

    @staticmethod
    def get_student_by_id(student_id):
        doc = db.collection('students2').document(student_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = doc.id
        
        try:
            notes_ref = db.collection('students2').document(student_id).collection('student_note').stream()
            notes = [n.to_dict() for n in notes_ref]
            data['notes'] = notes
        except Exception:
            data['notes'] = []
            
        return data

    @staticmethod
    def create_student(student_data):
        timestamp = firestore.SERVER_TIMESTAMP
        class_id = student_data.pop('class_id', None)
        
        student_data['created_at'] = timestamp
        student_data['updated_at'] = timestamp
        if 'is_active' not in student_data:
            student_data['is_active'] = True
            
        ref = db.collection('students2').document()
        ref.set(student_data)
        student_id = ref.id

        if class_id:
            db.collection('class_members').add({
                'student_id': student_id,
                'class_id': class_id,
                'status': 'active',
                'assigned_at': timestamp
            })

        return student_id

    @staticmethod
    def update_student(student_id, student_data):
        timestamp = firestore.SERVER_TIMESTAMP
        class_id = student_data.pop('class_id', None)
        
        status_val = student_data.pop('status', None)
        if status_val is not None:
            if status_val == "Đang học":
                student_data['is_active'] = True
            elif status_val == "Tạm nghỉ":
                student_data['is_active'] = 'paused'
            elif status_val == "Đã thôi học":
                student_data['is_active'] = False

        student_data['updated_at'] = timestamp
        
        doc_ref = db.collection('students2').document(student_id)
        if not doc_ref.get().exists:
            return False
            
        doc_ref.update(student_data)

        if class_id is not None:
            members_ref = db.collection('class_members').where('student_id', '==', student_id).stream()
            updated = False
            for m in members_ref:
                db.collection('class_members').document(m.id).update({
                    'class_id': class_id,
                    'status': 'active',
                    'updated_at': timestamp
                })
                updated = True
            if not updated and class_id:
                db.collection('class_members').add({
                    'student_id': student_id,
                    'class_id': class_id,
                    'status': 'active',
                    'assigned_at': timestamp
                })

        return True

    @staticmethod
    def delete_student(student_id, soft_delete=True):
        doc_ref = db.collection('students2').document(student_id)
        if not doc_ref.get().exists:
            return False
        if soft_delete:
            doc_ref.update({
                'is_active': False,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        else:
            doc_ref.delete()
        return True

    @staticmethod
    def get_current_class_id_and_name(student_id):
        try:
            for col in ['classes2', 'classes', 'classrooms']:
                docs = db.collection(col).stream()
                for d in docs:
                    c_data = d.to_dict() or {}
                    seat_map = c_data.get('seat_map', {})
                    if isinstance(seat_map, dict):
                        for seat_key, seat_val in seat_map.items():
                            if isinstance(seat_val, dict) and seat_val.get('student_id') == student_id:
                                c_name = c_data.get('name') or c_data.get('class_name', 'Chưa rõ')
                                return d.id, c_name

            members = db.collection('class_members').where('student_id', '==', student_id).stream()
            for m in members:
                m_data = m.to_dict()
                if m_data.get('status') == 'active':
                    class_id = m_data.get('class_id')
                    if class_id:
                        class_doc = db.collection('classes2').document(class_id).get()
                        if class_doc.exists:
                            c_data = class_doc.to_dict()
                            return class_id, c_data.get('name') or c_data.get('class_name', 'Chưa rõ')
        except Exception as e:
            print(f"Error getting class for student {student_id}: {e}")
        return '', 'Chưa phân lớp'