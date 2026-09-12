# HƯỚNG DẪN CHI TIẾT - FEATURE PARENT

---

## 1. CẤU TRÚC THƯ MỤC

```
lib/features/parent/
├── models/         → Chứa các class dữ liệu (ánh xạ từ Firestore)
├── services/       → Chứa logic giao tiếp với Firebase
├── screens/        → Chứa các màn hình UI
├── widgets/        → Chứa các widget dùng chung
└── utils/          → Chứa màu sắc, text style dùng chung
```

---

## 2. THƯ MỤC MODELS

> **Vai trò:** Định nghĩa cấu trúc dữ liệu. Mỗi model ánh xạ 1 collection trên Firestore.

| File | Mô tả |
|---|---|
| `student_model.dart` | Thông tin học sinh: tên, lớp, trường, GV, SĐT phụ huynh, thống kê nhanh |
| `session_model.dart` | Thông tin 1 buổi học: ngày, giờ, môn, phòng, % tập trung, trạng thái điểm danh |
| `notification_model.dart` | Thông báo: tiêu đề, nội dung, loại, thời gian, icon, màu |
| `attendance_summary_model.dart` | Tổng hợp điểm danh: tổng buổi, có mặt, vắng, đi muộn, % tập trung TB |
| `subject_focus_model.dart` | Tập trung theo môn học: tên môn, % tập trung, kỳ (hôm nay/tuần/tháng) |

### Cách hoạt động của Model:
```dart
// Firestore trả về DocumentSnapshot
// Model có hàm fromFirestore() để chuyển thành object Dart
factory StudentModel.fromFirestore(DocumentSnapshot doc) {
  final d = doc.data() as Map<String, dynamic>;
  return StudentModel(
    id: doc.id,
    name: d['name'] as String? ?? '',
    // ...
  );
}
```

---

## 3. THƯ MỤC SERVICES

> **Vai trò:** Xử lý toàn bộ logic giao tiếp với Firebase Firestore. Screen không được gọi Firestore trực tiếp mà phải đi qua service.

| File | Collection Firestore | Các hàm chính |
|---|---|---|
| `student_service.dart` | `students` | `getStudentById()`, `watchStudentById()`, `seedSampleData()` |
| `session_service.dart` | `sessions` | `getSessionsByStudent()`, `watchSessionsByStudent()`, `getSessionById()`, `getAttendanceSummary()` |
| `notification_service.dart` | `notifications` | `getNotificationsByStudent()`, `watchNotificationsByStudent()`, `getUnreadCount()` |
| `subject_focus_service.dart` | `subject_focus` | `getSubjectFocus()`, `watchSubjectFocus()`, `seedSampleData()` |

### Giải thích 2 loại hàm:
- **Future** (get...): Lấy data 1 lần → dùng `FutureBuilder`
- **Stream** (watch...): Lắng nghe realtime, tự cập nhật khi data thay đổi → dùng `StreamBuilder`

```dart
// Ví dụ dùng Future (lấy 1 lần)
final student = await StudentService().getStudentById('student_minh_anh');

// Ví dụ dùng Stream (realtime)
StudentService().watchStudentById('student_minh_anh').listen((student) {
  // tự động cập nhật khi data thay đổi
});
```

---

## 4. THƯ MỤC SCREENS

> **Vai trò:** Hiển thị UI, gọi service để lấy data, render lên màn hình.

| File | Mô tả | Kết nối Firebase |
|---|---|---|
| `home_screen.dart` | Màn hình chính, bottom nav bar | ✅ StudentService + SessionService |
| `session_history_screen.dart` | Danh sách lịch sử buổi học, filter | ✅ SessionService |
| `session_detail_screen.dart` | Chi tiết 1 buổi học | Nhận data từ session_history |
| `notification_screen.dart` | Danh sách thông báo, filter tab | ✅ NotificationService |
| `daily_overview_screen.dart` | Tổng quan tập trung + điểm danh | ✅ SubjectFocusService + SessionService |
| `profile_screen.dart` | Hồ sơ học sinh, thống kê nhanh | ✅ StudentService |
| `attendance_detail_screen.dart` | Chi tiết điểm danh | ⚠️ Static data (chưa có BE) |
| `switch_account_screen.dart` | Chọn tài khoản con | ⚠️ Static data (chưa có BE) |

---

## 5. THƯ MỤC WIDGETS

> **Vai trò:** Các widget tái sử dụng nhiều lần, tránh viết lặp code.

| File | Các widget |
|---|---|
| `common_widgets.dart` | `AppCard`, `StatusChip`, `AvatarWidget`, `SubjectProgressBar`, `BadgeIcon`, `CircularProgressWidget` |
| `bottom_nav_bar.dart` | `AppBottomNavBar` — thanh điều hướng dưới cùng có animation |

