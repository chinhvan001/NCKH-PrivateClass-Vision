# Edge Node

One edge node serves one camera, in the room of one class. It waits for a monitoring session of that class in Firestore and processes the camera only while that session is running and inside the configured schedule. It writes live seat states, per-seat evaluations, alerts and a heartbeat, all on the team's Firestore schema. This page covers running it and its side of the Firestore contract. Paths and delivery guarantees are in `src/sync/README.md`; the contract with the web admin and the app, including what they still have to build, is in `docs/web_admin_integration.md`.

## Run

From `camera-ai/`:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/secrets/edge-room-201.json"  # service account key, kept outside the repo
python -m src.main --config config/local_pipeline.json
```

The variable can also go in a `.env` file (gitignored) in `camera-ai/` or at the repository root; variables already set in the shell take precedence. The camera and its class are added on the web admin ([Connect the camera](#connect-the-camera)).

| Option | Meaning |
|---|---|
| `--config` | Local config, see `config/README.md`. Required. |
| `--model` | YOLOv8-pose weights. Default `models/yolov8n-pose.pt`. |
| `--check-camera [SECONDS]` | Only read the camera for 5 s (or `SECONDS`), print its resolution and frame rate, then exit. See [Connect the camera](#connect-the-camera). |
| `--video FILE` | Use a video file instead of the camera. See [Test with a video](#test-with-a-video-instead-of-the-camera). |

Exit code 2 means the config is invalid, the camera source variable it names is unset, or the `--video` file does not exist. Exit code 1 means credentials or the model are missing, or, with `--check-camera`, that the camera has not been added on the web admin, could not be opened or sent no frame. Ctrl+C or SIGTERM closes a running session as `incomplete` and marks the heartbeat offline.

## Connect the camera

### On the web admin

Leave `camera.class_id` and `camera.source_env` at `null` in the local config, as in `config/local_pipeline.example.json`, and set `camera.camera_id`. Start the edge node: it shows up on the web admin's camera page as "Chờ thêm camera trên web" (heartbeat status `unconfigured`). Press "Thêm" on that row, or "Thêm camera" with the same camera name, and fill in:

| Field | Value |
|---|---|
| Phòng học | An existing room, or the name of a new one. |
| Tên camera | The edge node's `camera.camera_id`. |
| Lớp theo dõi | The class whose sessions the camera monitors. A class has at most one camera. |
| Hãng camera, Địa chỉ IP, RTSP Port, Đường dẫn luồng | The camera's address. The brand fills in the stream path from the table below. |
| Tài khoản camera, Mật khẩu camera | The camera's own account. |

The web backend stores the camera's room and name in `cameras/{camera_id}`, and percent-encodes the account into an RTSP URL in `camera_configs/{camera_id}`. Rules deny `camera_configs` to every client, admins included, and the API never returns the URL; only the edge node reads it. The class gets `classes2/{class_id}.camera_id`, and the edge node finds its class with a query on that field which asks for nothing else.

The edge node picks a new camera up within 15 s and a class change within a minute, always between sessions: a running session keeps its class. It reads the URL again each time it opens the camera, so a changed address or password applies from the next session. To change them, right-click the camera on the web admin and choose "Chỉnh sửa thông tin".

### On the edge node

A field set in the local config takes precedence over the web admin. `camera.class_id` fixes the class. `camera.source_env` names an environment variable that holds the source:

- USB webcam: its index, `0` for the first one. `camera.width` and `camera.height` set its resolution.
- IP camera: its RTSP URL, `rtsp://user:password@192.168.1.64:554/<path>`. Percent-encode `@`, `:`, `/` and `#` in the password (`@` becomes `%40`), otherwise the URL breaks; the web admin does this itself. Logs and error messages hide everything between `://` and the last `@` either way.

### Stream paths

