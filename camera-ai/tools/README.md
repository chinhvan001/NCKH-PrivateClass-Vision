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

## Calibrate the detector and posture thresholds

`calibrate_pose.py` measures on SCB-Dataset (`scb`) and on a classroom video (`video`):

- the share of labelled students found for each `image_size`, `tile_size` and `pose_confidence`;
- `head_drop_ratio` by behaviour (hand-raising, read, write);
- GPU speed, and how continuously each seat position is detected;
- the alerts the real `EngagementEngine` raises for each threshold.

Results and decisions of 15 November 2026: [docs/calibration.md](../docs/calibration.md).

```powershell
python tools/calibrate_pose.py scb --dataset D:\Document\PCV\Temp-data\archive\SCB-Dataset --output reports\calibration_scb.json
python tools/calibrate_pose.py video --video D:\Videos\lop.mov --head-thresholds 0.3 0.4 --output reports\calibration_video.json
```

Like the tools above, it keeps frames in RAM only. The JSON holds aggregate numbers and the time and seat of each alert, never boxes, keypoints or images.

## Cut a video into one-person action clips for review

`cut_action_clips.py` builds a set for people to review the recognition clip by clip:

1. A first pass at 5 Hz finds the seat positions, each seat's torso angle and its frontal pose (`FrontalBaseline`: the frames where the eyes are furthest apart). It labels each frame with the same rules as `EngagementEngine`, which live in `src/engagement/posture_monitor.py`, checked in this order:
   1. slumped over (`is_slumped_over`) counts as drowsy;
   2. head down against the frontal pose (`is_head_down`) counts as reading or writing;
   3. head turned against the frontal pose counts as a head turn.
2. It keeps every 2-second window in which one student is seen in at least 80% of frames and one action covers at least 70% of them. It searches in steps of `--step` (0.2 s), and windows of the same seat never overlap. `--clips 0`, the default, keeps them all; a positive number spreads that many across actions.
3. For each window it runs detection again on every frame, at `image_size` 1280 on the full frame as the edge node does, and records the result.
4. `index.html` in the output folder plays every clip next to the system's answer. Reviewers mark it right or wrong, pick the real action, and export a CSV. Each run stores its marks under its own key, so a new run never shows the marks of an old one.

`--review` takes the CSV exported from an earlier round. The tool then:

- scores those windows again with the current rules and writes `rescore.json`, which holds accuracy, per-label counts and a confusion list, and checks that the seat numbering matches the earlier round;
- leaves those windows out of the new cut, so reviewers only see new clips.

With `--merge-reviewed`, the tool cuts those windows too, into one set with the new ones. Each of them starts with the real action the reviewer chose last time, for a second look.

```powershell
python tools/cut_action_clips.py --video D:\Videos\lop.mov --output D:\Videos\lop_clips_v2 --review ..\doc\danh_gia_clip.csv --allow-persistent-output
```

Unlike the tools above, this one writes images of students to disk. It does so only with `--allow-persistent-output`, and it refuses an output folder inside the repo.

- `anonymize_preview()` pixelates the whole frame to 32x24, which would hide the action. Instead, the head of every detected person in the clip is pixelated, sized from the shoulders and head keypoints, and the body stays visible.
- `--no-face-blur` writes the clips without pixelating heads, so reviewers can see where each student is looking. Use it only for footage of team members who agreed to be filmed; the default stays blurred.
- Keep the output folder off git and off any shared drive, and delete it after the review.
- The clips are too short to trigger the timed alerts (head drop 5 s, back turn 2 s), so they test per-frame posture recognition.
- Side conversation needs two people facing each other, so only its head-turn part is reviewed.
