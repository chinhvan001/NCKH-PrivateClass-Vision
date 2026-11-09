from google.cloud import firestore
from firebase_admin import firestore as admin_firestore
from repositories.student_repository import StudentRepository

db = admin_firestore.client()

class ReportRepository:
    @staticmethod
    def get_all_reports():
        """Lấy danh sách tất cả học sinh và ánh xạ giáo viên, môn học tối ưu hóa không gây quá tải Firebase"""
        try:
            reports = []
            
            # 1. Tải trước toàn bộ bảng Teachers và Sessions vào bộ nhớ RAM để tra cứu cục bộ (tránh query lặp lại gây quá tải Firebase)
            teachers_map = {}
            try:
                for t_doc in db.collection('teachers').stream():
                    t_data = t_doc.to_dict() or {}
                    teachers_map[t_doc.id] = t_data.get('full_name') or t_data.get('name') or 'Giáo viên'
            except Exception:
                pass

            sessions_map = {}
            try:
                for s_doc in db.collection('sessions').stream():
                    s_data = s_doc.to_dict() or {}
                    sessions_map[s_doc.id] = s_data
            except Exception:
                pass

            # 2. Lấy danh sách học sinh toàn trường
            raw_students = StudentRepository.get_all_students()

            for student in raw_students:
                student_id = student.get('id')
                student_name = student.get('full_name', 'Chưa rõ')
                
                class_id, current_class_name = StudentRepository.get_current_class_id_and_name(student_id)
                if not current_class_name or current_class_name in ['Chưa rõ', '']:
                    current_class_name = 'Chưa phân lớp'

                # 3. Truy vấn sub-collection student_note của học sinh
                notes_ref = db.collection('students2').document(student_id).collection('student_note').stream()
                notes_list = list(notes_ref)

                if not notes_list:
                    reports.append({
                        "id": None,
                        "student_id": student_id,
                        "student_name": student_name,
                        "class_id": class_id,
                        "current_class": current_class_name,
                        "teacher_name": "---",
                        "subject": "---",
                        "content": "Chưa có nhận xét",
                        "has_note": False,
                        "type": "student_note"
                    })
                else:
                    for note in notes_list:
                        n_data = note.to_dict() or {}
                        session_id = n_data.get('session_id')
                        
                        subject_val = '---'
                        teacher_name_val = 'Giáo viên'
                        
                        # Tra cứu nhanh qua Map đã lưu sẵn trên RAM
                        if session_id and session_id in sessions_map:
                            s_data = sessions_map[session_id]
                            subject_val = s_data.get('subject') or s_data.get('ten_mon', '---')
                            
                            teacher_id = s_data.get('teacher_id') or s_data.get(' giáo_vien_id ')
                            if not teacher_id:
                                teacher_id = n_data.get('created_by')
                                
                            if teacher_id:
                                clean_teacher_id = str(teacher_id).strip()
                                if clean_teacher_id in teachers_map:
                                    teacher_name_val = teachers_map[clean_teacher_id]
                        
                        # Fallback lấy trực tiếp từ created_by nếu chưa có tên giáo viên
                        if teacher_name_val == 'Giáo viên' and n_data.get('created_by'):
                            clean_teacher_id = str(n_data.get('created_by')).strip()
                            if clean_teacher_id in teachers_map:
                                teacher_name_val = teachers_map[clean_teacher_id]

                        reports.append({
                            "id": note.id,
                            "student_id": student_id,
                            "student_name": student_name,
                            "class_id": class_id,
                            "current_class": current_class_name,
                            "teacher_name": teacher_name_val,
                            "subject": subject_val,
                            "content": n_data.get('content') or n_data.get('thrilled', '---'),
                            "created_at": n_data.get('created_at'),
                            "has_note": True,
                            "type": "student_note"
                        })

            # 4. Truy vấn Báo cáo hệ thống (system_issues)
            try:
                for issue in db.collection('system_issues').stream():
                    i_data = issue.to_dict() or {}
                    reports.append({
                        "id": issue.id,
                        "student_id": i_data.get('sender_id', ''),
                        "student_name": i_data.get('sender_name', 'Hệ thống'),
                        "class_id": '',
                        "current_class": 'Toàn hệ thống',
                        "teacher_name": i_data.get('reporter', 'Giáo viên/Phụ huynh'),
                        "subject": i_data.get('issue_type', 'Sự cố'),
                        "content": i_data.get('content', ''),
                        "has_note": True,
                        "type": "system_issue"
                    })
            except Exception:
                pass

            # 5. Truy vấn Ý kiến đóng góp (user_feedbacks)
            try:
                for fb in db.collection('user_feedbacks').stream():
                    f_data = fb.to_dict() or {}
                    reports.append({
                        "id": fb.id,
                        "student_id": f_data.get('user_id', ''),
                        "student_name": f_data.get('user_name', 'Người dùng'),
                        "class_id": '',
                        "current_class": 'Đóng góp',
                        "teacher_name": f_data.get('role', 'Phụ huynh'),
                        "subject": f_data.get('topic', 'Góp ý'),
                        "content": f_data.get('content', ''),
                        "has_note": True,
                        "type": "user_feedback"
                    })
            except Exception:
                pass

            return reports
        except Exception as e:
            print(f"Error fetching all reports: {e}")
            return []

    @staticmethod
    def create_report(student_id, report_data):
        timestamp = firestore.SERVER_TIMESTAMP
        report_data['created_at'] = timestamp
        ref = db.collection('students2').document(student_id).collection('student_note').document()
        ref.set(report_data)
        return ref.id

    @staticmethod
    def update_report(student_id, report_id, report_data):
        doc_ref = db.collection('students2').document(student_id).collection('student_note').document(report_id)
        if not doc_ref.get().exists:
            return False
        report_data['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.update(report_data)
        return True

    @staticmethod
    def delete_report(student_id, report_id):
        doc_ref = db.collection('students2').document(student_id).collection('student_note').document(report_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True