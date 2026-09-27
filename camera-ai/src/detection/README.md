# Module `detection/` — Pose-only, không sinh trắc học

> **Chính sách hiện tại:** pipeline chỉ dùng `PoseDetector` (YOLOv8-pose) để
> tính chỉ số tư thế/engagement. Public API `src.detection` không export Face
> Detector, Face Landmarker, facial landmark hay embedding; không dùng những
> dữ liệu này trong runtime hoặc output production.

## Cấu hình CCTV/lớp học đông (PoseDetector)

```powershell
python tests/demo_camera_ai.py <video> --imgsz 960 --tile-size 960 --tile-overlap 0.20
```

- `--imgsz 960` giữ chi tiết hơn mức mặc định 640.
- `--tile-size 960` chia khung CCTV lớn thành các ô giao nhau và gộp pose trùng
  bằng IoU.
- `--confidence 0.20 --max-detections 100` là điểm khởi đầu cho lớp đông; cần
  hiệu chỉnh lại theo video thật để cân bằng false-positive và FPS.

Demo dùng hai model song song: `models/yolo11s.pt` chỉ phát hiện class
`person` để đếm/hiển thị **coverage**, còn `models/yolov8n-pose.pt` chỉ tạo
pose phục vụ engagement. Do đó người bị che đến mức không đủ 17 keypoint vẫn
được đếm bằng `people=...`; không được suy diễn điểm engagement cho người đó.
`--person-iou` mặc định 0.70 (khác pose IoU 0.50) để NMS không xoá hai người
ngồi sát nhau trong lớp đông.

## Dữ liệu được phép xuất

Chỉ số được phép rời pipeline là `seat_id` theo vị trí (không gắn tên), thời
điểm, điểm engagement, trạng thái tư thế và số sự kiện. Dùng:

```powershell
python tests/demo_camera_ai.py <video> --seats config/seat_grid.json --engagement-jsonl engagement.jsonl
```

JSONL không chứa ảnh, video, khuôn mặt, embedding, keypoint, bounding box, tên
hoặc mã học sinh. Mọi preview/debug phải qua `src.privacy.anonymize_preview()`
trước khi hiển thị/ghi; video overlay bị chặn mặc định.

---

## Tài liệu lịch sử (không dùng trong pipeline hiện tại)

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

## Cấu hình CCTV/lớp học đông (PoseDetector)

Demo `tests/demo_camera_ai.py` dùng `PoseDetector` (YOLOv8-pose) cho hướng
không nhận diện danh tính hiện tại. Cấu hình cũ mặc định suy luận ở 640 px và
chỉ quét cả khung một lần; đây là nguyên nhân thường gặp khiến học sinh ở hàng
sau bị quá nhỏ và bị bỏ sót.

Demo hiện mặc định các giá trị ưu tiên **không bỏ sót người**:

```powershell
python tests/demo_camera_ai.py <video> --output annotated.mp4
```

- `--imgsz 960`: tăng độ phân giải đầu vào YOLO.
- `--tile-size 960 --tile-overlap 0.20`: chia khung CCTV lớn thành các ô chồng
  lấp; pose ở vùng chồng lấp được gộp bằng IoU để không đếm đôi.
- `--confidence 0.20 --max-detections 100`: giữ các người xa/có confidence
  thấp và không chặn số người trong lớp.

Đổi lại, một khung 1080p có thể cần 4 lần suy luận, vì vậy cần đo FPS trên máy
đích. Nếu FPS không đáp ứng, giảm `--imgsz`/`--tile-size` xuống 768 hoặc xử lý
mỗi 2–3 frame; không nên quay lại 640 ngay khi chưa so false-negative trên
video thật. Dùng `--tile-size 0` để tắt tiling khi camera chỉ có khung 720p
hoặc cần benchmark baseline.

### Cảnh báo tương tác riêng giữa hai ghế

Khi đã có file `--seats` được calibration, có thể bật thuật toán pose-only:

```powershell
python tests/demo_camera_ai.py <video> --seats config/seat_grid.json --detect-side-conversation
```

Nó chỉ cảnh báo khi hai ghế gần nhau cùng có dấu hiệu quay đầu vào nhau liên
tục 3 giây; không nhận diện danh tính và không tuyên bố họ thực sự đang nói.
Sửa `--conversation-max-distance` theo khoảng cách pixel giữa hai ghế cạnh
nhau và `--conversation-duration` theo quy định lớp học. Muốn xác nhận có lời
nói, cần microphone/luồng âm thanh riêng với xử lý mức năng lượng/voice activity
theo vùng, sau khi có sự đồng ý và chính sách quyền riêng tư phù hợp.

### Cảnh báo quay lưng

Với camera **frontal**, bật `--detect-turning-back` để cảnh báo một ghế có
vai nhìn rõ nhưng các điểm mặt có confidence thấp liên tục. Đây là dấu hiệu
"mặt không hướng camera" (có thể là quay lưng, cúi đầu hoặc bị che), không
phải kết luận quay lưng. Có thể chỉnh `--back-turn-duration` (mặc định 2 giây)
và `--back-turn-max-face-visibility` (mặc định 0.20). Không dùng tín hiệu này
cho camera top-down.

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