| Brand | Main stream | Sub stream |
|---|---|---|
| Hikvision, HiLook | `/Streaming/Channels/101` | `/Streaming/Channels/102` |
| Dahua, KBVision, Imou | `/cam/realmonitor?channel=1&subtype=0` | `/cam/realmonitor?channel=1&subtype=1` |
| TP-Link Tapo | `/stream1` | `/stream2` |

For other brands, see the camera's manual, or run ONVIF Device Manager (free, Windows): it finds the ONVIF cameras on the network and shows each stream's URL. A Tapo camera needs a camera account created in the Tapo app (camera settings, Advanced Settings, Camera Account). An Imou camera usually takes `admin` with the safety code printed on its label. A camera with neither RTSP nor ONVIF cannot be read.

### Check the connection

Before the first session:

```powershell
python -m src.main --config config/local_pipeline.json --check-camera
# Camera rtsp://***@192.168.1.64:554/Streaming/Channels/101: 1280x720, 10.0 fps trong 5s (capture_fps 10).
```

The check opens the camera the way a session does, without the model, and keeps frames in memory only, wiping each one. It needs `GOOGLE_APPLICATION_CREDENTIALS` only when the URL comes from the web admin. It is a manual installation step: the running edge node still opens the camera only during a session. To look at the image, open the same URL in VLC (Media, Open Network Stream); that is also where to take the snapshot for drawing seats (`config/README.md`).

- An IP camera sends the resolution set in its own settings: `camera.width`/`height` cannot change it, and the edge node logs a warning when they differ. Give the stream it reads about 1280x720, in the camera's settings or by choosing the sub stream if that one is at least 720p. The pixel thresholds assume about that size, and 2K or 4K frames make pose inference several times slower.
- A network stream is read at the camera's own frame rate and only the newest frame is kept at `sampling.capture_fps`, so frames do not queue up in the stream buffers and lag behind.
- A network camera that does not answer fails after 10 s, when opening or reading. The heartbeat then reports `unavailable` and the edge node retries every 10 s.

How each config section is used:

| Section | Effect |
|---|---|
| `camera` | `camera_id` names the heartbeat document and the camera on the web admin, and is written into results. `class_id` selects the sessions to follow and the seat plan to load, and the camera source is read from the environment variable named in `source_env`; either one `null` comes from the web admin. `angle_type` enables back-turn detection for `frontal` cameras only. |
| `seating` | Image position of the four corner seats, from which every seat's position is derived, or `null` when the seats are drawn on the web admin (`seat_regions/{camera_id}`, which take precedence; `config/README.md`). |
| `sampling` | Capture FPS. Pose inference runs on every n-th frame; the other frames are wiped without processing. |
| `thresholds` | Pose detector settings, side-conversation and back-turn detectors. |
| `schedule` | The camera opens only inside these local-time windows, even while a session is running. |
| `privacy` | One-frame buffer, no persistent output, `retention_days` for `expire_at`. |

## Test with a video instead of the camera

`--video` replaces the camera with a video file, to test recognition when the camera is out of reach:

```powershell
python -m src.main --config config/local_pipeline.json --video D:/videos/lesson.mp4 --check-camera  # opens the file only
python -m src.main --config config/local_pipeline.json --video D:/videos/lesson.mp4
```

- The rest works as in a real lesson. The edge node follows the class's sessions and writes the same documents. It reads the video only while a session is running inside `schedule`; to test outside those hours, widen `schedule` in a test config. The camera source in the config or on the web admin is not used.
- The video plays in real time, like a camera. Frames that pass while the edge node is busy are skipped, so posture durations and alerts keep their real timing. At the end, the video starts again from the beginning. People jump at that point, so use a video longer than the test.
- The seats must match the video. One way is to take a snapshot of the video in VLC (Video, Take Snapshot) and draw the seats over it in "Xác định chỗ ngồi" on the web admin. The other is to set `seating.corner_seats` from that snapshot.
- Results from a video are stored like those of a real lesson. Use a test session, and delete it on the web admin afterwards; this also deletes its edge documents.
- A recording of a real class is personal data. Use one made with consent, keep it outside the repository, and delete it after testing.

