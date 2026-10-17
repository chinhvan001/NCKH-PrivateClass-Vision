# Local config schema

Copy `local_pipeline.example.json` to a local file that stays out of Git (for example `local_pipeline.json`). The camera source is not in the JSON: put it in the environment variable named by `camera.source_env`, for example:

```powershell
$env:CAMERA_ROOM_201_SOURCE = "rtsp://..."
```

Then start the edge node with `python -m src.main --config config/local_pipeline.json` (see `docs/edge_node.md`).

Sections (`schema_version` 2):

- `camera`: `camera_id` (for example `Camera 201`, also the name of the heartbeat document `edge_nodes/{camera_id}`), `class_id` (the `classes` document of the class taught in this room), resolution, the **name** of the environment variable holding the camera source, and `angle_type` (`frontal` or `top_down`; back-turn detection runs only for `frontal`).
- `seating.corner_seats`: pixel position, in the camera image, of the centre of the four corner seats (see below).
- `sampling`: capture FPS, and run pose inference on every n-th frame.
- `thresholds`: pose and alert thresholds.
- `schedule`: an IANA timezone and the weekday/time windows in which the camera may be opened. Outside them the edge node keeps the camera closed even if a session is running. The timezone is validated at load; on Windows this needs the `tzdata` package from `requirements.txt`.
- `privacy`: a buffer of exactly one frame, no persistent output, and `retention_days`, which sets `expire_at` on every session document the edge node writes (Firestore TTL deletes them after that).

The schema rejects unknown keys such as `rtsp_url`, `student_id`, `name`, face models or embeddings, so that data cannot slip into the config by accident.

## Corner seats

Firestore only knows each seat's row and column (`classes/{class_id}/seats`). Where a seat appears in the image depends on how the camera is mounted, so it stays on the edge node: give the image position of the four corner seats, at shoulder height of a seated student, keyed by their row and column labels in the class seating plan:

| Key | Seat |
|---|---|
| `first_row_first_column` | row 1, column 1 |
| `first_row_last_column` | row 1, last column |
| `last_row_last_column` | last row, last column |
| `last_row_first_column` | last row, column 1 |

The edge node maps every other seat through a perspective transform of this quadrilateral, so seats farther from the camera sit closer together, as they do in the image. The four points must form a convex quadrilateral in this order, otherwise the session's seat layout is rejected and the heartbeat reports `unavailable`.

To find the points, mount the camera as it will stay, have someone sit in each corner seat during setup, and read their shoulder midpoint from the anonymized preview of `tests/demo_camera_ai.py` (nothing is saved unless `--allow-persistent-output` is passed). Recalibrate whenever the camera moves.
