# Local config schema

Copy `local_pipeline.example.json` to a local file (for example `local_pipeline.json`; every JSON file here except the example is gitignored) and set `camera.camera_id`. The camera's class and RTSP URL are added on the web admin's camera page, so the example leaves `camera.class_id` and `camera.source_env` at `null`. Then start the edge node with `python -m src.main --config config/local_pipeline.json` (`docs/edge_node.md`, Connect the camera).

To keep them on the edge node instead, set `camera.class_id`, and put the source in the environment variable named by `camera.source_env`; the JSON never holds the source itself:

```powershell
$env:CAMERA_ROOM_201_SOURCE = "rtsp://..."
```

Sections (`schema_version` 2):

- `camera`: `camera_id` (for example `Camera 201`, also the name of the heartbeat document `edge_nodes/{camera_id}` and of the camera on the web admin), `class_id` (the `classes2` document of the class taught in this room, or `null` for the class set on the web admin), resolution, the **name** of the environment variable holding the camera source (or `null` for the URL entered on the web admin), and `angle_type` (`frontal` or `top_down`; back-turn detection runs only for `frontal`).
- `seating.corner_seats`: pixel position, in the camera image, of the centre of the four corner seats, or `null` when an admin draws the seats on the web admin's camera page (see below).
- `sampling`: capture FPS, and run pose inference on every n-th frame.
- `thresholds`: pose and alert thresholds.
- `schedule`: an IANA timezone and the weekday/time windows in which the camera may be opened. Outside them the edge node keeps the camera closed even if a session is running. The timezone is validated at load; on Windows this needs the `tzdata` package from `requirements.txt`.
- `privacy`: a buffer of exactly one frame, no persistent output, and `retention_days`, which sets `expire_at` on every session document the edge node writes (Firestore TTL deletes them after that).

The schema rejects unknown keys such as `rtsp_url`, `student_id`, `name`, face models or embeddings, so that data cannot slip into the config by accident.

## Seat positions

Firestore only knows how many rows and columns the class has (`row_count`, `column_count` on `classes2/{class_id}`). Where each seat appears in the image depends on how the camera is mounted. When a session starts, the edge node takes the seat positions from:

1. **Seats drawn on the web admin** (`seat_regions/{camera_id}`), when an admin drew them for this config's `camera.class_id`. On the camera page, "Xác định chỗ ngồi" lets an admin drag one rectangle per seat over a snapshot of the camera. The snapshot is opened from the admin's own computer and stays in the browser: only the rectangles are saved, in pixels of the snapshot together with its size. The edge node scales them if its frames have another resolution, and counts a person for a seat only when their shoulder midpoint is inside that seat's rectangle. Seats without a rectangle are not tracked. The web camera's name must be this config's `camera.camera_id`.
2. **The four corner seats** below, otherwise.

Take the snapshot when the classroom is empty, from the same stream and angle the edge node uses (for example VLC: open the RTSP stream, then Video → Take Snapshot), and draw each rectangle around where a seated student's shoulders and upper body appear. Redraw whenever the camera moves.

## Corner seats

Without drawn seats, give the image position of the four corner seats, at shoulder height of a seated student, keyed by their row and column labels in the class seating plan:

| Key | Seat |
|---|---|
| `first_row_first_column` | row 1, column 1 |
| `first_row_last_column` | row 1, last column |
| `last_row_last_column` | last row, last column |
| `last_row_first_column` | last row, column 1 |

The edge node maps every other seat through a perspective transform of this quadrilateral, so seats farther from the camera sit closer together, as they do in the image. The four points must form a convex quadrilateral in this order, otherwise the session's seat layout is rejected and the heartbeat reports `unavailable`.

To find the points, mount the camera as it will stay, have someone sit in each corner seat during setup, and read their shoulder midpoint from the anonymized preview of `tests/demo_camera_ai.py` (nothing is saved unless `--allow-persistent-output` is passed). Recalibrate whenever the camera moves.