To test without Firebase or a camera, run the offline demo: `camera-ai/venv/Scripts/python backend/tests/demo_server.py --video lesson.mp4`, from the repository root.

- YOLO runs on the video instead of the simulated poses.
- The demo's CAM-1 plays the video, so "Lấy ảnh từ camera" in "Xác định chỗ ngồi" returns a frame of it. Draw the seats over that frame before starting the 11B2 lesson.

## Session control (written by the web admin or app)

The edge node listens to the top-level `sessions` collection, filtered on `class_id` equal to its class (`camera.class_id`, or the class set for the camera on the web admin):

| `status` | Edge node |
|---|---|
| `scheduled` | Ignored. |
| `running` | Starts the session if none is running: loads the class seat plan, then opens the camera inside the schedule. |
| `paused` | Closes the camera and pauses alerts. Going back to `running` reopens it, and behaviour episodes start over. |
| `completed` | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| `cancelled`, document deleted, or any other value | Closes the camera and sets `monitoring_status` to `incomplete`. |

The web admin sets these values (`backend/routes/session_routes.py`); the older `live` still counts as `running` and `ended` as `completed`.

The edge node reads only `class_id` and `status`; `started_at` and `ended_at` are ignored, and the `schedule` windows bound when the camera may open.

- Keep at most one `running` or `paused` session per class. If there are several, the edge node takes the one with the smallest ID.
- Session IDs must match `[A-Za-z0-9_-]{1,64}`. Firestore auto-IDs do.
- The seat plan is loaded when the session starts and fixed for the whole session: only `row_count`/`column_count` from `classes2/{class_id}` (a field projection: the class's `seat_map`, which maps seats to students, is never read). Seats are numbered `S01`, `S02`, ... row by row, the same keys the web admin writes in `seat_map`. Seat positions come from `seat_regions/{camera_id}` when an admin drew them for this class on the web admin's camera page (rectangles in pixels of a snapshot, scaled to the stream's resolution; a person counts for a seat only inside its rectangle, and seats without one are not tracked), otherwise from the corner seats. If the plan cannot be loaded (missing class, more than 50 rows or columns, corner seats not forming a convex quadrilateral, no usable drawn seat and no corner seats, Firestore unreachable), the heartbeat reports `unavailable` and the edge node retries every 10 s.

## Live seat states: `session_results/{session_id}`

Written when the session starts, then every 10 s of monitored time, and once more when it stops. Fields: `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map`, `expire_at`. `result_map` holds one entry per seat seen so far:

| Field | Meaning |
|---|---|
| `concentration` | 0–100 score over the last 60 s; null when the seat is `away`. |
| `interaction` | Side-conversation alerts for this seat since the session started. |
| `status` | `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s). |

| `monitoring_status` | Meaning |
|---|---|
| `running` | Written while the session runs. |
| `completed` | The session was set to `completed`. |
| `incomplete` | The session stopped without being ended (cancelled, document deleted, edge node shut down), or the edge node restarted during it and the scores cover only the part after the restart (UC04 alternate flow). A result still `running` after the session ended means the edge node died; treat it as incomplete. |

## Per-seat evaluations: `session_evaluations/{session_id}_{seat_id}`

Written every 5 minutes of monitored time and when the session stops, one document per seat seen. Fields: `session_id`, `seat_id`, `captured_at`, `concentration` (last 60 s), `avg_concentration` (whole session), `distraction` (alerts of any type for this seat), `observed_sec` (time the seat was seen), `expire_at`.

- Use `observed_sec` to drop seats where someone only walked past, and to weight class averages.
- For reports and exports (UC03, UC11), map `seat_id` to students through `sessions/{session_id}/monitored_students`, the seating the web admin freezes when the session starts (`docs/web_admin_integration.md`).

## Posture windows: `session_windows/{session_id}_{run}_{seq}`

Written with every `session_results` update (every 10 s of monitored time) and once more when the session stops. The web backend's scoring worker reads them (`docs/backend_scoring_and_schema_proposal.md`, Part 1). No client reads them.

Fields: `session_id`, `camera_id`, `run`, `seq`, `start_sec`, `end_sec` (monitored seconds of this run), `captured_at`, `monitoring_status` (`running`; the last window says `completed` or `incomplete`), `seats`, `expire_at`.

- `run` is 8 random hex characters, new each time the edge node starts or resumes the session; the session clock restarts at 0 in each run.
- `seq` counts the run's windows from 0.

`seats` holds one entry per seat seen during the window:

| Field | Meaning |
|---|---|
| `normal_sec`, `slumping_sec`, `head_drop_sec` | Time in each posture state during the window. The time between two sightings belongs to the state of the later one; a gap of more than 30 s counts for nothing. Their sum never exceeds the window. |
| `last_seen_sec` | Monitored second of the last sighting. |
| `last_state` | `normal`, `slumping` or `head_drop` at that sighting. |
| `last_behaviour_sec` | Monitored second of the last back turn or side conversation in the window, or null. |
| `alerts` | Alerts of this seat that started in the window, per type; types with none are left out. |

## Alerts: `sessions/{session_id}/alerts/{id}`

Fields: `session_id`, `seat_id`, `type` (`head_drop`, `back_turn`, `side_conversation`), `start_sec`, `duration_sec`, `expire_at`. The web admin or the teacher adds `status` (`acknowledged` or `dismissed`), `handled_by` and `handled_at`; an alert without `status` is new.

## Heartbeat: `edge_nodes/{camera_id}`

Written every 10 s and on every status change. Fields: `class_id`, `online`, `status`, `session_id`, `fps` (inferred frames per second), `camera_ok`, `last_frame_at`, `updated_at`.

| `status` | Meaning |
|---|---|
| `idle` | No running session. |
| `monitoring` | Session running, frames arriving. |
| `paused` | Session paused, camera closed. |
| `unavailable` | Session running, but the camera sent no frame for 5 s or could not be opened (retried every 10 s), or the seat plan could not be loaded. Show "temporarily unavailable" (UC02). |
| `outside_schedule` | Session running outside the schedule windows. The camera stays closed. |
| `unconfigured` | The local config leaves the class to the web admin, and the camera has not been added there yet. `class_id` is null. |

- Treat the node as offline when `online` is false or `updated_at` is more than 30 s old. Timestamps come from the edge clock in UTC, so keep NTP enabled on edge nodes.
- `camera_ok` is null until the camera has been opened once. The edge node never opens the camera outside a session just to test it, so before a session `camera_ok` reflects the previous one.
- UC04 step 3 (check before starting): the class has a seat plan, and the heartbeat is online and recent.

## Timing

`captured_at`, `expire_at` and the heartbeat's timestamps are UTC wall-clock times from the edge clock. Results and evaluations are paced by monitored time, so a pause writes nothing. `start_sec` (alerts) counts seconds of monitored time since the session started; a pause or a camera outage advances that clock by at most 5 s, so it is not wall-clock time since the start. Alert times are rounded to 0.1 s.

## Known limits

- The Firestore listener dies when the network drops (a reconnect recursion in `google-api-core`). The edge node subscribes again once its Firestore writes succeed. Until then it keeps the last session state it saw, so a session ended during an outage is closed only after reconnection. The schedule still bounds when the camera can be open.
- Opening a network camera that does not answer blocks the loop for up to 10 s, so the heartbeat can be up to about 20 s old meanwhile (the web admin treats 30 s as offline).
- One camera per class: `session_results` uses the session ID as its document ID. The web admin refuses a second camera for a class.
- The class set on the web admin is read again every minute while no session runs (every 15 s until the camera is added), about 1,500 reads a day per edge node.
- With per-node custom tokens (option B in `docs/firestore_security_review.md`) the class is a token claim: mint the token again after changing a camera's class on the web admin.
- Alert push notifications (FCM, UC09) are not built.
