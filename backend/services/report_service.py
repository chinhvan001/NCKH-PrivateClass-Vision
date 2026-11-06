from repositories.report_repository import ReportRepository

class ReportService:
    @staticmethod
    def get_reports_overview(query_params):
        raw_reports = ReportRepository.get_all_reports()
        
        total = len(raw_reports)
        # Thống kê theo môn học
        subject_stats = {}
        for r in raw_reports:
            subj = r.get('subject', 'Khác')
            subject_stats[subj] = subject_stats.get(subj, 0) + 1

        return {
            "success": True,
            "stats": {
                "total": total,
                "subjects": subject_stats
            },
            "data": raw_reports
        }

    @staticmethod
    def create_report(data):
        student_id = data.get('student_id')
        content = data.get('content')
        if not student_id or not content:
            return {"success": False, "error": "Thiếu học sinh hoặc nội dung báo cáo"}
            
        report_data = {
            "content": content,
            "session_id": data.get('session_id', ''),
            "created_by": data.get('teacher_id', '')
        }
        
        new_id = ReportRepository.create_report(student_id, report_data)
        return {"success": True, "id": new_id, "message": "Tạo báo cáo thành công"}

    @staticmethod
    def update_report(student_id, report_id, data):
        success = ReportRepository.update_report(student_id, report_id, data)
        if not success:
            return {"success": False, "error": "Cập nhật báo cáo thất bại"}
        return {"success": True, "message": "Cập nhật báo cáo thành công"}

    @staticmethod
    def delete_report(student_id, report_id):
        success = ReportRepository.delete_report(student_id, report_id)
        if not success:
            return {"success": False, "error": "Xóa báo cáo thất bại"}
        return {"success": True, "message": "Xóa báo cáo thành công"}