---

## 6. THƯ MỤC UTILS

> **Vai trò:** Hằng số dùng chung toàn bộ feature parent.

| File | Mô tả |
|---|---|
| `app_colors.dart` | Tất cả màu sắc: primary, green, red, orange, background... |
| `app_text_styles.dart` | Tất cả text style: heading1-3, body1-2, caption, small, button... |

---

## 7. CẤU TRÚC FIRESTORE (DATABASE)

```
Firestore
├── students/
│   └── student_minh_anh/       ← document ID = studentId
│       ├── name: "Minh Anh"
│       ├── className: "Lớp 5A"
│       ├── schoolName: "Trường ABC"
│       ├── teacherName: "Nguyễn Văn A"
│       ├── avgFocusPercent: 78
│       ├── totalSessions: 10
│       ├── presentSessions: 9
│       └── nextSessionTime: "15:30"
│
├── sessions/
│   └── {auto_id}/
│       ├── studentId: "student_minh_anh"
│       ├── date: "Thứ 6, 16/05/2024"
│       ├── time: "08:00 - 09:30"
│       ├── subject: "Toán"
│       ├── room: "P.201"
│       ├── percent: 85
│       ├── status: "present"   ← present/absent/late/excused
│       └── createdAt: Timestamp
│
├── notifications/
│   └── {auto_id}/
│       ├── studentId: "student_minh_anh"
│       ├── title: "Điểm danh hôm nay"
│       ├── body: "Minh Anh có mặt đúng giờ"
│       ├── type: "attendance"  ← attendance/reminder/announcement
│       ├── tab: "Thông báo"
│       └── createdAt: Timestamp
│
└── subject_focus/
    └── {auto_id}/
        ├── studentId: "student_minh_anh"
        ├── subject: "Toán"
        ├── percent: 85
        └── period: "week"      ← today/week/month
```

---

## 8. CÁCH LIÊN KẾT PROJECT VỚI FIREBASE

### Bước 1 — Cài FlutterFire CLI
```
dart pub global activate flutterfire_cli
```

### Bước 2 — Đăng nhập Firebase
```
firebase login
```

### Bước 3 — Chạy lệnh configure
```
flutterfire configure
```
Chọn project `private-class-vision` → chọn platform Android/iOS → tự sinh ra file `firebase_options.dart`

### Bước 4 — Thêm dependencies vào pubspec.yaml
```yaml
dependencies:
  firebase_core: ^4.14.0
  cloud_firestore: ^6.9.0
  firebase_auth: ^6.6.1
```

### Bước 5 — Khởi tạo Firebase trong main.dart
```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(const PrivateClassVision());
}
```

### Bước 6 — Thêm google-services.json (Android)
- Vào Firebase Console → Project Settings → Android app
- Download file `google-services.json`
- Đặt vào thư mục `android/app/`

---

## 9. LUỒNG DỮ LIỆU (DATA FLOW)

```
Firestore Database
      ↓
   Service        (query, parse DocumentSnapshot → Model)
      ↓
   Screen         (FutureBuilder / StreamBuilder)
      ↓
   Widget         (hiển thị UI)
```

### Ví dụ cụ thể — HomeScreen:
```
Firestore (students + sessions)
      ↓
StudentService.getStudentById()      → StudentModel
SessionService.getAttendanceSummary() → AttendanceSummaryModel
      ↓
HomeScreen dùng FutureBuilder chờ data
      ↓
Hiển thị tên, lớp, % tập trung, điểm danh lên UI
```

---

## 10. XỬ LÝ LỖI THƯỜNG GẶP

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `PERMISSION_DENIED` | Firestore Rules chưa cho phép | Mở Rules trên Firebase Console |
| `FAILED_PRECONDITION` | Thiếu Firestore Index | Tạo composite index trên Firebase Console |
| `firebase_options.dart not found` | Chưa chạy flutterfire configure | Chạy lại `flutterfire configure` |
| Data hiển thị trống | Chưa seed data | Gọi hàm `seedSampleData()` |
| `studentId` cứng | Chưa tích hợp Auth | Thay `student_minh_anh` bằng ID thật từ Firebase Auth |

---

## 11. TODO - CÒN CẦN LÀM

- [ ] Thay `studentId` cứng bằng ID thật từ Firebase Auth
- [ ] Kết nối `AttendanceDetailScreen` với Firestore
- [ ] Kết nối `SwitchAccountScreen` với danh sách con thật
- [ ] Đổi Firestore Rules về `if isSignedIn()` sau khi tích hợp Auth
- [ ] Xóa nút Seed Data sau khi có data thật
