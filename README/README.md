# PrivateClass Vision

Tài liệu tổng thể của hệ thống quản trị lớp học riêng `PrivateClass Vision`.

## 1. Tổng quan

PrivateClass Vision là ứng dụng web dành cho quản trị viên để:

- Đăng nhập bằng Google hoặc email/mật khẩu thông qua Firebase Authentication.
- Kiểm tra quyền truy cập dựa trên tài khoản trong Firestore.
- Xem tổng quan danh sách giáo viên.
- Tìm kiếm, lọc và cập nhật thông tin giáo viên.
- Xem giao diện quản lý các phiên học và chi tiết phiên học.
- Cập nhật hồ sơ cá nhân và đổi mật khẩu quản trị viên.

Hệ thống hiện được tách thành hai phần:

```text
PrivateClass-Vision/
├── backend/                 # Flask API và kết nối Firebase Admin SDK
├── frontend/                # React + Vite, giao diện quản trị
└── README/                  # Tài liệu hệ thống
```

## 2. Kiến trúc hệ thống

```text
Trình duyệt
    │
    │ React/Vite, Firebase Web SDK
    ▼
Frontend :5173
    │
    │ HTTP JSON + Authorization: Bearer <Firebase ID Token>
    ▼
Backend Flask :5000
    │
    ├── Firebase Authentication / Identity Toolkit
    └── Cloud Firestore
```

### Công nghệ chính

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Frontend | React 19, React Router, Vite | Giao diện và điều hướng quản trị |
| UI | CSS riêng, Tailwind CSS plugin | Bố cục, biểu mẫu, responsive |
| Authentication frontend | Firebase Web SDK | Google login, logout và Firebase Auth state |
| Backend | Python Flask | REST API, kiểm tra token và nghiệp vụ |
| Database | Cloud Firestore | Lưu người dùng và thông tin quản trị |
| Authentication backend | Firebase Admin SDK | Xác thực Firebase ID Token |
| CORS | Flask-CORS | Cho phép frontend gọi backend khi phát triển cục bộ |

## 3. Cấu trúc thư mục

### Backend

```text
backend/
├── app.py                 # Flask app, route API, kiểm tra quyền
├── firebase_config.py     # Khởi tạo Firebase Admin và Firestore
├── requirements.txt       # Python dependencies
├── serviceAccountKey.json # Firebase service account, không được public
├── test_firebase.py       # Kiểm tra kết nối Firebase
├── .env                   # Biến môi trường cục bộ nếu cần
└── venv/                  # Python virtual environment cục bộ
```

### Frontend

```text
frontend/
├── package.json           # Scripts và dependencies
├── vite.config.js         # Cấu hình Vite
├── index.html             # HTML entry point
├── public/                # Tài nguyên tĩnh
└── src/
    ├── App.jsx            # Khai báo route và ProtectedRoute
    ├── main.jsx           # React entry point
    ├── firebase.js         # Cấu hình Firebase Web SDK
    ├── pages/             # Các trang Login, Dashboard, Account, Session
    ├── components/
    │   ├── admin/          # Header, sidebar, dashboard, quản lý tài khoản
    │   ├── auth/           # Form login Google và email/mật khẩu
    │   └── common/         # Button, Input, Icon dùng chung
    ├── layouts/            # Layout dùng chung nếu được mở rộng
    ├── routes/             # Route-related code
    ├── services/            # Tầng gọi service nếu bổ sung thêm
    ├── styles/              # CSS theo từng màn hình
    └── utils/AuthSession.js # Lưu, đọc, xóa session admin
```

## 4. Chuẩn bị môi trường

### Yêu cầu

- Python 3.10 trở lên.
- Node.js 18 trở lên và npm.
- Một Firebase project có bật:
  - Firebase Authentication.
  - Google provider nếu dùng đăng nhập Google.
  - Email/Password provider nếu dùng email và mật khẩu.
  - Cloud Firestore.
- Firebase service account key cho backend.

### Cấu hình Firebase backend

1. Tạo service account trong Firebase/Google Cloud.
2. Tải file JSON credentials.
3. Đặt file tại `backend/serviceAccountKey.json`, hoặc thay đổi cách nạp credentials trong `backend/firebase_config.py`.
4. Không commit file credentials lên Git và không gửi file này lên client.
5. Kiểm tra project ID trong credentials trùng với Firebase project đang dùng.

