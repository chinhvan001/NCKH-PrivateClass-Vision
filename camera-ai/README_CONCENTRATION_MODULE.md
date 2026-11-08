# BÁO CÁO CHI TIẾT TRIỂN KHAI MODULE XỬ LÝ ĐIỂM TẬP TRUNG HỌC SINH
## (Student Concentration Dynamic Scoring System - 3-Tier Architecture)

---

### 1. TỔNG QUAN KIẾN TRÚC 3 LỚP (3-TIER ARCHITECTURE)

Hệ thống được thiết kế theo đúng chuẩn kiến trúc phân tầng 3 lớp (3-Tier Clean Architecture), đảm bảo tính phân tách trách nhiệm (Separation of Concerns), dễ bảo trì, mở rộng và kiểm thử:

```
                  [ Camera-AI Edge Node ]
                             │
                             │  HTTP POST (JSON Payload định kỳ 3-5s)
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION TIER (Routes / Controllers)                                 │
│    - File: routes/concentration_routes.py                                   │
│    - Tiếp nhận HTTP POST request từ camera-ai edge nodes                   │
│    - Kiểm tra tính toàn vẹn (Validation): kiểm tra kiểu dữ liệu, danh sách  │
│      học sinh, các trường bắt buộc, behavior_state hợp lệ                  │
│    - Điều hướng xử lý sang Business Logic Tier                              │
│    - Trả về mã phản hồi chuẩn HTTP: 200 OK, 400 Bad Request, 500 Error     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. BUSINESS LOGIC TIER (Services / Use Cases)                               │
│    - File: services/concentration_service.py                                │
│    - Khởi tạo điểm mặc định ban đầu: 100.0                                  │
│    - Bảng trọng số trạng thái hành vi:                                      │
│        * attentive: +1.0                                                    │
│        * slightly_distracted: -1.5                                          │
│        * looking_down: -3.0                                                 │
│        * sleeping: -4.5                                                     │
│        * using_phone: -6.0                                                  │
│        * away_from_seat: -4.0                                               │
│        * active_participating: +4.0                                         │
│    - Hệ số lũy tiến vi phạm: multiplier = min(2.5, 1.0 + (duration / 20.0)) │
│    - Giới hạn (clamping) điểm số an toàn trong khoảng [0.0, 100.0]          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. DATA ACCESS TIER (Repositories / Firebase Service)                       │
│    - File: repositories/concentration_repository.py                         │
│    - Sử dụng Firebase Admin SDK (Cloud Firestore)                           │
│    - Đường dẫn lưu trữ:                                                     │
│        * Real-time: classrooms/{classroom_id}/live_scores/{student_id}      │
│        * Lịch sử:   classrooms/{classroom_id}/live_scores/{student_id}/     │
│                     history_logs/{auto_id}                                  │
│    - Áp dụng Firestore Batch Writes (db.batch()) cam kết nguyên tử (atomic) │
│    - Cơ chế tự động phân đoạn (Chunking) tối đa 200 HS/batch để không vượt   │
│      ngưỡng giới hạn 500 writes của Firestore                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2. CHI TIẾT THUẬT TOÁN TÍNH ĐIỂM TẬP TRUNG ĐỘNG

#### 2.1. Bảng trọng số hành vi (`BEHAVIOR_WEIGHTS`)
| Hành vi (`behavior_state`) | Trọng số (`weight`) | Phân loại |
| :--- | :---: | :--- |
| `attentive` | **+1.0** | Tích cực (Nghe giảng tập trung) |
| `slightly_distracted` | **-1.5** | Vi phạm nhẹ (Nhìn ngó xung quanh) |
| `looking_down` | **-3.0** | Vi phạm (Cúi đầu) |
| `sleeping` | **-4.5** | Vi phạm nặng (Gục đầu ngủ) |
| `using_phone` | **-6.0** | Vi phạm rất nặng (Sử dụng điện thoại) |
| `away_from_seat` | **-4.0** | Vi phạm (Rời khỏi chỗ ngồi) |
| `active_participating` | **+4.0** | Rất tích cực (Giơ tay / tương tác phát biểu) |

#### 2.2. Hệ số lũy tiến vi phạm theo thời gian (`multiplier`)
- Áp dụng phạt tăng nặng cho các hành vi bị trừ điểm (`weight < 0`):
  $$\text{multiplier} = \min\left(2.5, 1.0 + \frac{\text{duration\_counter}}{20.0}\right)$$
  * Ví dụ:
    - Kéo dài $0\text{s} \rightarrow \text{multiplier} = 1.0$
    - Kéo dài $10\text{s} \rightarrow \text{multiplier} = 1.5$
    - Kéo dài $20\text{s} \rightarrow \text{multiplier} = 2.0$
    - Kéo dài $\ge 30\text{s} \rightarrow \text{multiplier} = 2.5$ (chặn trần tối đa ở 2.5)
- Với hành vi cộng điểm (`attentive`, `active_participating`):
  $$\text{multiplier} = 1.0$$

#### 2.3. Mức biến thiên và giới hạn điểm (`clamping`)
- Mức biến thiên:
  $$\Delta = \text{round}(\text{weight} \times \text{multiplier}, 2)$$
- Điểm số mới:
  $$\text{new\_score} = \text{round}(\max(0.0, \min(100.0, \text{previous\_score} + \Delta)), 2)$$

---

### 3. CẤU TRÚC VÀ DANH SÁCH FILE ĐÃ THỰC HIỆN

#### 3.1. Phía Backend Thử nghiệm & Chính thức (`backend/`)
1. **`repositories/concentration_repository.py`**:
   - `get_classroom_live_scores_map(classroom_id, student_ids)`: Đọc điểm hiện tại của các học sinh.
   - `save_live_scores_batch(classroom_id, student_records)`: Ghi batch đồng thời trạng thái live và tạo log lịch sử trong `history_logs`. Tự động chia nhỏ chunks nếu số lượng học sinh lớn.
   - `get_student_history_logs(classroom_id, student_id, limit)`: Truy vấn danh sách lịch sử phục vụ vẽ biểu đồ (Chart.js / Flutter Chart).
2. **`services/concentration_service.py`**:
   - Điều phối toàn bộ nghiệp vụ tính điểm: kiểm tra input, tính multiplier, tính new_score, giới hạn [0.0, 100.0], tính điểm trung bình lớp học.
3. **`routes/concentration_routes.py`**:
   - Cung cấp API endpoints:
     * `POST /api/v1/concentration/process-score`
     * `POST /api/v1/concentration/classrooms/<classroom_id>/live-scores`
     * `GET /api/v1/concentration/history/<classroom_id>/<student_id>`
4. **`app.py`**:
   - Đăng ký `concentration_bp` vào Flask app mà không làm ảnh hưởng đến các routes/blueprints có sẵn khác.
5. **Bộ Unit Tests**:
   - `tests/test_concentration_service.py` (8 test cases)
   - `tests/test_concentration_routes.py` (5 test cases)
   - `tests/test_concentration_repository.py` (2 test cases)

#### 3.2. Phía Edge Node (`camera-ai/`)
1. **`src/sync/concentration_client.py`**:
   - HTTP Client chuyên dụng gửi JSON payload học sinh định kỳ 3-5 giây sang backend kèm xử lý lỗi timeout, ngắt kết nối mạng.
2. **`tools/simulate_concentration_stream.py`**:
   - Script chạy độc lập giả lập luồng dữ liệu 5 học sinh gửi đều đặn mỗi 3-5 giây để kiểm thử toàn diện End-to-End.
3. **`tests/test_concentration_client.py`**:
   - Unit test kiểm thử client với mock session HTTP POST.

---

### 4. ĐẶC TẢ API ENDPOINTS

#### Endpoint 1: Xử lý điểm tập trung từ Camera AI
- **Method**: `POST`
- **URL**: `/api/v1/concentration/process-score`
- **Headers**: `Content-Type: application/json`
- **Request Body mẫu**:
```json
{
  "classroom_id": "CLASS_12A1",
  "students": [
    {
      "student_id": "HS001",
      "behavior_state": "attentive",
      "duration_counter": 5.0,
      "seat_id": "S01"
    },
    {
      "student_id": "HS002",
      "behavior_state": "using_phone",
      "duration_counter": 20.0,
      "seat_id": "S02"
    }
  ]
}
```
- **Response mẫu (200 OK)**:
```json
{
  "success": true,
  "message": "Tính toán và cập nhật điểm tập trung học sinh thành công.",
  "data": {
    "classroom_id": "CLASS_12A1",
    "total_students": 2,
    "saved_count": 2,
    "average_score": 94.0,
    "results": [
      {
        "student_id": "HS001",
        "classroom_id": "CLASS_12A1",
        "previous_score": 100.0,
        "current_score": 100.0,
        "behavior_state": "attentive",
        "duration_counter": 5.0,
        "multiplier": 1.0,
        "delta": 1.0,
        "seat_id": "S01"
      },
      {
        "student_id": "HS002",
        "classroom_id": "CLASS_12A1",
        "previous_score": 100.0,
        "current_score": 88.0,
        "behavior_state": "using_phone",
        "duration_counter": 20.0,
        "multiplier": 2.0,
        "delta": -12.0,
        "seat_id": "S02"
      }
    ]
  }
}
```

#### Endpoint 2: Lấy dữ liệu lịch sử vẽ biểu đồ thống kê
- **Method**: `GET`
- **URL**: `/api/v1/concentration/history/<classroom_id>/<student_id>?limit=120`
- **Response mẫu (200 OK)**:
```json
{
  "success": true,
  "classroom_id": "CLASS_12A1",
  "student_id": "HS001",
  "total_records": 2,
  "history_logs": [
    {
      "id": "log_01",
      "score": 100.0,
      "behavior_state": "attentive",
      "duration_counter": 3.0,
      "delta": 1.0,
      "timestamp": "2026-11-07T16:40:00+00:00"
    },
    {
      "id": "log_02",
      "score": 97.0,
      "behavior_state": "looking_down",
      "duration_counter": 5.0,
      "delta": -3.0,
      "timestamp": "2026-11-07T16:40:05+00:00"
    }
  ]
}
```

---

### 5. KẾT QUẢ KIỂM THỬ (15/15 TESTS PASSED)

Tất cả các bài kiểm thử tự động đã chạy thành công 100%:
- Bảng trọng số đúng tuyệt đối theo đặc tả.
- Hệ số `multiplier` lũy tiến chính xác theo thời lượng và bị chặn trần ở `2.5`.
- Cơ chế `clamping` đảm bảo điểm không bao giờ tràn ra ngoài dải `[0.0, 100.0]`.
- Firestore Batch Writes ghi nguyên tử cả live score và history logs.
- Validation xử lý chặt chẽ lỗi nhập liệu, trả về HTTP status 400 rõ ràng.

---

### 6. HƯỚNG DẪN KHỞI CHẠY VÀ SỬ DỤNG

1. **Khởi động Backend Flask Server**:
   ```bash
   cd D:\NCKH\PrivateClass-Vision\backend
   python app.py
   ```
   Server sẽ lắng nghe tại `http://127.0.0.1:5000`.

2. **Chạy script mô phỏng Camera-AI gửi dữ liệu**:
   ```bash
   cd D:\NCKH\Test\camera-ai
   python tools/simulate_concentration_stream.py
   ```

3. **Chạy bộ kiểm thử tự động (Pytest)**:
   ```bash
   pytest tests/test_concentration_service.py tests/test_concentration_routes.py tests/test_concentration_repository.py -v
   ```
