from repositories.student_repository import StudentRepository

class StudentService:
    @staticmethod
    def get_students_overview(query_params):
        raw_students = StudentRepository.get_all_students()
        
        total = len(raw_students)
        active_count = sum(1 for s in raw_students if s.get('is_active') is True)
        paused_count = sum(1 for s in raw_students if s.get('is_active') == 'paused')
        dropped_count = sum(1 for s in raw_students if s.get('is_active') is False)

        result_list = []
        for s in raw_students:
            student_id = s.get('id')
            class_id, current_class = StudentRepository.get_current_class_id_and_name(student_id)
            
            is_active = s.get('is_active', True)
            if is_active is True:
                status_str = "Đang học"
            elif is_active == 'paused':
                status_str = "Tạm nghỉ"
            else:
                status_str = "Đã thôi học"

            result_list.append({
                "id": student_id,
                "full_name": s.get('full_name', ''),
                "birthday": s.get('birthday'),
                "gender": "Nam" if s.get('gender') in ['male', 'Nam'] else "Nữ",
                "class_id": class_id,
                "current_class": current_class,
                "status": status_str,
                "phone_number": s.get('parent_phonenumber', ''),
                "parent_name": s.get('parent_name', 'Chưa cập nhật')
            })

        classes = StudentRepository.get_all_classes()

        return {
            "success": True,
            "stats": {
                "total": total,
                "active": active_count,
                "paused": paused_count,
                "dropped": dropped_count
            },
            "classes": classes,
            "data": result_list
        }

    @staticmethod
    def get_student_detail(student_id):
        student = StudentRepository.get_student_by_id(student_id)
        if not student:
            return {"success": False, "error": "Không tìm thấy học sinh"}
        
        class_id, current_class = StudentRepository.get_current_class_id_and_name(student_id)
        student['class_id'] = class_id
        student['current_class'] = current_class

        gender_val = student.get('gender')
        student['gender'] = "Nam" if gender_val in ['male', 'Nam'] else "Nữ"
        
        return {"success": True, "data": student}

    @staticmethod
    def create_student(data):
        if not data.get('full_name'):
            return {"success": False, "error": "Họ và tên không được để trống"}
        new_id = StudentRepository.create_student(data)
        return {"success": True, "id": new_id, "message": "Thêm học sinh thành công"}

    @staticmethod
    def update_student(student_id, data):
        success = StudentRepository.update_student(student_id, data)
        if not success:
            return {"success": False, "error": "Cập nhật thất bại hoặc không tìm thấy học sinh"}
        return {"success": True, "message": "Cập nhật thành công"}

    @staticmethod
    def delete_student(student_id):
        success = StudentRepository.delete_student(student_id, soft_delete=True)
        if not success:
            return {"success": False, "error": "Xóa học sinh thất bại"}
        return {"success": True, "message": "Đã chuyển trạng thái học sinh thành thôi học"}