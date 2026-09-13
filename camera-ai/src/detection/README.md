# Module `detection/` — Face Detector + Face Landmarker (MediaPipe Tasks API)

## Bước bắt buộc trước khi chạy: tải file model

MediaPipe **không đóng gói sẵn file model** trong gói pip — bạn phải tải về
thủ công, cho **cả 2 loại model** (Face Detector và Face Landmarker dùng file
khác nhau). Sandbox dùng để phát triển code này cũng **không tải được** vì bị
chặn domain `storage.googleapis.com`, nên bước này bạn cần tự làm trên máy có
mạng bình thường.

### 1. Face Detector (đã có từ Sprint 2)

1. Tạo thư mục `models/` trong `camera-ai/` (ngang hàng với `src/`) nếu chưa có.
2. Tải file model tại:
   ```
   https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
   ```
   Có thể tải bằng trình duyệt, hoặc PowerShell:
   ```powershell
   Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite" -OutFile "models\blaze_face_short_range.tflite"
   ```
3. Xác nhận đường dẫn cuối cùng là `camera-ai/models/blaze_face_short_range.tflite`.

### 2. Face Landmarker (mới, Sprint 3)

Khác với Face Detector (1 file `.tflite` đơn), Face Landmarker dùng file
`.task` (một bundle đóng gói nhiều model con).

```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" -OutFile "models\face_landmarker.task"
```
Xác nhận đường dẫn cuối cùng là `camera-ai/models/face_landmarker.task`.

URL này đã được đối chiếu với tài liệu mẫu chính thức của Google
(`google-ai-edge/mediapipe-samples`) và gói `@mediapipe/tasks-vision` trên
npm — đáng tin cậy. Nếu Google đổi đường dẫn model trong tương lai (đôi khi
xảy ra), tìm lại tại trang chính thức:
https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker — mục
"Models".

Nếu Google đổi đường dẫn model Face Detector (đôi khi xảy ra), tìm lại tại:
https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector — mục "Models".

### Cấu hình (tuỳ chọn, qua `.env`)

```
FACE_DETECTOR_MODEL_PATH=models/blaze_face_short_range.tflite
FACE_DETECTOR_MIN_CONFIDENCE=0.5

FACE_LANDMARKER_MODEL_PATH=models/face_landmarker.task
FACE_LANDMARKER_MAX_FACES=30
FACE_LANDMARKER_MIN_DETECTION_CONFIDENCE=0.5
FACE_LANDMARKER_MIN_PRESENCE_CONFIDENCE=0.5
FACE_LANDMARKER_MIN_TRACKING_CONFIDENCE=0.5
FACE_LANDMARKER_OUTPUT_MATRIX=1
```

Nếu không set, module dùng đúng các giá trị mặc định ở trên.

**`FACE_LANDMARKER_MAX_FACES` là giá trị quan trọng nhất cần nhớ chỉnh** —
mặc định gốc của MediaPipe là `num_faces=1` (tối ưu cho ứng dụng kiểu selfie).
Vì đây là lớp học có nhiều học sinh, `LandmarkerConfig` đã đặt mặc định thành
`30`, nhưng nếu bạn tự tạo `LandmarkerConfig()` mà không qua `from_env()` và
quên set giá trị này, module sẽ chỉ bao giờ phát hiện được **1 khuôn mặt duy
nhất** trong cả lớp.

## Phạm vi module này

- **`face_detector.py`** (Sprint 2): chỉ phát hiện vị trí khuôn mặt (bounding
  box) + 6 keypoint cơ bản — dùng model BlazeFace short-range, nhẹ và nhanh,
  phù hợp CPU.
- **`face_landmarker.py`** (Sprint 3, mới): 478 điểm landmark chi tiết cho
  từng khuôn mặt + transformation matrix (ma trận 4×4) — làm đầu vào trực
  tiếp cho module `engagement/` ở Sprint 4 (tính head pose từ transformation
  matrix, tính eye-aspect-ratio từ landmark vùng mắt), đúng theo tài liệu
  nghiên cứu Sprint 1.

