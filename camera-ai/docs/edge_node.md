# Edge Node

One edge node serves one camera. It waits for a monitoring session in Firestore and processes the camera only while that session is active and inside the configured schedule. It writes anonymized records, alerts, a heartbeat and an end-of-session summary. This page covers running it and the Firestore contract with the teacher and admin apps. Paths and delivery guarantees are in `src/sync/README.md`.

## Run

From `camera-ai/`:

```powershell
$env:CAMERA_ROOM_A_01_SOURCE = "rtsp://..."                          # the name set in camera.source_env
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/secrets/edge-room-a.json"   # kept outside the repo
python -m src.main --config config/local_pipeline.json
```

| Option | Meaning |
|---|---|
| `--config` | Local config, see `config/README.md`. Required. |
| `--seats` | Seat grid JSON used when Firestore has no seat grid or cannot be reached at startup. |
| `--model` | YOLOv8-pose weights. Default `models/yolov8n-pose.pt`. |

Exit code 2 means the config is invalid or the camera source variable is unset. Exit code 1 means credentials, model or seat grid are missing. Ctrl+C or SIGTERM closes a running session as `incomplete` and marks the heartbeat offline.

How each config section is used:

| Section | Effect |
|---|---|
| `camera` | Classroom and camera IDs, which name the Firestore paths. The camera source is read from the environment variable named in `source_env`. |
| `sampling` | Capture FPS. Pose inference runs on every n-th frame; the other frames are wiped without processing. |
| `thresholds` | Pose detector settings, side-conversation and back-turn detectors. Back-turn runs only for `frontal` cameras (from the Firestore seat grid). |
| `schedule` | The camera opens only inside these local-time windows, even while a session is active. |
| `privacy` | One-frame buffer, no persistent output. |

## Session control (written by the teacher app)

The edge node listens to `classrooms/{classroom_id}/sessions`. The app creates a session document and sets its `state` field (UC04):

| `state` | Edge node |
|---|---|
| `active` | Starts the session if none is running, and opens the camera (inside the schedule). |
| `paused` | Closes the camera and pauses alerts. |
| back to `active` | Reopens the camera. Behaviour episodes start over. |
| `ended` | Closes the camera and writes the summary as `completed`. |
| document deleted, or any other value | Closes the camera and writes the summary as `incomplete`. |

- Keep at most one `active` or `paused` session per classroom. If there are several, the edge node takes the one with the smallest ID.
- Session IDs must match `[A-Za-z0-9_-]{1,64}`. Firestore auto-IDs do.
- Every camera of the classroom joins the same session, and each writes its own summary.
- The seat grid is fixed when the session starts. A recalibration applies from the next session.

## Heartbeat: `classrooms/{classroom_id}/edge_nodes/{camera_id}`

Written every 10 s and on every status change. Fields: `online`, `status`, `session_id`, `fps` (inferred frames per second), `camera_ok`, `last_frame_at`, `updated_at`.

| `status` | Meaning |
|---|---|
| `idle` | No live session. |
| `monitoring` | Session active, frames arriving. |
| `paused` | Session paused, camera closed. |
| `unavailable` | Session active, but the camera sent no frame for 5 s or could not be opened (retried every 10 s). Show "temporarily unavailable" (UC02). |
| `outside_schedule` | Session active outside the schedule windows. The camera stays closed. |

- Treat the node as offline when `online` is false or `updated_at` is more than 30 s old. Timestamps come from the edge clock in UTC, so keep NTP enabled on edge nodes.
- `camera_ok` is null until the camera has been opened once. The edge node never opens the camera outside a session just to test it, so before a session `camera_ok` reflects the previous one.
- UC04 step 3 (check before starting): the seat grid document exists, and the heartbeat is online and recent.

## End-of-session summary: `classrooms/{classroom_id}/sessions/{session_id}/summaries/{camera_id}`

Fields: `session_id`, `status`, `class_average`, and `seats`, a list of `{seat_id, engagement_score, observed_sec, head_drop_events, slumping_events}`.

| `status` | Meaning |
|---|---|
| `running` | Written when the session starts. |
| `completed` | The teacher ended the session. |
| `incomplete` | The session stopped without the teacher ending it (document deleted, edge node shut down), or the edge node restarted during it and the scores cover only the part after the restart (UC04 alternate flow). |

- A summary still `running` after the session ended means the edge node died without closing it; show it as incomplete.
- `engagement_score` is the cumulative 0–100 score, or null if the seat was never scored. `observed_sec` is how long the seat was seen.
- `class_average` weights each seat's score by `observed_sec`, so someone walking past a seat for a few seconds barely counts. With several cameras in one room, combine their summaries the same way.
- For reports and exports (UC03, UC11), read one document per camera per session and map `seat_id` to students through the seating map.

## Timing

`observed_at_sec` (records) and `start_sec` (alerts) count seconds of monitored time since the session started. A pause or a camera outage advances that clock by at most 5 s, so it is not wall-clock time since the start.

## Known limits

- The Firestore listener dies when the network drops (a reconnect recursion in `google-api-core`). The edge node subscribes again once its Firestore writes succeed. Until then it keeps the last session state it saw, so a session ended during an outage is closed only after reconnection. The schedule still bounds when the camera can be open.
- Opening an unreachable RTSP camera can block the loop for about 30 s (OpenCV timeout), during which the heartbeat is not refreshed.
- Alert push notifications (FCM, UC09) are not built.
