# Firestore seat grid

Mỗi camera đọc duy nhất document:
`classrooms/{classroom_id}/camera_configs/{camera_id}`.

```json
{
  "schema_version": 1,
  "config_version": 3,
  "camera_id": "cam-01",
  "classroom_id": "room-a",
  "camera_angle_type": "frontal",
  "seats": [{"seat_id": "A1", "center_x": 320, "center_y": 420}]
}
```

`config_version` phải tăng mỗi lần hiệu chỉnh. Client poll `refresh()` theo
lịch cục bộ; chỉ thay grid khi version mới hơn. Khi Firestore lỗi, giữ config
đã xác thực trong RAM; nếu chưa từng nhận được config, mới dùng file fallback
cục bộ. Không có ảnh, URL camera, tên người học, ID người học, track ID hoặc
biometric trong document. Quy tắc Firestore phải chỉ cho service account camera
đọc document đúng lớp/camera của nó; quyền ghi chỉ dành cho dịch vụ calibration.
