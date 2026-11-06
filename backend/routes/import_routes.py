from flask import Blueprint, request, jsonify
import pandas as pd
from datetime import datetime
import re

import_bp = Blueprint('import_bp', __name__)
from firebase_config import db 

@import_bp.route('/api/import/<data_type>', methods=['POST'])
def import_file(data_type):
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file tải lên"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Chưa chọn file"}), 400

    filename = file.filename.lower()
    try:
        if not filename.endswith(('.xlsx', '.xls', '.pdf')):
            return jsonify({"success": False, "message": "Vui lòng sử dụng file Excel (.xlsx, .xls) hoặc PDF (.pdf)"}), 400

        if filename.endswith('.pdf'):
            return jsonify({"success": False, "message": "Tính năng đọc dữ liệu trực tiếp từ file PDF đang được cập nhật."}), 400

        # Đọc file Excel bằng pandas
        df = pd.read_excel(file, header=None)
        header_row_idx = 0
        for idx, row in df.iterrows():
            row_str = str(row.values)
            if any(keyword in row_str for keyword in ["Họ và tên", "Tên", "Email", "Gmail", "Số điện thoại", "SĐT"]):
                header_row_idx = idx
                break

        df = pd.read_excel(file, header=header_row_idx)
        df.dropna(how='all', inplace=True)
        records = df.to_dict(orient='records')

        success_count = 0
        duplicates = []

        # ==================== XỬ LÝ NHẬP GIÁO VIÊN ====================
        if data_type == 'teachers':
            existing_emails = set()
            teachers_ref = db.collection("teachers").stream()
            for doc in teachers_ref:
                doc_data = doc.to_dict()
                email_val = doc_data.get("email")
                if email_val and email_val != "Chưa có email":
                    existing_emails.add(email_val.strip().lower())

            for item in records:
                name = str(item.get("Họ và tên", item.get("Tên", item.get("name", "")))).strip()
                email = str(item.get("Email", item.get("Gmail", item.get("email", "")))).strip()
                phone = str(item.get("Số điện thoại", item.get("SĐT", item.get("phone_number", "")))).strip()
                subject = str(item.get("Bộ môn", item.get("Môn", item.get("subject", "")))).strip()
                status = str(item.get("Trạng thái", "Đang hoạt động")).strip()

                if not name or name == "nan" or name == "None":
                    continue

                formatted_email = email if email and email != "nan" else "Chưa có email"
                email_lower = formatted_email.lower()

                if email_lower != "chưa có email" and email_lower in existing_emails:
                    duplicates.append(name)
                    continue

                teacher_data = {
                    "name": name,
                    "email": formatted_email,
                    "phone_number": phone if phone and phone != "nan" else "",
                    "subject": subject if subject and subject != "nan" else "Chưa cập nhật",
                    "is_active": False if "vô hiệu" in status.lower() else True,
                    "create_date": datetime.now()
                }
                
                db.collection("teachers").add(teacher_data)
                if email_lower != "chưa có email":
                    existing_emails.add(email_lower)
                success_count += 1

        # ==================== XỬ LÝ NHẬP HỌC SINH (SỬ DỤNG BẢNG students2) ====================
        elif data_type == 'students':
            def clean_str(val):
                """Hàm chuẩn hóa chuỗi: xóa khoảng trắng thừa, đưa về chữ thường"""
                if not val or val == "nan" or val == "None":
                    return ""
                return re.sub(r'\s+', ' ', str(val)).strip().lower()

            # 1. Tải danh sách lớp hiện có để map tên lớp
            classes_map = {}
            classes_ref = db.collection("classes").stream()
            for c_doc in classes_ref:
                c_data = c_doc.to_dict()
                c_name = clean_str(c_data.get("name", ""))
                if c_name:
                    classes_map[c_name] = c_doc.id

            # 2. Tải danh sách học sinh từ bảng "students2" để check trùng 4 yếu tố
            existing_students = []
            students_ref = db.collection("students2").stream()
            for doc in students_ref:
                doc_data = doc.to_dict()
                cls_val = clean_str(doc_data.get("current_class", doc_data.get("class_id", "")))
                
                existing_students.append({
                    "full_name": clean_str(doc_data.get("full_name", "")),
                    "class_name": cls_val,
                    "parent_name": clean_str(doc_data.get("parent_name", "")),
                    "parent_phonenumber": clean_str(doc_data.get("parent_phonenumber", doc_data.get("phone_number", "")))
                })

            for item in records:
                name_raw = str(item.get("Họ và tên", item.get("Tên", item.get("full_name", "")))).strip()
                phone_raw = str(item.get("Số điện thoại", item.get("SĐT", item.get("parent_phonenumber", "")))).strip()
                gender_raw = str(item.get("Giới tính", "Nam")).strip()
                status_raw = str(item.get("Trạng thái", "Đang học")).strip()
                parent_name_raw = str(item.get("Phụ huynh", item.get("parent_name", ""))).strip()
                class_excel_raw = str(item.get("Lớp hiện tại", item.get("Lớp", ""))).strip()

                if not name_raw or name_raw == "nan" or name_raw == "None":
                    continue

                name_clean = clean_str(name_raw)
                parent_name_clean = clean_str(parent_name_raw)
                phone_clean = clean_str(phone_raw)
                class_clean = clean_str(class_excel_raw)

                resolved_class_id = classes_map.get(class_clean, class_excel_raw)
                resolved_class_clean = clean_str(resolved_class_id)

                # Kiểm tra trùng lặp: Bắt buộc CẢ 4 YẾU TỐ phải khớp hoàn toàn
                is_duplicate = False
                for ex in existing_students:
                    if (ex["full_name"] == name_clean and 
                        (ex["class_name"] == class_clean or ex["class_name"] == resolved_class_clean) and
                        ex["parent_name"] == parent_name_clean and 
                        ex["parent_phonenumber"] == phone_clean):
                        is_duplicate = True
                        break

                if is_duplicate:
                    duplicates.append(name_raw)
                    continue  # Trùng cả 4 yếu tố -> Bỏ qua

                # Lấy thêm trường Ngày sinh từ file Excel (hỗ trợ nhiều tên cột khác nhau)
                birthday_raw = str(item.get("Ngày sinh", item.get("Birthday", item.get("birthday", "")))).strip()

                # Thêm mới học sinh vào bảng "students2" (Đã bổ sung đầy đủ birthday và parent_name)
                student_data = {
                    "full_name": name_raw,
                    "birthday": birthday_raw if birthday_raw != "nan" else "",
                    "gender": gender_raw if gender_raw in ["Nam", "Nữ"] else "Nam",
                    "parent_phonenumber": phone_raw if phone_raw != "nan" else "",
                    "parent_name": parent_name_raw if parent_name_raw != "nan" else "",
                    "class_id": resolved_class_id,
                    "current_class": class_excel_raw if class_excel_raw != "nan" else "",
                    "status": status_raw if status_raw in ["Đang học", "Tạm nghỉ", "Đã thôi học"] else "Đang học",
                    "created_at": datetime.now()
                }
                
                db.collection("students2").add(student_data)
                
                # Cập nhật vào danh sách tạm để check trùng với các dòng phía sau trong cùng file
                existing_students.append({
                    "full_name": name_clean,
                    "class_name": class_clean,
                    "parent_name": parent_name_clean,
                    "parent_phonenumber": phone_clean
                })
                success_count += 1
        else:
            return jsonify({"success": False, "message": "Loại dữ liệu không hợp lệ"}), 400

        target_name = "giáo viên" if data_type == 'teachers' else "học sinh"
        return jsonify({
            "success": True, 
            "success_count": success_count,
            "duplicates": duplicates,
            "message": f"Đã nhập thành công {success_count} {target_name}."
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi xử lý file: {str(e)}"}), 500