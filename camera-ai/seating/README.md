# Module `seating/` — Pseudonymous Spatial Seating Mapping

Gán mỗi khung xương (skeleton, từ `PoseDetector`) vào một **seat_id** dựa trên vị trí không gian trong khung hình — **không dùng bất kỳ hình thức nhận diện danh tính nào**. Đây là thành phần thay thế vai trò "nhận diện" mà hướng cũ (facial landmark) từng đảm nhiệm một phần, đúng tinh thần Proposal chính thức (Pseudonymous Spatial Tracking).

## Thành phần

| File | Vai trò |
|---|---|
| `seat_grid.py` | `Seat`, `SeatGrid` — định nghĩa lưới chỗ ngồi đã hiệu chỉnh (calibrate), đọc/ghi từ file JSON cục bộ. |
| `seat_mapper.py` | `assign_seats()` — gán seat cho **một khung hình đơn lẻ**, thuật toán nearest-centroid. |
| `seat_tracker.py` | `SeatTracker` — duy trì `seat_id` **ổn định qua nhiều khung hình liên tiếp**, xử lý nhiễu (jitter) và khuất tạm thời. **Dùng cái này trong pipeline thật**, không dùng trực tiếp `assign_seats()` trừ khi chỉ cần xử lý 1 ảnh tĩnh. |

## 1. Calibration — xác định vị trí từng ghế

Trước khi dùng, cần một file JSON mô tả toạ độ trung tâm từng ghế trong khung hình camera **của đúng góc lắp đặt camera đó**:

```json
{
  "seats": [
    {"seat_id": "A1", "center_x": 120, "center_y": 340},
    {"seat_id": "A2", "center_x": 260, "center_y": 340},
    {"seat_id": "B1", "center_x": 120, "center_y": 480}
  ]
}
```

Cách tạo file này ở giai đoạn hiện tại (chưa có UI admin-web — đó là việc của Danh, xem ghi chú trong `reorganized-tasks-post-pivot.md`):

1. Chụp một khung hình tĩnh từ camera lớp học thật.
2. Mở ảnh đó bằng công cụ xem ảnh có toạ độ pixel (hoặc viết script nhỏ dùng `cv2.imshow` + bắt sự kiện click chuột) để xác định toạ độ (x, y) trung tâm từng ghế.
3. Đặt tên `seat_id` theo quy ước dễ đọc (ví dụ `A1`, `A2` theo hàng-cột), lưu thành file JSON như trên.
4. Nạp bằng `SeatGrid.from_json_file("path/to/seat_grid.json")`.

**Lưu ý quan trọng**: `SeatGrid` gắn với **một cách lắp đặt camera cụ thể** (góc quay, vị trí). Nếu camera bị dịch chuyển hoặc lắp ở phòng khác, phải calibrate lại từ đầu.

## 2. Gán seat cho một khung hình (`assign_seats`)

Thuật toán: lấy **trung điểm 2 vai** (`left_shoulder`, `right_shoulder`) của mỗi người làm vị trí đại diện, rồi gán vào seat có tâm **gần nhất** (nearest-centroid). Dùng trung điểm vai thay vì đầu/mũi vì đây là điểm ổn định nhất trên thân trên, ít bị lệch khi học sinh cúi/ngả đầu — đúng thứ sẽ bị đo ở task tiếp theo (head drop/slumping), nên không thể dùng để định vị người.

```python
from src.seating import SeatGrid, assign_seats

grid = SeatGrid.from_json_file("config/seat_grid.json")
assignments = assign_seats(people, grid, max_distance=80.0)
```

Nếu 2 người cùng gần nhất với 1 ghế (đứng sát nhau, hoặc calibration chưa chuẩn), chỉ người gần tâm ghế hơn được gán — không bao giờ có 2 người cùng mang 1 `seat_id` trong cùng một khung hình.

## 3. Ổn định qua thời gian (`SeatTracker`) — dùng cho pipeline thật

`assign_seats()` xử lý độc lập từng khung hình — nếu dùng trực tiếp trong vòng lặp video, một người ngồi yên vẫn có thể bị "nhảy" `seat_id` qua lại giữa 2 ghế gần nhau chỉ vì nhiễu (jitter) nhỏ trong toạ độ keypoint từ YOLOv8-pose. `SeatTracker` giải quyết việc này bằng 2 cơ chế:

### Tính liên tục (continuity)
Nếu vị trí hiện tại gần vị trí đã biết gần đây nhất của một ghế đang được theo dõi (trong phạm vi `continuity_threshold`), giữ nguyên `seat_id` đó — **không** tính lại nearest-centroid từ đầu. Chỉ khi không khớp với track nào đang có (người mới xuất hiện, hoặc ghế đã "mất dấu" quá lâu), mới fallback về nearest-centroid thô.

### Xử lý khuất tạm thời (occlusion)
Một ghế không bị coi là "trống" ngay khi một khung hình không phát hiện được người ở đó (học sinh cúi thấp, bị che một phần). Ghế được giữ trong trạng thái theo dõi tối đa `max_missing_frames` khung hình liên tiếp trước khi thực sự bị xoá.

```python
from src.seating import SeatGrid, SeatTracker

grid = SeatGrid.from_json_file("config/seat_grid.json")
tracker = SeatTracker(grid, max_missing_frames=15, continuity_threshold=40.0)

for frame in video_stream:
    people = pose_detector.detect(frame.image)
    stable_assignments = tracker.update(people)  # Dict[seat_id, SeatAssignment]
```

### Chọn `continuity_threshold` thế nào

Giá trị này cần **lớn hơn** mức nhiễu bình thường của detection, nhưng **nhỏ hơn một nửa** khoảng cách tối thiểu giữa 2 ghế liền kề (nếu không sẽ gán nhầm sang ghế bên cạnh khi người đó chỉ hơi nghiêng người). Giá trị cụ thể cần tinh chỉnh bằng thực nghiệm với dữ liệu/video thật — số 40.0 trong ví dụ chỉ là giá trị khởi điểm để test.

## Giới hạn đã biết

- Chưa xử lý trường hợp bố cục lớp thay đổi giữa buổi học (đúng theo Assumption "Fixed Seating Arrangement" của Proposal — học sinh ngồi cố định trong một buổi học).
- `continuity_threshold` và `max_missing_frames` là hằng số cấu hình thủ công, chưa có cơ chế tự động tinh chỉnh theo mật độ lớp học hoặc chất lượng detection thực tế.
- Chưa tích hợp với module `config/` (Sprint 7) để nhận file calibration từ xa qua admin-web — hiện tại chỉ đọc từ file JSON cục bộ.

## Chạy unit test

```bash
python -m pytest tests/seating/ -v
```

Bộ test dùng `PersonPose` giả lập (không cần model/webcam thật), bao gồm test mô phỏng 30 học sinh ngồi cố định qua 10 khung hình liên tiếp có nhiễu ngẫu nhiên, xác nhận không ai bị nhảy `seat_id`.