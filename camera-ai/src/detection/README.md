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

Đổi lại, một khung 1080p có thể cần 4 lần suy luận, vì vậy cần đo FPS trên máy
đích. Nếu FPS không đáp ứng, giảm `--imgsz`/`--tile-size` xuống 768 hoặc xử lý
mỗi 2–3 frame; không nên quay lại 640 ngay khi chưa so false-negative trên
video thật. Dùng `--tile-size 0` để tắt tiling khi camera chỉ có khung 720p
hoặc cần benchmark baseline.

Demo dùng hai model song song: `models/yolo11s.pt` chỉ phát hiện class
`person` để đếm/hiển thị **coverage**, còn `models/yolov8n-pose.pt` chỉ tạo
pose phục vụ engagement. Do đó người bị che đến mức không đủ 17 keypoint vẫn
được đếm bằng `people=...`; không được suy diễn điểm engagement cho người đó.
`--person-iou` mặc định 0.70 (khác pose IoU 0.50) để NMS không xoá hai người
ngồi sát nhau trong lớp đông.

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

## Dữ liệu được phép xuất

Chỉ số được phép rời pipeline là `seat_id` theo vị trí (không gắn tên), thời
điểm, điểm engagement, trạng thái tư thế và số sự kiện. Dùng:

```powershell
python tests/demo_camera_ai.py <video> --seats config/seat_grid.json --engagement-jsonl engagement.jsonl
```

JSONL không chứa ảnh, video, khuôn mặt, embedding, keypoint, bounding box, tên
hoặc mã học sinh. Mọi preview/debug phải qua `src.privacy.anonymize_preview()`
trước khi hiển thị/ghi; video overlay bị chặn mặc định.