> `firebase_config.py` hiện đang đọc file `serviceAccountKey.json` theo đường dẫn tương đối. Vì vậy backend nên được chạy từ thư mục `backend`.

### Cài đặt backend

PowerShell:

```powershell
cd d:\NCKH\PrivateClass-Vision\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Backend mặc định phục vụ tại:

```text
http://127.0.0.1:5000
```

Health check:

```text
GET http://127.0.0.1:5000/
```

Kết quả thành công:

```json
{
  "success": true,
  "message": "PrivateClass Vision API is running"
}
```

### Cài đặt frontend

```powershell
cd d:\NCKH\PrivateClass-Vision\frontend
npm install
npm run dev
```

Frontend mặc định chạy tại URL Vite hiển thị trong terminal, thường là:

```text
http://localhost:5173
```

Các lệnh frontend:

```powershell
npm run dev      # Chạy môi trường phát triển
npm run build    # Build production
npm run preview  # Chạy thử bản build
npm run lint     # Kiểm tra ESLint
```

## 5. Luồng đăng nhập và phân quyền

### Đăng nhập Google

1. Người dùng chọn Google Login trên frontend.
2. Firebase Web SDK xác thực Google và trả về Firebase ID Token.
3. Frontend gửi token tới `POST /api/auth/google`.
4. Backend dùng Firebase Admin SDK xác minh token.
5. Backend lấy document `users/{uid}` trong Firestore.
6. Backend chỉ cho phép role `admin` hoặc `super_admin` và tài khoản đang hoạt động.
7. Frontend lưu user, ID token và thời gian hết hạn vào `localStorage`.
8. Người dùng được chuyển tới Dashboard.

### Đăng nhập email/mật khẩu

1. Frontend gửi email và mật khẩu tới `POST /api/auth/email-password`.
2. Backend gọi Firebase Identity Toolkit để xác thực thông tin đăng nhập.
3. Backend xác minh lại ID Token nhận được.
4. Backend kiểm tra document người dùng, role và `is_active`.
5. Backend trả token cùng dữ liệu người dùng hợp lệ.

### Bảo vệ route frontend

`ProtectedRoute` trong `frontend/src/App.jsx` kiểm tra session bằng `getAdminSession()`.

- Chưa có session: chuyển về `/login`.
- Session hết hạn: xóa local storage và chuyển về `/login`.
- Có session hợp lệ: cho phép mở trang quản trị.

Session frontend hiện có thời hạn 30 phút, được lưu bằng ba khóa:

```text
adminUser
idToken
sessionExpiresAt
```

### Bảo vệ API backend

Các API quản trị yêu cầu header:

```http
Authorization: Bearer <Firebase ID Token>
Content-Type: application/json
```

Backend thực hiện các bước:

1. Đọc Bearer token.
2. Gọi `auth.verify_id_token`.
3. Tìm user tương ứng trong Firestore.
4. Kiểm tra role và trạng thái tài khoản.
5. Chỉ thực hiện nghiệp vụ sau khi xác thực thành công.

Các role quản trị được chấp nhận:

```text
admin
super_admin
```

Role giáo viên:

```text
teacher
```

## 6. Các route frontend

| URL | Trang | Quyền |
|---|---|---|
| `/login` | Đăng nhập | Công khai |
| `/dashboard` | Tổng quan quản trị | Admin |
| `/account-management` | Quản lý giáo viên | Admin |
| `/session-management` | Quản lý phiên học | Admin |
| `/session-management/:sessionId` | Chi tiết phiên học | Admin |
| `/` | Tự chuyển đến `/login` | - |
| URL không tồn tại | Tự chuyển đến `/login` | - |

## 7. REST API backend

### `GET /`

Health check, không yêu cầu token.

### `POST /api/auth/google`

Đăng nhập bằng Firebase ID Token từ Google.

Request:

```json
{
  "idToken": "<firebase-id-token>"
}
```

Thành công trả về thông tin admin. Các lỗi thường gặp: `400` thiếu token, `401` token không hợp lệ, `403` tài khoản không có quyền hoặc bị vô hiệu hóa.

### `POST /api/auth/email-password`

Đăng nhập bằng email và mật khẩu.

Request:

```json
{
  "email": "admin@example.com",
  "password": "your-password"
}
```

Thành công trả về:

```json
{
  "success": true,
  "message": "Đăng nhập thành công.",
  "idToken": "<firebase-id-token>",
  "user": {
    "uid": "firebase-uid",
    "email": "admin@example.com",
    "name": "Admin",
    "phone_number": "",
    "role": "admin",
    "is_active": true
  }
}
```

### `GET /api/admin/users`

Lấy toàn bộ tài khoản có `role = teacher`. Yêu cầu token admin.

Response chính:

```json
{
  "success": true,
  "users": [
    {
      "id": "teacher-uid",
      "uid": "teacher-uid",
      "email": "teacher@example.com",
      "name": "Nguyen Van A",
      "phone_number": "0900000000",
      "role": "teacher",
      "is_active": true,
      "subject": ["Toán", "Lý"]
    }
  ],
  "total": 1
}
```

### `PUT /api/users/<uid>`

Cập nhật tài khoản giáo viên. Chỉ cập nhật được user có role `teacher`.

Request có thể gồm một hoặc nhiều trường:

```json
{
  "name": "Nguyen Van A",
  "phone_number": "0900000000",
  "subject": ["Toán", "Lý"],
  "is_active": true
}
```

Quy tắc:

- `name` không được rỗng nếu gửi lên.
- `subject` phải là một mảng; các phần tử được trim và loại bỏ giá trị rỗng.
- `is_active` phải là boolean.
- Không cho dùng API này để cập nhật tài khoản admin.

### `GET /api/admin/profile/<uid>`

Lấy hồ sơ admin. Token chỉ được xem profile của chính UID trong URL.

### `PUT /api/admin/profile/<uid>`

Cập nhật hồ sơ admin của chính mình.

Request:

```json
{
  "name": "Admin mới",
  "phone_number": "0900000000"
}
```

### `POST /api/admin/change-password`

Đổi mật khẩu của admin hiện tại. Yêu cầu token hợp lệ và tài khoản có role quản trị.

Các field request được backend sử dụng:

```json
{
  "currentPassword": "old-password",
  "newPassword": "new-password"
}
```

## 8. Mô hình dữ liệu Firestore

Collection chính:

```text
users/{uid}
```

### Document admin

```json
{
  "uid": "admin-uid",
  "email": "admin@example.com",
  "name": "System Admin",
  "phone_number": "0900000000",
  "role": "admin",
  "is_active": true
}
```

### Document giáo viên

```json
{
  "uid": "teacher-uid",
  "email": "teacher@example.com",
  "name": "Nguyen Van A",
  "phone_number": "0900000000",
  "role": "teacher",
  "is_active": true,
  "subject": ["Toán", "Lý"]
}
```

### Quy ước quan trọng

- Tên document nên trùng với Firebase Auth UID.
- `role` quyết định loại tài khoản.
- `is_active` mặc định được xem là `true` nếu field không tồn tại.
- `subject` của giáo viên phải là mảng chuỗi.
- Firebase Authentication lưu thông tin xác thực; Firestore lưu thông tin nghiệp vụ và phân quyền ứng dụng.

## 9. Các màn hình chính

### Login

Bao gồm đăng nhập Google và email/mật khẩu. Sau khi thành công, session admin được lưu local và người dùng đi tới Dashboard.

### Dashboard

Gọi `GET /api/admin/users` để lấy danh sách giáo viên, sau đó hiển thị các số liệu tổng quan như tổng số, đang hoạt động và đã vô hiệu hóa.

### Account Management

Gọi `GET /api/admin/users` để hiển thị danh sách giáo viên. Form chỉnh sửa gọi `PUT /api/users/<uid>` để cập nhật họ tên, số điện thoại, bộ môn và trạng thái.

### Session Management

Hiển thị lịch phiên học, bộ lọc theo ngày, lớp, môn, giáo viên và trạng thái. Theo mã nguồn hiện tại, dữ liệu phiên học trong `SessionManagementPanel.jsx` đang là dữ liệu mẫu ở frontend, chưa được lấy từ API backend.

### Session Detail

Hiển thị chi tiết phiên học theo `sessionId`, gồm lớp, môn, giáo viên, thời gian, trạng thái và chỉ số tập trung nếu có. Trang hiện có fallback data khi không tìm thấy phiên tương ứng.

### Admin Profile

Header và modal hồ sơ cho phép lấy/cập nhật thông tin admin. Đổi mật khẩu sử dụng API riêng của backend.

## 10. Mã trạng thái HTTP

| Mã | Ý nghĩa |
|---|---|
| `200` | Thành công |
| `400` | Request thiếu hoặc sai dữ liệu |
| `401` | Chưa xác thực hoặc token không hợp lệ |
| `403` | Đã xác thực nhưng không đủ quyền |
| `404` | Không tìm thấy tài nguyên |
| `405` | Method không được hỗ trợ |
| `500` | Lỗi xử lý phía server |
| `503` | Backend không kết nối được Firebase trong lúc đăng nhập |

Response lỗi có dạng cơ bản:

```json
{
  "success": false,
  "message": "Mô tả lỗi"
}
```

## 11. Kiểm thử và chẩn đoán lỗi

### Kiểm tra backend

```powershell
cd d:\NCKH\PrivateClass-Vision\backend
.\venv\Scripts\Activate.ps1
python test_firebase.py
```

### Kiểm tra frontend

```powershell
cd d:\NCKH\PrivateClass-Vision\frontend
npm run lint
npm run build
```

### Một số lỗi thường gặp

- `serviceAccountKey.json` không tìm thấy: chạy backend từ thư mục `backend` hoặc sửa đường dẫn credentials.
- `401 Unauthorized`: token đã hết hạn, thiếu header Bearer hoặc Firebase project không khớp.
- `403`: document `users/{uid}` chưa tồn tại, role không phải `admin`/`super_admin`, hoặc `is_active` là `false`.
- Frontend không gọi được backend: kiểm tra backend đã chạy ở port `5000`, URL trong các page có đúng `http://127.0.0.1:5000` và CORS.
- Không đăng nhập Google được: kiểm tra Google provider, authorized domains và Firebase configuration.
- Firestore không đọc được: kiểm tra service account, project ID và quyền IAM/Firestore.

