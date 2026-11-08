# Ground truth person SCB — quy trình duyệt

Mục tiêu là đo `person recall` cho mọi người trong khung, thay vì dùng nhãn
hành vi SCB làm đại diện. Mỗi nhãn chỉ có class `0 = person`; không dùng tên,
track ID, embedding khuôn mặt, hay bất kỳ định danh sinh trắc học nào.

## Tạo proposal đa bối cảnh

```powershell
python tools/prepare_person_ground_truth.py --dataset D:\Document\PCV\Temp-data\archive\SCB-Dataset --output data\person_gt_review --per-scene 12
```

Lệnh chỉ đọc ảnh gốc vào RAM, không copy ảnh. Nó tạo `manifest.jsonl` và các
box đề xuất ở `proposals/`. Các box này **không phải ground truth**.

## Duyệt thủ công

Người kiểm duyệt sửa proposal theo từng ảnh, dùng định dạng YOLO `0 cx cy w h`,
và lưu kết quả vào `ground_truth/<scene>/labels/val/<image>.txt`. Khi duyệt:

1. Box mỗi người thấy được phải có đúng một nhãn; xoá box trùng hoặc box không phải người.
2. Không đánh số, đặt tên, hoặc nối cùng người giữa các ảnh.
3. Đánh dấu `status: reviewed` trong manifest; một người thứ hai kiểm tra ngẫu nhiên ít nhất 20% ảnh.
4. Không sửa `locked_test`; chỉ calibration được dùng để chọn ngưỡng detector.

Tập khởi đầu mặc định có 72 ảnh, 24 locked-test và 48 calibration, trải trên
6 bối cảnh SCB. Mở rộng ưu tiên các ảnh có từ 16 người trở lên sau khi duyệt.

Sau khi hoàn tất, chạy `tools/evaluate_person_detection.py` cho locked-test.
Tuyệt đối không dùng proposal hay nhãn chưa duyệt để báo cáo độ chính xác.
