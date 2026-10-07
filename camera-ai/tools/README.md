# Công cụ dữ liệu giả lập

`generate_synthetic_classroom.py` tạo video bằng hình học 2D: lớp học, bàn ghế
và silhouette không khuôn mặt. Không dùng ảnh, video, giọng nói hay bất kỳ dữ
liệu nào từ học sinh/người thật.

```powershell
python tools/generate_synthetic_classroom.py --output data/synthetic.mp4 --seats data/synthetic_seats.json --labels data/synthetic_labels.jsonl
```

Kết quả gồm video mô phỏng, seat grid tương thích demo và JSONL nhãn kịch bản:
`normal` (0–3s, 10–12s), `side_conversation` (3–7s), `turning_back` (7–10s).
Nhãn chỉ để kiểm thử luồng UI/cảnh báo; video vector này không dùng để đánh giá
độ chính xác phát hiện người của YOLO trên CCTV thật.

## Đo độ bao phủ phát hiện người trên SCB-Dataset

`evaluate_person_detection.py` đối chiếu prediction với ground truth theo IoU
(mặc định 0,50). `recall_detection_success` là tỷ lệ người có nhãn thật đã
được phát hiện; kèm theo precision và F1 để tránh tối ưu bằng cách sinh quá
nhiều box. Báo cáo tách theo thư mục ảnh (góc camera) và mật độ nhãn: 1–5,
6–15, và từ 16 người.

```powershell
# COCO JSON
python tools/evaluate_person_detection.py --images D:\SCB-Dataset\images --annotations D:\SCB-Dataset\annotations\instances.json --output reports\scb_person_metrics.json

# YOLO labels (class 0 là person)
python tools/evaluate_person_detection.py --images D:\SCB-Dataset\images --annotations D:\SCB-Dataset\labels --format yolo --output reports\scb_person_metrics.json
```

Công cụ không tạo ảnh debug/preview: mỗi khung chỉ tồn tại trong RAM cho lần
suy luận rồi được giải phóng. JSON đầu ra chỉ gồm số liệu tổng hợp ẩn danh.

## Tạo ground truth person cho SCB

Xem [hướng dẫn quy trình duyệt](../data/person_gt_review/README.md). Công cụ
`prepare_person_ground_truth.py` chọn ảnh validation đa bối cảnh và tạo box đề
xuất để kiểm duyệt; ảnh gốc không bị sao chép. Proposal không được dùng làm
ground truth hoặc để công bố metric.
