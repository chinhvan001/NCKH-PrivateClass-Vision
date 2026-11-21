# Camera AI settings

Camera AI needs no file per camera. Each camera, with its class, address, angle and seats, is added on the web admin (`docs/edge_node.md`, Connect the camera). This folder holds the optional settings file that every camera on the machine shares.

## Settings file

Without `--settings`, camera AI uses the defaults in `src/config/local_schema.py` (`DEFAULT_SETTINGS`), which are the values in `settings.example.json`. To change them:

1. Copy the example to a local file, for example `settings.json`. Every JSON file here except the example is gitignored.
2. Start camera AI with `python -m src.main --settings config/settings.json`.

Sections (`schema_version` 3):

- `sampling`: the capture FPS, and how often pose inference runs: on every n-th frame. Use 1 on a GPU (`docs/edge_node.md`, GPU).
- `thresholds`: pose and alert thresholds.
- `schedule`: an IANA timezone, and the weekday and time windows in which a camera may be opened. Outside them, the edge node keeps the camera closed even if a session is running.
  - The default is Monday to Saturday, 06:30 to 18:00. The web timetable has Saturday lessons, and its periods run from 07:00 to 17:25.
  - The timezone is checked when the file loads. On Windows this needs the `tzdata` package from `requirements.txt`.
- `privacy`: a buffer of exactly one frame, no persistent output, and `retention_days`. Camera AI deletes a session's data in `edge-data/sessions/` once it is older than that, at start and then daily.

The schema rejects unknown keys such as `camera`, `rtsp_url`, `student_id`, `name`, face models or embeddings, so that such data cannot slip in by accident. A per-camera config from before November 2026 (`schema_version` 2, with `camera` and `seating` sections) is refused with a hint to add the camera on the web admin instead.

## Seat positions

Firestore only knows how many rows and columns the class has (`row_count`, `column_count` on `classes2/{class_id}`). Where each seat appears in the image depends on how the camera is mounted, so an admin draws the seats on the web admin's camera page.

When a session starts, the web admin copies the seats drawn for the camera's class (`seat_regions/{camera_id}`) into the session it gives the camera (`edge-data/camera_sessions/{camera_id}.json`), and refuses to start a lesson until they are drawn. A running session keeps those seats even if they are redrawn.

1. On the camera page, open "Xác định chỗ ngồi" on the camera's row.
2. Drag one rectangle per seat over a snapshot of the camera. The snapshot stays in the admin's browser: only the rectangles are saved, in pixels of the snapshot, together with its size.

How the edge node uses the rectangles:

- It scales them if its frames have another resolution.
- It counts a person for a seat only when the midpoint of their shoulders is inside that seat's rectangle.
- It does not track seats without a rectangle.

Take the snapshot when the classroom is empty, from the same stream and angle camera AI uses. Use "Lấy ảnh từ camera" when the backend has `CAMERA_SNAPSHOT=1`, or VLC: open the RTSP stream, then Video, Take Snapshot. Draw each rectangle around where a seated student's shoulders and upper body appear. Redraw whenever the camera moves.

The edge node no longer uses the four-corner-seat layout (`seating.corner_seats` in `LocalPipelineConfig.from_dict`, `src/seating/seat_layout.py`); only its own tests do.
