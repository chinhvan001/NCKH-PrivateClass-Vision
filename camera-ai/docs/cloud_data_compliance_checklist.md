# Checklist tuan thu du lieu Cloud

## Ket luan bat buoc

Payload telemetry gui len Cloud chi duoc co dung ba truong: `seat_id`,
`keypoints` (cac cap toa do so `x, y`) va `engagement_score`. Khong co ngoai
le cho anh goc, crop, khuon mat, embedding, bbox, track ID, ten, ma hoc sinh,
URL camera, timestamp chi tiet, hay log suy luan. `seat_id` la ma vi tri ghe,
khong duoc co mapping den danh tinh o bat ky dich vu Cloud nao.

### Alert (UC09)

Canh bao hanh vi la schema rieng, chi co dung nam truong: `session_id`,
`seat_id`, `type`, `start_sec`, `duration_sec`. `type` chi thuoc allowlist
`head_drop`, `back_turn`, `side_conversation` (side conversation phat 1 alert
cho moi ghe, khong co truong cap ghe). `start_sec`/`duration_sec` la giay
tuong doi tu dau phien, lam tron 0.1s -- khong phai wall-clock. `session_id`
la ma opaque ngau nhien (`[A-Za-z0-9_-]{1,64}`), khong ghep ten lop/giao vien.

## Checklist truoc khi bat dong bo

- [ ] Moi diem gui Cloud dung `make_cloud_payload()`; khong tu tao dict.
- [ ] Moi alert gui Cloud/FCM dung `make_alert_event()`; kiem thu `set(alert) == {"session_id", "seat_id", "type", "start_sec", "duration_sec"}`.
- [ ] Kiem thu assertion `set(payload) == {"seat_id", "keypoints", "engagement_score"}`.
- [ ] `keypoints` chi la `[x, y]` so huu han; khong kem confidence, crop hoac bbox.
- [ ] `engagement_score` nam trong 0-100 hoac `null` khi chua du du lieu.
- [ ] `seat_id` la ma ghe da calibration, khong la ten, ma hoc sinh hay persistent person ID.
- [ ] Frame/crop duoc huy sau suy luan; khong co bucket, collection hay queue nao nhan pixel.
- [ ] Firestore seat-grid la config tach biet; collection telemetry khong duoc phep ghi them truong.
- [ ] Firestore Rules/Cloud IAM: camera service account chi ghi collection telemetry duoc cap quyen; dich vu calibration chi ghi document seat-grid.
- [ ] Logging, error reporting va dead-letter queue da redact payload; khong log body day du neu request loi.
- [ ] Review schema va Rules khi them integration; reject unknown fields o server/Cloud Function.

## Bang kiem phat hanh

| Kiem tra | Bang chung can luu | Dat |
|---|---|---|
| Allowlist payload | Unit test `test_cloud_payload.py` | [ ] |
| Allowlist alert | Unit test `test_alert_event.py` | [ ] |
| Khong co pixel | Code review frame lifecycle va transport | [ ] |
| Khong dinh danh ca nhan | Review `seat_id` va Firestore collections | [ ] |
| Phan quyen toi thieu | Firestore Rules va IAM review | [ ] |
| Retention | Cau hinh TTL cho telemetry aggregate | [ ] |

## Can doi chieu Proposal

Repository hien khong chua file Proposal chinh thuc de trich dan muc/so trang.
Truoc khi phat hanh, nguoi phu trach can doi chieu checklist nay voi cac muc
privacy, pseudonymous spatial seating va data-retention trong Proposal; neu
co yeu cau chat hon, schema Cloud phai giam truoc khi trien khai.
