# Edge Node

One edge node serves one camera, in the room of one class. It waits for a monitoring session of that class in Firestore and processes the camera only while that session is running and inside the configured schedule. It writes live seat states, per-seat evaluations, alerts and a heartbeat, all on the team's Firestore schema. This page covers running it and its side of the Firestore contract. Paths and delivery guarantees are in `src/sync/README.md`; the contract with the web admin and the app, including what they still have to build, is in `docs/web_admin_integration.md`.

## Run

From `camera-ai/`:

```powershell
$env:CAMERA_ROOM_201_SOURCE = "rtsp://..."                          # the name set in camera.source_env
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/secrets/edge-room-201.json"  # kept outside the repo
python -m src.main --config config/local_pipeline.json
```

| Option | Meaning |
|---|---|
| `--config` | Local config, see `config/README.md`. Required. |
| `--model` | YOLOv8-pose weights. Default `models/yolov8n-pose.pt`. |

Exit code 2 means the config is invalid or the camera source variable is unset. Exit code 1 means credentials or the model are missing. Ctrl+C or SIGTERM closes a running session as `incomplete` and marks the heartbeat offline.

How each config section is used:

| Section | Effect |
|---|---|
| `camera` | `class_id` selects the sessions to follow and the seat plan to load; `camera_id` names the heartbeat document and is written into results. The camera source is read from the environment variable named in `source_env`. `angle_type` enables back-turn detection for `frontal` cameras only. |
| `seating` | Image position of the four corner seats; every seat's position is derived from them (`config/README.md`). |
| `sampling` | Capture FPS. Pose inference runs on every n-th frame; the other frames are wiped without processing. |
| `thresholds` | Pose detector settings, side-conversation and back-turn detectors. |
| `schedule` | The camera opens only inside these local-time windows, even while a session is running. |
| `privacy` | One-frame buffer, no persistent output, `retention_days` for `expire_at`. |

## Session control (written by the web admin or app)

The edge node listens to the top-level `sessions` collection, filtered on `class_id` equal to `camera.class_id`:

| `status` | Edge node |
|---|---|
| `scheduled` | Ignored. |
| `running` | Starts the session if none is running: loads the class seat plan, then opens the camera inside the schedule. |
| `paused` | Closes the camera and pauses alerts. Going back to `running` reopens it, and behaviour episodes start over. |
| `ended` | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| `cancelled`, document deleted, or any other value | Closes the camera and sets `monitoring_status` to `incomplete`. |

Until the `Web` branch switches to the schema, `live` counts as `running` and `completed` as `ended`.

The edge node reads only `class_id` and `status`; `started_at` and `ended_at` are ignored, and the `schedule` windows bound when the camera may open.

- Keep at most one `running` or `paused` session per class. If there are several, the edge node takes the one with the smallest ID.
- Session IDs must match `[A-Za-z0-9_-]{1,64}`. Firestore auto-IDs do.
- The seat plan is loaded when the session starts and fixed for the whole session: `row_count`/`column_count` from `classes/{class_id}` and `row`/`column` from `classes/{class_id}/seats` (never `student_id`). While a class has no seat documents, seats are numbered `S1`..`Sn` row by row, like the `Web` branch's `seat_assignments`. If the plan cannot be loaded (missing class, more than 50 rows or columns, no valid seat, corner seats not forming a convex quadrilateral, Firestore unreachable), the heartbeat reports `unavailable` and the edge node retries every 10 s.

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
| `completed` | The session was set to `ended`. |
| `incomplete` | The session stopped without being ended (cancelled, document deleted, edge node shut down), or the edge node restarted during it and the scores cover only the part after the restart (UC04 alternate flow). A result still `running` after the session ended means the edge node died; treat it as incomplete. |

## Per-seat evaluations: `session_evaluations/{session_id}_{seat_id}`

Written every 5 minutes of monitored time and when the session stops, one document per seat seen. Fields: `session_id`, `seat_id`, `captured_at`, `concentration` (last 60 s), `avg_concentration` (whole session), `distraction` (alerts of any type for this seat), `observed_sec` (time the seat was seen), `expire_at`.

- Use `observed_sec` to drop seats where someone only walked past, and to weight class averages.
- For reports and exports (UC03, UC11), map `seat_id` to students through `classes/{class_id}/seats`.

## Alerts: `sessions/{session_id}/alerts/{id}`

Fields: `session_id`, `seat_id`, `type` (`head_drop`, `back_turn`, `side_conversation`), `start_sec`, `duration_sec`, `expire_at`. The teacher adds `status` (`acknowledged` or `dismissed`); an alert without `status` is new.

## Heartbeat: `edge_nodes/{camera_id}`

Written every 10 s and on every status change. Fields: `class_id`, `online`, `status`, `session_id`, `fps` (inferred frames per second), `camera_ok`, `last_frame_at`, `updated_at`.

| `status` | Meaning |
|---|---|
| `idle` | No running session. |
| `monitoring` | Session running, frames arriving. |
| `paused` | Session paused, camera closed. |
| `unavailable` | Session running, but the camera sent no frame for 5 s or could not be opened (retried every 10 s), or the seat plan could not be loaded. Show "temporarily unavailable" (UC02). |
| `outside_schedule` | Session running outside the schedule windows. The camera stays closed. |

- Treat the node as offline when `online` is false or `updated_at` is more than 30 s old. Timestamps come from the edge clock in UTC, so keep NTP enabled on edge nodes.
- `camera_ok` is null until the camera has been opened once. The edge node never opens the camera outside a session just to test it, so before a session `camera_ok` reflects the previous one.
- UC04 step 3 (check before starting): the class has a seat plan, and the heartbeat is online and recent.

## Timing

`captured_at`, `expire_at` and the heartbeat's timestamps are UTC wall-clock times from the edge clock. Results and evaluations are paced by monitored time, so a pause writes nothing. `start_sec` (alerts) counts seconds of monitored time since the session started; a pause or a camera outage advances that clock by at most 5 s, so it is not wall-clock time since the start. Alert times are rounded to 0.1 s.

## Known limits

- The Firestore listener dies when the network drops (a reconnect recursion in `google-api-core`). The edge node subscribes again once its Firestore writes succeed. Until then it keeps the last session state it saw, so a session ended during an outage is closed only after reconnection. The schedule still bounds when the camera can be open.
- Opening an unreachable RTSP camera can block the loop for about 30 s (OpenCV timeout), during which the heartbeat is not refreshed.
- One camera per class: `session_results` uses the session ID as its document ID.
- Alert push notifications (FCM, UC09) are not built.
