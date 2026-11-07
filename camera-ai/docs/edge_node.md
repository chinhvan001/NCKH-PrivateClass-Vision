# Edge Node

Camera AI runs once on the machine that also runs the web admin, and keeps one edge node for each camera added on the web admin's camera page. Each edge node serves one camera, in the room of one class. It waits until the web admin gives its camera a monitoring session, and processes the camera only while that session is running and inside the schedule. It writes live seat states, per-seat evaluations, posture windows, alerts and a heartbeat.

Camera AI and the web admin exchange all of this as JSON files in `edge-data/` on that machine, not through Firestore. Camera AI needs no Firebase account, and its writes every 10 s cost nothing against the Firebase project's daily quota. Only the web backend talks to Firestore.

This page covers running camera AI and its side of the contract with the web admin. File layout and write guarantees are in `src/sync/README.md`. The whole contract, including what the web admin and the app still have to build, is in `docs/web_admin_integration.md`.

## Run

From `camera-ai/`:

```powershell
python -m src.main
```

Start camera AI once, for example when the machine starts, from the same checkout as the web backend: both find `edge-data/` at the repository root. It needs no file per camera: cameras are added on the web admin ([Connect the camera](#connect-the-camera)).

Every 30 s it reads the cameras the web admin saved in `edge-data/cameras/`. It keeps one edge node per camera, each on a thread named after the camera, which appears in every log line. All edge nodes share one pose model.

| Change on the web admin | Camera AI |
|---|---|
| A camera is added | Its edge node starts within 30 s. |
| A camera is deleted | Its edge node stops, and a running session is closed as `incomplete`. |
| A camera's angle changes | Its edge node restarts. The web admin refuses the change while the class has a session. |

An edge node that stops on an error starts again at the next check. At start and then once a day, camera AI also deletes the data of sessions older than `privacy.retention_days`.

| Option | Meaning |
|---|---|
| `--settings FILE` | Settings shared by every camera: sampling, thresholds, schedule and retention. See `config/README.md`. Without it, the values in `config/settings.example.json` apply. |
| `--model` | YOLOv8-pose weights. Default `models/yolov8n-pose.pt`. |
| `--camera NAME` | Run only this camera of the web admin, for example in a test. |
| `--check-camera [SECONDS]` | Only read every camera for 5 s (or `SECONDS`), print each one's resolution and frame rate, then exit. See [Connect the camera](#connect-the-camera). |
| `--video FILE` | Use a video file instead of the cameras' streams. See [Test with a video](#test-with-a-video-instead-of-the-camera). |

Exit codes:

- **2:** the settings file is invalid, or the `--video` file does not exist.
- **1:** the model is missing. With `--check-camera`, it also means the web admin has no camera, or a camera could not be opened or sent no frame.

Ctrl+C or SIGTERM closes running sessions as `incomplete` and marks the heartbeats offline.

### GPU

On a machine with an NVIDIA GPU, install the CUDA build of PyTorch in the venv. Pick a CUDA version the driver supports; the header of `nvidia-smi` shows it.

```powershell
pip install torch==2.14.0+cu130 torchvision==0.29.0+cu130 --index-url https://download.pytorch.org/whl/cu130
```

The edge node then runs pose inference on the GPU without any setting, and logs the device when the model loads: `Da nap YOLOv8-pose tu '...' tren GPU NVIDIA GeForce RTX 3050 Laptop GPU`. To force the CPU, set `CUDA_VISIBLE_DEVICES=-1`.

Measured on 1 November on the RTX 3050 Laptop GPU (4 GB), with the default settings (1280x720 frames, `image_size` 960, two tiles of 960):

- **Speed:** 43 ms a frame, against 184–357 ms on the laptop's CPU.
- **Detections:** the same people and confidences as on the CPU.
- **Memory:** about 170 MB of GPU memory for the one model all cameras share.
- **Capacity:** the GPU keeps up with every frame of a 10 fps camera, so a `--settings` file can set `sampling.inference_every_n_frames` to 1. The cameras take turns on the model: about four cameras at 5 inferences a second, or two at 10.

The edge node stays in FP32. Half precision (FP16) was no faster on this model and missed a person at confidence 0.53.

## Connect the camera

Everything is set on the web admin's camera page. Press "Thêm camera" and fill in:

| Field | Value |
|---|---|
| Phòng học | An existing room, or the name of a new one. |
| Tên camera | Any name that can be a file name: none of `\ / : * ? " < >` or a vertical bar. It becomes the camera's ID and the name of its files in `edge-data/`, and cannot be changed later. |
| Lớp theo dõi | The class whose sessions the camera monitors. A class has at most one camera. |
| Góc đặt camera | "Phía trước lớp" (`frontal`): in front of the class, facing the students. Only this angle can raise back-turn alerts. "Từ trên cao" (`top_down`): looking down from above. |
| Hãng camera, Địa chỉ IP, RTSP Port, Đường dẫn luồng | The camera's address. The brand fills in the stream path from the table below. |
| Tài khoản camera, Mật khẩu camera | The camera's own account. |

Where the web backend stores it:

- **Firestore `cameras/{camera_id}`:** the camera's room, name and angle, for the web admin and the app.
- **`edge-data/cameras/{camera_id}.json`:** the angle, and the account percent-encoded into an RTSP URL. It never goes to Firestore, and the API never returns it. Logs and error messages hide everything between `://` and the last `@`.
- **Firestore `classes2/{class_id}.camera_id`:** the class's camera. When a session of the class starts, the web admin gives it to this camera.

Camera AI starts the camera's edge node within 30 s. Then draw the seats: "Xác định chỗ ngồi" on the camera's row (`config/README.md`, Seat positions). The web admin refuses to start a lesson of the class until they are drawn.

The edge node reads the URL each time it opens the camera, so a changed address or password applies from the next session. A changed class applies from the next session that starts. To change them, right-click the camera on the web admin and choose "Chỉnh sửa thông tin".

Cameras added before 4 November 2026 kept their URL in Firestore (`camera_configs`). Camera AI no longer reads it: open "Chỉnh sửa thông tin" once and save, without retyping the account. The web admin then moves the URL to `edge-data/` and deletes it from Firestore.

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
python -m src.main --check-camera
# Camera 201 (rtsp://***@192.168.1.64:554/Streaming/Channels/101): 1280x720, 10.0 fps trong 5s (capture_fps 10).
```

The check opens every camera on the web admin the way a session does, or only one with `--camera NAME`. It runs without the model, and keeps frames in memory only, wiping each one. It is a manual installation step: the running edge nodes still open their cameras only during a session.

- **Resolution:** an IP camera sends the resolution set in its own settings. Give the stream it reads about 1280x720, in the camera's settings or by choosing the sub stream if that one is at least 720p. The pixel thresholds assume about that size, and 2K or 4K frames make pose inference several times slower.
- A network stream is read at the camera's own frame rate and only the newest frame is kept at `sampling.capture_fps`, so frames do not queue up in the stream buffers and lag behind.
- A network camera that does not answer fails after 10 s, when opening or reading. The heartbeat then reports `unavailable` and the edge node retries every 10 s.

The camera, its class, address, angle and seats come from the web admin. The settings shared by every camera have defaults, and a `--settings` file can change them (`config/README.md`):

| Section | Effect |
|---|---|
| `sampling` | Capture FPS. Pose inference runs on every n-th frame; the other frames are wiped without processing. |
| `thresholds` | Pose detector settings, side-conversation and back-turn detectors. |
| `schedule` | The cameras open only inside these local-time windows, even while a session is running. Default: Monday to Saturday, 06:30 to 18:00. |
| `privacy` | One-frame buffer, no persistent output, `retention_days` for session data in `edge-data/`. |

## Test with a video instead of the camera

`--video` replaces the camera with a video file, to test recognition when the camera is out of reach:

```powershell
python -m src.main --video D:/videos/lesson.mp4 --camera "Camera 201" --check-camera  # opens the file only
python -m src.main --video D:/videos/lesson.mp4 --camera "Camera 201"
```

- **The camera must exist on the web admin.** Its class and seats come from there, and only its stream is replaced. Without `--camera`, every camera plays the video.
- **The rest works as in a real lesson.** The edge node follows the sessions the web admin gives its camera and writes the same files. It reads the video only while a session is running inside `schedule`; to test outside those hours, pass a `--settings` file with a wider `schedule`.
- **The video plays in real time,** like a camera. Frames that pass while the edge node is busy are skipped, so posture durations and alerts keep their real timing. At the end, the video starts again from the beginning. People jump at that point, so use a video longer than the test.
- **The seats must match the video.** Take a snapshot of the video in VLC (Video, Take Snapshot) and draw the seats over it in "Xác định chỗ ngồi" on the web admin.
- Results from a video are stored like those of a real lesson. Use a test session, and delete it on the web admin afterwards; this also deletes its files in `edge-data/`.
- A recording of a real class is personal data. Use one made with consent, keep it outside the repository, and delete it after testing.

To test without Firebase or a camera, run the offline demo: `camera-ai/venv/Scripts/python backend/tests/demo_server.py --video lesson.mp4`, from the repository root.

- YOLO runs on the video instead of the simulated poses.
- The demo's CAM-1 plays the video, so "Lấy ảnh từ camera" in "Xác định chỗ ngồi" returns a frame of it. Draw the seats over that frame before starting the 11B2 lesson.

## Session control (written by the web admin)

When an admin starts a session, the web admin gives it to the class's camera in `edge-data/camera_sessions/{camera_id}.json`, and updates `status` there at every change. The edge node reads the file again every second.

| `status` | Edge node |
|---|---|
| `scheduled` | Ignored. |
| `running` | Starts the session if none is running: builds the seat plan from the file, then opens the camera inside the schedule. |
| `paused` | Closes the camera and pauses alerts. Going back to `running` reopens it, and behaviour episodes start over. |
| `completed` | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| Any other value, or another session given to the camera | Closes the camera and sets `monitoring_status` to `incomplete`. |

The older `live` still counts as `running` and `ended` as `completed`.

- The file holds one session per camera, so a camera never runs two sessions. Session IDs must match `[A-Za-z0-9_-]{1,64}`; Firestore auto-IDs do.
- The seat plan comes with the session and is fixed for the whole session: `row_count`/`column_count` of the class and the rectangles drawn for this class on the camera page (`seat_regions`), copied when the session starts. The class's `seat_map`, which maps seats to students, never reaches the edge node. Seats are numbered `S01`, `S02`, ... row by row, the same keys the web admin writes in `seat_map`. Rectangles are in pixels of a snapshot and scaled to the stream's resolution. A person counts for a seat only inside its rectangle, and seats without one are not tracked. If the plan cannot be used (more than 50 rows or columns, no usable rectangle), the heartbeat reports `unavailable` and the edge node retries every 10 s.

## Live seat states: `sessions/{session_id}/result.json`

Written when the session starts, then every 10 s of monitored time, and once more when it stops. Fields: `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map`. `result_map` holds one entry per seat seen so far:

| Field | Meaning |
|---|---|
| `concentration` | 0–100 score over the last 60 s; null when the seat is `away`. |
| `interaction` | Side-conversation alerts for this seat since the session started. |
| `status` | `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s). |

| `monitoring_status` | Meaning |
|---|---|
| `running` | Written while the session runs. |
| `completed` | The session was set to `completed`. |
| `incomplete` | The session stopped without being ended (cancelled, deleted, replaced, edge node shut down), or the edge node restarted during it and the scores cover only the part after the restart (UC04 alternate flow). A result still `running` after the session ended means the edge node died; treat it as incomplete. |

## Per-seat evaluations: `sessions/{session_id}/evaluations.json`

Written every 5 minutes of monitored time and when the session stops, one entry per seat seen, keyed by seat ID. Fields: `session_id`, `seat_id`, `captured_at`, `concentration` (last 60 s), `avg_concentration` (whole session), `distraction` (alerts of any type for this seat), `observed_sec` (time the seat was seen).

- Use `observed_sec` to drop seats where someone only walked past, and to weight class averages.
- For reports and exports (UC03, UC11), map `seat_id` to students through `sessions/{session_id}/monitored_students` in Firestore, the seating the web admin freezes when the session starts (`docs/web_admin_integration.md`).

## Posture windows: `sessions/{session_id}/windows.jsonl`

One line per window: with every result update (every 10 s of monitored time) and once more when the session stops. The web backend's scoring worker reads them (`docs/backend_scoring_and_schema_proposal.md`, Part 1).

Fields: `session_id`, `camera_id`, `run`, `seq`, `start_sec`, `end_sec` (monitored seconds of this run), `captured_at`, `monitoring_status` (`running`; the last window says `completed` or `incomplete`), `seats`.

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

## Alerts: `sessions/{session_id}/alerts.jsonl`

One line per alert. Fields: `id` (random, set once), `session_id`, `seat_id`, `type` (`head_drop`, `back_turn`, `side_conversation`), `start_sec`, `duration_sec`. When an admin handles an alert, the web admin records `status` (`acknowledged` or `dismissed`), `handled_by` and `handled_at` under its `id` in `handled_alerts.json`; an alert without `status` is new.

## Heartbeat: `edge_nodes/{camera_id}.json`

Written every 10 s and on every status change. Fields: `online`, `status`, `session_id`, `fps` (inferred frames per second), `camera_ok`, `last_frame_at`, `updated_at`.

| `status` | Meaning |
|---|---|
| `idle` | No running session. |
| `monitoring` | Session running, frames arriving. |
| `paused` | Session paused, camera closed. |
| `unavailable` | Session running, but the camera sent no frame for 5 s or could not be opened (retried every 10 s), or the seat plan could not be used. Show "temporarily unavailable" (UC02). |
| `outside_schedule` | Session running outside the schedule windows. The camera stays closed. |

- Treat the node as offline when `online` is false or `updated_at` is more than 30 s old.
- `camera_ok` is null until the camera has been opened once. The edge node never opens the camera outside a session just to test it, so before a session `camera_ok` reflects the previous one.
- UC04 step 3 (check before starting): the class has a seat plan and drawn seats, and its camera's heartbeat is online and recent.

## Timing

`captured_at` and the heartbeat's timestamps are UTC wall-clock times. Results and evaluations are paced by monitored time, so a pause writes nothing. `start_sec` (alerts) counts seconds of monitored time since the session started; a pause or a camera outage advances that clock by at most 5 s, so it is not wall-clock time since the start. Alert times are rounded to 0.1 s.

## Known limits

- Camera AI sees only what the web backend writes. A session started, paused or ended in the Firebase console or directly by the app never reaches it; the app must call the web API.
- Opening a network camera that does not answer blocks the loop for up to 10 s, so the heartbeat can be up to about 20 s old meanwhile (the web admin treats 30 s as offline).
- One camera per class: the web admin refuses a second camera for a class.
- Alert push notifications (FCM, UC09) are not built.
