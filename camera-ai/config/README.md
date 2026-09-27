# Schema config cục bộ

Sao chép `local_pipeline.example.json` thành một file local ngoài Git (ví dụ
`local_pipeline.json`). Nguồn camera không nằm trong JSON: đặt nó trong biến
môi trường có tên khai báo ở `camera.source_env`, ví dụ:

```powershell
$env:CAMERA_ROOM_A_01_SOURCE = "rtsp://..."
```

Schema gồm:

- `camera`: camera ID, mã phòng/lớp, độ phân giải và **tên** biến môi trường
  chứa nguồn camera.
- `sampling`: FPS capture và số frame bỏ qua giữa các lần inference.
- `thresholds`: ngưỡng pose/cảnh báo đã dùng trong demo.
- `schedule`: timezone và cửa sổ ngày–giờ được xử lý.
- `privacy`: bắt buộc buffer đúng 1 frame, cấm persistent output.

Schema cố ý từ chối các trường lạ như `rtsp_url`, `student_id`, `name`, face
model hoặc embedding, để các dữ liệu đó không thể vô tình đi vào config.
