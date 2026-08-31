# Module `capture/`

Đọc khung hình từ camera lớp học, cấu hình được FPS/độ phân giải, tự động kết
nối lại khi mất tín hiệu tạm thời, và chạy được trên thread nền để không làm
chậm các bước xử lý AI phía sau (`detection/`, `engagement/`...).

## Thành phần

| File | Vai trò |
|---|---|
| `config.py` | `CaptureConfig` — cấu hình nguồn camera, FPS, độ phân giải, tham số reconnect. Đọc được từ `.env` qua `CaptureConfig.from_env()`. |
| `camera_capture.py` | `CameraCapture` — mở/đọc camera qua OpenCV, tự throttle theo FPS, tự kết nối lại khi mất tín hiệu. |
| `frame_buffer.py` | `FrameBuffer` — hàng đợi khung hình thread-safe, tự loại bỏ khung hình cũ nhất khi đầy (drop-oldest). |
| `capture_worker.py` | `CaptureWorker` — chạy `CameraCapture` trên thread nền, tự đẩy khung hình vào `FrameBuffer`. **Đây là cách dùng chính**, các module khác nên dùng `CaptureWorker` thay vì tự quản lý `CameraCapture` + thread. |

## Cài đặt nhanh

Thêm vào `.env` (xem `.env.example`):
```
CAMERA_SOURCE=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=15
```
Bỏ trống `CAMERA_WIDTH`/`CAMERA_HEIGHT` nếu muốn giữ độ phân giải mặc định của camera.

## Cách dùng (khuyến nghị — qua `CaptureWorker`)

```python
from src.capture import CaptureWorker, CaptureConfig, CameraOpenError

worker = CaptureWorker(CaptureConfig.from_env(), buffer_size=5)

try:
    worker.start()  # nem CameraOpenError ngay tai day neu camera khong mo duoc
except CameraOpenError as e:
    print(f"Khong mo duoc camera: {e}")
    raise

try:
    while True:
        frame = worker.buffer.get(timeout=1.0)
        if frame is None:
            continue  # het timeout, chua co frame moi -- binh thuong, thu lai
        print(frame.frame_index, frame.timestamp, frame.image.shape)
        # ... day frame.image sang detection/ o day
finally:
    worker.stop()
```

Chạy thử trực quan (có cửa sổ hiển thị, vẽ bounding box nếu model đã sẵn sàng):
```bash
python detection_test.py
```

## Cách dùng khi chỉ cần đọc đơn giản, không cần thread nền

Chỉ dùng khi script ngắn/một luồng xử lý duy nhất — nếu có bước xử lý AI chạy
sau, luôn ưu tiên `CaptureWorker` ở trên để tránh việc đọc camera bị chậm theo
tốc độ xử lý AI.

```python
from src.capture import CameraCapture, CaptureConfig

with CameraCapture(CaptureConfig.from_env()) as cam:
    for frame in cam.frames():  # generator, tu throttle theo target_fps
        print(frame.frame_index)
```

## Các khái niệm cần hiểu trước khi chỉnh sửa module này

### Vì sao có `FrameBuffer` mà không gọi `detection/` thẳng trong vòng lặp đọc camera?

Đọc camera (I/O-bound) và xử lý AI (CPU-bound) chạy với tốc độ khác nhau. Nếu
gọi trực tiếp, bước đọc camera sẽ bị "chậm theo" bước xử lý AI, làm giảm FPS
thực tế đọc được. `CaptureWorker` tách hai việc này ra hai luồng riêng, nối
với nhau qua `FrameBuffer`.

### Vì sao `FrameBuffer` bỏ khung hình cũ thay vì chờ?

Đây là giám sát gần-thời-gian-thực, không phải ghi hình lưu trữ đầy đủ. Một
khung hình bị trễ vài giây không còn nhiều giá trị để tính mức độ tập trung —
nên khi hàng đợi đầy, `FrameBuffer` chủ động bỏ khung hình **cũ nhất**, giữ
khung hình **mới nhất**. Theo dõi `worker.buffer.dropped_count`: nếu số này
tăng liên tục, nghĩa là bước xử lý phía sau (`detection/`) đang chậm hơn tốc
độ đọc camera — cần giảm `CAMERA_FPS` hoặc tối ưu bước xử lý đó.

### Vì sao `CameraOpenError` ném ra ngay tại `start()`, không phải trong thread nền?

`CaptureWorker.start()` mở camera **đồng bộ trước khi tạo thread**. Nếu để
việc mở camera diễn ra bên trong thread nền, lỗi mở camera thất bại sẽ bị
"nuốt" âm thầm (thread chết ngay lập tức mà code gọi `start()` không hề biết),
rất khó phát hiện. Thiết kế hiện tại đảm bảo lỗi cấu hình sai (sai
`CAMERA_SOURCE`, camera đang bị chiếm dụng...) được phát hiện ngay lập tức.

### Mất kết nối tạm thời được xử lý thế nào?

`CameraCapture` tự phát hiện khi `cv2.VideoCapture.read()` thất bại liên tục,
tự thử kết nối lại theo cơ chế backoff tăng dần (`reconnect_initial_delay` →
nhân dần theo `reconnect_backoff_factor`, tối đa `reconnect_max_delay`).
`read()`/`frames()` trả về `None`/bỏ qua khung hình trong lúc đang thử kết nối
lại — **không** raise exception, vì đây là tình huống có thể tự phục hồi,
khác với lỗi mở camera lần đầu.

## Chạy unit test

```bash
pip install pytest --break-system-packages   # neu chua co
python -m pytest tests/capture/ -v
```

Bộ test dùng một video giả lập (tạo tự động trong lúc test, không cần webcam
thật) để kiểm tra: mở/đóng camera, throttle FPS, tự kết nối lại khi hết dữ
liệu, và hành vi drop-oldest của `FrameBuffer` — bao gồm cả test chạy nhiều
thread cùng lúc. Xem chi tiết từng test case trong `tests/capture/`.

## Giới hạn đã biết

- `width`/`height` trong `CaptureConfig` chỉ có tác dụng với **camera thật**
  (webcam/IP camera) — không có tác dụng khi `source` là một file video, vì
  OpenCV không resize được khung hình đã ghi sẵn trong file.
- `apply_config()` (dùng khi module `config/` ở Sprint 7 đẩy cấu hình mới từ
  xa xuống) mở lại camera hoàn toàn nếu `source` thay đổi; nếu chỉ đổi
  FPS/độ phân giải thì áp dụng trực tiếp lên kết nối đang mở, không gián đoạn.