## 12. Bảo mật và triển khai

- Không commit `serviceAccountKey.json`, file `.env`, token hoặc mật khẩu.
- Nên chuyển URL backend và Firebase config phù hợp sang biến môi trường khi triển khai production.
- Không nên hard-code API URL `http://127.0.0.1:5000` trong nhiều component; nên gom vào một cấu hình dùng chung.
- Production phải dùng HTTPS.
- CORS nên giới hạn origin frontend thay vì mở toàn bộ bằng `CORS(app)`.
- Không nên coi localStorage là nơi lưu trữ token có mức bảo mật cao; cần cân nhắc cookie HttpOnly và cơ chế refresh token khi triển khai thực tế.
- Cần cấu hình Firebase Auth authorized domains và Firestore Security Rules theo môi trường.
- Nên bổ sung logging có kiểm soát, không ghi token, mật khẩu hoặc thông tin nhạy cảm vào log.

## 13. Những phần cần phát triển tiếp

1. Tạo API và collection cho phiên học thay vì dùng dữ liệu mẫu trong frontend.
2. Đồng bộ `SessionManagement` và `SessionDetail` với backend.
3. Đưa `API_BASE_URL` vào biến môi trường Vite.
4. Bổ sung test tự động cho API auth, phân quyền và cập nhật giáo viên.
5. Bổ sung validation rõ hơn cho số điện thoại, mật khẩu và dữ liệu Firestore.
6. Chuẩn hóa việc quản lý lỗi và trạng thái loading ở các trang.
7. Tách credentials và các khóa cấu hình khỏi source code.
8. Thêm cơ chế refresh hoặc xác minh lại Firebase token khi session frontend gần hết hạn.

## 14. Quy trình chạy đầy đủ trong môi trường phát triển

Mở hai terminal:

Terminal 1:

```powershell
cd d:\NCKH\PrivateClass-Vision\backend
.\venv\Scripts\Activate.ps1
python app.py
```

Terminal 2:

```powershell
cd d:\NCKH\PrivateClass-Vision\frontend
npm run dev
```

Sau đó mở URL frontend, đăng nhập bằng tài khoản đã được cấp trong Firebase Authentication và có document tương ứng trong Firestore collection `users` với role `admin` hoặc `super_admin`.
