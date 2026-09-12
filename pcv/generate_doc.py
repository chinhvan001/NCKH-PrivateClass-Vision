from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# ── Tiêu đề chính ────────────────────────────────────────────────────────────
title = doc.add_heading('HƯỚNG DẪN CHI TIẾT - FEATURE PARENT', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()

# ── 1. Cấu trúc thư mục ──────────────────────────────────────────────────────
doc.add_heading('1. CẤU TRÚC THƯ MỤC', 1)
doc.add_paragraph('lib/features/parent/ gồm các thư mục:')
items = [
    ('models/', 'Chứa các class dữ liệu, ánh xạ từ Firestore collection'),
    ('services/', 'Chứa logic giao tiếp với Firebase Firestore'),
    ('screens/', 'Chứa các màn hình UI'),
    ('widgets/', 'Chứa các widget dùng chung'),
    ('utils/', 'Chứa màu sắc, text style dùng chung toàn feature'),
]
for folder, desc in items:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(folder)
    run.bold = True
    p.add_run(f' — {desc}')

# ── 2. Models ─────────────────────────────────────────────────────────────────
doc.add_heading('2. THƯ MỤC MODELS', 1)
doc.add_paragraph('Mỗi model ánh xạ 1 collection trên Firestore. Có hàm fromFirestore() để parse dữ liệu.')
models = [
    ('student_model.dart', 'Thông tin học sinh: tên, lớp, trường, GV, SĐT, thống kê nhanh'),
    ('session_model.dart', 'Buổi học: ngày, giờ, môn, phòng, % tập trung, trạng thái điểm danh'),
    ('notification_model.dart', 'Thông báo: tiêu đề, nội dung, loại, thời gian, icon, màu'),
    ('attendance_summary_model.dart', 'Tổng hợp điểm danh: tổng buổi, có mặt, vắng, đi muộn, % tập trung TB'),
    ('subject_focus_model.dart', 'Tập trung theo môn: tên môn, % tập trung, kỳ (hôm nay/tuần/tháng)'),
]
for file, desc in models:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(file)
    run.bold = True
    p.add_run(f' — {desc}')

# ── 3. Services ───────────────────────────────────────────────────────────────
doc.add_heading('3. THƯ MỤC SERVICES', 1)
doc.add_paragraph('Xử lý toàn bộ logic giao tiếp với Firebase. Screen không gọi Firestore trực tiếp mà phải đi qua service.')
services = [
    ('student_service.dart', 'students', 'getStudentById(), watchStudentById(), seedSampleData()'),
    ('session_service.dart', 'sessions', 'getSessionsByStudent(), watchSessionsByStudent(), getSessionById(), getAttendanceSummary()'),
    ('notification_service.dart', 'notifications', 'getNotificationsByStudent(), watchNotificationsByStudent(), getUnreadCount()'),
    ('subject_focus_service.dart', 'subject_focus', 'getSubjectFocus(), watchSubjectFocus(), seedSampleData()'),
]
for file, collection, funcs in services:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(file)
    run.bold = True
    p.add_run(f' → collection: {collection}')
    p.add_run(f'\n   Hàm: {funcs}')

doc.add_paragraph()
doc.add_paragraph('Giải thích 2 loại hàm:')
p = doc.add_paragraph(style='List Bullet')
p.add_run('Future (get...)').bold = True
p.add_run(' — Lấy data 1 lần, dùng FutureBuilder trong UI')
p = doc.add_paragraph(style='List Bullet')
p.add_run('Stream (watch...)').bold = True
p.add_run(' — Lắng nghe realtime, tự cập nhật khi data thay đổi, dùng StreamBuilder')

# ── 4. Screens ────────────────────────────────────────────────────────────────
doc.add_heading('4. THƯ MỤC SCREENS', 1)
screens = [
    ('home_screen.dart', 'Màn hình chính, bottom nav bar', '✅ StudentService + SessionService'),
    ('session_history_screen.dart', 'Danh sách lịch sử buổi học, filter chip', '✅ SessionService'),
    ('session_detail_screen.dart', 'Chi tiết 1 buổi học', 'Nhận data từ session_history'),
    ('notification_screen.dart', 'Danh sách thông báo, filter tab', '✅ NotificationService'),
    ('daily_overview_screen.dart', 'Tổng quan tập trung + điểm danh', '✅ SubjectFocusService + SessionService'),
    ('profile_screen.dart', 'Hồ sơ học sinh, thống kê nhanh', '✅ StudentService'),
    ('attendance_detail_screen.dart', 'Chi tiết điểm danh', '⚠️ Static data, chưa có BE'),
    ('switch_account_screen.dart', 'Chọn tài khoản con', '⚠️ Static data, chưa có BE'),
]
for file, desc, firebase in screens:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(file)
    run.bold = True
    p.add_run(f' — {desc} | {firebase}')

# ── 5. Widgets & Utils ────────────────────────────────────────────────────────
doc.add_heading('5. THƯ MỤC WIDGETS', 1)
widgets = [
    ('common_widgets.dart', 'AppCard, StatusChip, AvatarWidget, SubjectProgressBar, BadgeIcon, CircularProgressWidget'),
    ('bottom_nav_bar.dart', 'AppBottomNavBar — thanh điều hướng dưới cùng có animation'),
]
for file, desc in widgets:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(file)
    run.bold = True
    p.add_run(f' — {desc}')

doc.add_heading('6. THƯ MỤC UTILS', 1)
utils = [
    ('app_colors.dart', 'Tất cả màu sắc: primary, green, red, orange, background...'),
    ('app_text_styles.dart', 'Tất cả text style: heading1-3, body1-2, caption, small, button...'),
]
for file, desc in utils:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(file)
    run.bold = True
    p.add_run(f' — {desc}')

# ── 6. Cấu trúc Firestore ─────────────────────────────────────────────────────
doc.add_heading('7. CẤU TRÚC FIRESTORE DATABASE', 1)
collections = [
    ('students/{studentId}', [
        'name: "Minh Anh"',
        'className: "Lớp 5A"',
        'schoolName: "Trường ABC"',
        'teacherName: "Nguyễn Văn A"',
        'avgFocusPercent: 78',
        'totalSessions: 10',
        'presentSessions: 9',
        'nextSessionTime: "15:30"',
    ]),
    ('sessions/{auto_id}', [
        'studentId: "student_minh_anh"',
        'date: "Thứ 6, 16/05/2024"',
        'time: "08:00 - 09:30"',
        'subject: "Toán"',
        'room: "P.201"',
        'percent: 85',
        'status: "present"  ← present/absent/late/excused',
        'createdAt: Timestamp',
    ]),
    ('notifications/{auto_id}', [
        'studentId: "student_minh_anh"',
        'title: "Điểm danh hôm nay"',
        'body: "Minh Anh có mặt đúng giờ"',
        'type: "attendance"  ← attendance/reminder/announcement',
        'tab: "Thông báo"',
        'createdAt: Timestamp',
    ]),
    ('subject_focus/{auto_id}', [
        'studentId: "student_minh_anh"',
        'subject: "Toán"',
        'percent: 85',
        'period: "week"  ← today/week/month',
    ]),
]
for collection, fields in collections:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(collection)
    run.bold = True
    for field in fields:
        p2 = doc.add_paragraph(style='List Bullet 2')
        p2.add_run(field)

# ── 7. Cách liên kết Firebase ─────────────────────────────────────────────────
doc.add_heading('8. CÁCH LIÊN KẾT PROJECT VỚI FIREBASE', 1)
steps = [
    ('Bước 1 — Cài FlutterFire CLI', 'dart pub global activate flutterfire_cli'),
    ('Bước 2 — Đăng nhập Firebase', 'firebase login'),
    ('Bước 3 — Configure project', 'flutterfire configure  →  chọn project private-class-vision  →  tự sinh firebase_options.dart'),
    ('Bước 4 — Thêm dependencies', 'firebase_core, cloud_firestore, firebase_auth vào pubspec.yaml'),
    ('Bước 5 — Khởi tạo trong main.dart', 'await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform)'),
    ('Bước 6 — Thêm google-services.json', 'Download từ Firebase Console → Project Settings → đặt vào android/app/'),
]
for step, detail in steps:
    p = doc.add_paragraph(style='List Number')
    run = p.add_run(step)
    run.bold = True
    p.add_run(f'\n   {detail}')

# ── 8. Luồng dữ liệu ─────────────────────────────────────────────────────────
doc.add_heading('9. LUỒNG DỮ LIỆU (DATA FLOW)', 1)
doc.add_paragraph('Firestore Database  →  Service (query + parse)  →  Screen (FutureBuilder/StreamBuilder)  →  Widget (hiển thị UI)')
doc.add_paragraph()
doc.add_paragraph('Ví dụ HomeScreen:')
p = doc.add_paragraph(style='List Bullet')
p.add_run('StudentService.getStudentById()').bold = True
p.add_run(' → trả về StudentModel (tên, lớp, trường...)')
p = doc.add_paragraph(style='List Bullet')
p.add_run('SessionService.getAttendanceSummary()').bold = True
p.add_run(' → trả về AttendanceSummaryModel (tổng buổi, có mặt, vắng...)')
p = doc.add_paragraph(style='List Bullet')
p.add_run('HomeScreen dùng FutureBuilder').bold = True
p.add_run(' → chờ cả 2 xong rồi render UI')

# ── 9. Lỗi thường gặp ────────────────────────────────────────────────────────
doc.add_heading('10. LỖI THƯỜNG GẶP', 1)
errors = [
    ('PERMISSION_DENIED', 'Firestore Rules chưa cho phép', 'Mở Rules trên Firebase Console'),
    ('FAILED_PRECONDITION', 'Thiếu Firestore Index', 'Tạo composite index trên Firebase Console'),
    ('firebase_options.dart not found', 'Chưa chạy flutterfire configure', 'Chạy lại flutterfire configure'),
    ('Data hiển thị trống', 'Chưa seed data', 'Gọi hàm seedSampleData()'),
    ('studentId cứng', 'Chưa tích hợp Auth', 'Thay student_minh_anh bằng ID thật từ Firebase Auth'),
]
for error, cause, fix in errors:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(error)
    run.bold = True
    p.add_run(f'\n   Nguyên nhân: {cause}')
    p.add_run(f'\n   Cách fix: {fix}')

# ── 10. TODO ──────────────────────────────────────────────────────────────────
doc.add_heading('11. TODO - CÒN CẦN LÀM', 1)
todos = [
    'Thay studentId cứng bằng ID thật từ Firebase Auth',
    'Kết nối AttendanceDetailScreen với Firestore',
    'Kết nối SwitchAccountScreen với danh sách con thật',
    'Đổi Firestore Rules về if isSignedIn() sau khi tích hợp Auth',
    'Xóa nút Seed Data sau khi có data thật',
]
for todo in todos:
    doc.add_paragraph(f'☐  {todo}', style='List Bullet')

# ── Lưu file ──────────────────────────────────────────────────────────────────
doc.save('HUONG_DAN_PARENT.docx')
print('✅ Tạo file HUONG_DAN_PARENT.docx thành công!')
