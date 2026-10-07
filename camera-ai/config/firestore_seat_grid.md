# Firestore seat grid

Each camera reads exactly one document:
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

`config_version` must increase with every recalibration. The client calls `refresh()` on a local schedule and replaces the grid only when the version is newer. If Firestore fails, it keeps the last validated config in RAM, and falls back to the local file only if it never received one. The document holds no images, camera URLs, student names or IDs, track IDs or biometric data.

No app writes this document yet. The web admin keeps only `row_number` and `column_number` on the classroom, which give no seat positions in the image, so until a calibration screen exists, write it by hand in the Firebase console or pass `--seats` to the edge node. With the web admin, `camera_id` and `classroom_id` are both the classroom document's ID (`docs/web_admin_integration.md`).

The edge node reads this document with the service account key named by `GOOGLE_APPLICATION_CREDENTIALS` (see `src/sync/README.md`). The Admin SDK bypasses Security Rules, so Rules only control the teacher and admin apps that write calibrations. See `firestore.rules` and `docs/firestore_security_review.md`.