Hai module này **độc lập nhau** — không bắt buộc phải chạy cả hai cùng lúc.
Trên thực tế, nếu chỉ cần landmark, `FaceLandmarker` tự nó cũng phát hiện
được khuôn mặt (không cần chạy `FaceDetector` trước) — dùng `FaceDetector`
riêng khi chỉ cần bounding box nhanh, nhẹ hơn mà không cần landmark chi tiết.

## Lưu ý kỹ thuật quan trọng (dễ nhầm)

- `bounding_box` (Face Detector) và **landmark points** (cả hai module) mà
  MediaPipe trả về đều là **toạ độ chuẩn hoá 0.0–1.0** — TRỪ `bounding_box`
  của Face Detector là pixel tuyệt đối sẵn. Cả hai module trong thư mục này
  đã tự nhân/không nhân đúng theo từng loại trước khi trả ra
  (`FaceBox`/`FaceLandmarks`) — đây là lỗi rất dễ mắc và khó phát hiện nếu tự
  viết lại (nhầm normalized với pixel, hoặc ngược lại).
- `FaceLandmarks.transformation_matrix` có thể là `None` nếu
  `output_transformation_matrix=False`, hoặc nếu số lượng matrix MediaPipe
  trả về ít hơn số khuôn mặt phát hiện được (trường hợp hiếm nhưng module đã
  xử lý an toàn, không `IndexError`).

## Cách dùng — Face Landmarker

```python
from src.capture import CaptureWorker, CaptureConfig
from src.detection import FaceLandmarker, LandmarkerConfig

worker = CaptureWorker(CaptureConfig.from_env())
worker.start()

with FaceLandmarker(LandmarkerConfig.from_env()) as landmarker:
    try:
        while True:
            frame = worker.buffer.get(timeout=1.0)
            if frame is None:
                continue
            faces = landmarker.detect(frame.image, frame.timestamp)
            for face in faces:
                print(f"{len(face.points)} diem landmark, "
                      f"co transformation matrix: {face.transformation_matrix is not None}")
    finally:
        worker.stop()
```

## Cách dùng — Face Detector

```python
from src.capture import CaptureWorker, CaptureConfig
from src.detection import FaceDetector, DetectionConfig

worker = CaptureWorker(CaptureConfig.from_env())
worker.start()

with FaceDetector(DetectionConfig.from_env()) as detector:
    try:
        while True:
            frame = worker.buffer.get(timeout=1.0)
            if frame is None:
                continue
            faces = detector.detect(frame.image, frame.timestamp)
            for face in faces:
                print(face.x, face.y, face.width, face.height, face.confidence)
    finally:
        worker.stop()
```

## Đã test những gì (chưa cần model thật)

**Face Detector:**
- Import, cấu trúc class, xử lý lỗi khi thiếu file model.
- Logic parse `FaceDetectorResult` → `FaceBox`, dùng đúng dữ liệu mẫu từ tài
  liệu chính thức MediaPipe để đối chiếu (bounding box giữ pixel, keypoint
  nhân đúng với width/height).

**Face Landmarker:**
- Import, xử lý lỗi khi thiếu file model (`FaceLandmarkerError`).
- Logic parse `FaceLandmarkerResult` → `FaceLandmarks` với 2 khuôn mặt cùng
  lúc, quy đổi normalized → pixel đúng cho từng điểm.
- Trường hợp `transformation_matrix` rỗng (tắt tính năng) → trả về `None`
  đúng, không `IndexError`.
- `LandmarkerConfig.from_env()` đọc đúng `max_num_faces` và ép kiểu bool đúng
  cho `FACE_LANDMARKER_OUTPUT_MATRIX`.

**Cả hai module:**
- Logic bảo vệ timestamp tăng dần nghiêm ngặt (yêu cầu bắt buộc của chế độ
  VIDEO trong MediaPipe).
- Pipeline chuyển đổi ảnh BGR (từ OpenCV) → RGB → `mp.Image`.

**Chưa test được** (cần bạn tự làm sau khi tải model): độ chính xác phát
hiện/landmark thật với webcam, FPS thực tế khi chạy `detect()` liên tục trong
vòng lặp thật với nhiều khuôn mặt cùng lúc trong khung hình lớp học, và liệu
`max_num_faces=30` có ảnh hưởng đáng kể đến hiệu năng khi lớp học đông hay
không (cần benchmark ở Sprint 3 tiếp theo).