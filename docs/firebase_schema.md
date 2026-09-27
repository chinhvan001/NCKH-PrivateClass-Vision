# CẤU TRÚC FIRESTORE DATABASE (SCHEMA)

Yêu cầu AI BẮT BUỘC sử dụng chính xác tên Collection, Field keys, Data Types và Relationships dưới đây khi xây dựng Dart Models (tích hợp `fromJson`/`toJson`) và viết các truy vấn Firebase.

## 1. Collection: `classrooms`

- **Document ID:** `classroom_id` (String)
- **Fields:**
  - `classroom_name` (String): Tên phòng học.
  - `camera_name` (String): Tên camera giám sát.
  - `camera_status` (String): Trạng thái hoạt động của camera.
  - `row` (int): Số hàng ghế trong phòng.
  - `column` (int): Số cột ghế trong phòng.
  - `ip_address` (String): Địa chỉ IP của camera.
  - `rtsp_port` (int): Cổng kết nối RTSP.
  - `rtsp_url` (String): Đường dẫn luồng stream RTSP.

## 2. Collection: `teacher`

- **Document ID:** `teacher_id` (String)
- **Fields:**
  - `create_day` (Timestamp): Ngày tạo tài khoản.
  - `email` (String): Email của giáo viên.
  - `phone_number` (String): Số điện thoại.
  - `subject` (String): Môn học giảng dạy.
  - `name` (String): Tên giáo viên.

## 3. Collection: `classes`

- **Document ID:** `class_id` (String)
- **Fields:**
  - `classroom_id` (String): Reference -> `classrooms`.
  - `teacher_id` (String): Reference -> `teacher`.
  - `class_name` (String): Tên lớp học.
  - `class_size` (int): Sĩ số lớp.
  - `school_year` (int): Năm học.

## 4. Collection: `parent`

- **Document ID:** `parent_id` (String)
- **Fields:**
  - `create_day` (Timestamp): Ngày tạo tài khoản.
  - `email` (String): Email phụ huynh.
  - `phone_number` (String): Số điện thoại.
  - `name` (String): Tên phụ huynh.

## 5. Collection: `students`

- **Document ID:** `student_id` (String)
- **Fields:**
  - `student_name` (String): Tên học sinh.
  - `birthday` (Timestamp/String): Ngày sinh.
  - `gender` (String): Giới tính.
  - `parent_id` (String): Reference -> `parent`.
  - `parent_email` (String): Email của phụ huynh.

## 6. Collection: `Enrollment`

- **Document ID:** `enrollment_id` (String)
- **Fields:**
  - `class_id` (String): Reference -> `classes`.
  - `student_id` (String): Reference -> `students`.
  - `row` (int): Vị trí hàng của học sinh trong lớp.
  - `column` (int): Vị trí cột của học sinh trong lớp.
  - `is_studying` (bool): Trạng thái đang học.
  - `school_year` (int): Năm học.

## 7. Collection: `admin`

- **Document ID:** `admin_id` (String)
- **Fields:**
  - `create_day` (Timestamp): Ngày tạo tài khoản.
  - `email` (String): Email quản trị viên.
  - `phone_number` (String): Số điện thoại.
  - `school` (String): Tên trường học quản lý.
  - `name` (String): Tên quản trị viên.

## 8. Collection: `monitoring_sessions`

- **Document ID:** `monitoring_session_id` (String)
- **Fields:**
  - `class_id` (String): Reference -> `classes`.
  - `teacher_id` (String): Reference -> `teacher`.
  - `classroom_id` (String): Reference -> `classrooms`.
  - `avg_attention_score` (double): Điểm tập trung trung bình của lớp.
  - `present_student` (int): Số học sinh có mặt.
  - `note` (String): Ghi chú buổi học.
  - `start_time` (Timestamp): Thời gian bắt đầu.
  - `end_time` (Timestamp): Thời gian kết thúc.
  - `students` (Array): Mảng trên Firestore (ánh xạ sang Dart là List<Map>) chứa danh sách dữ liệu học sinh. Mỗi phần tử trong mảng là một Object gồm:
    - `student_id` (String): Reference -> `students`.
    - `row` (int): Vị trí hàng.
    - `column` (int): Vị trí cột.
    - `is_attention` (bool): Trạng thái tập trung.
    - `is_present` (bool): Trạng thái có mặt.
    - `attention_score` (double): Điểm tập trung cá nhân.
    - `note` (String): Ghi chú cá nhân.
