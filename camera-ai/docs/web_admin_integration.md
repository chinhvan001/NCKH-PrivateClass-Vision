# Web Admin Integration

The web admin (Flask backend in `backend/` using the Admin SDK, React frontend in `frontend/`, merged from branch `Web` into `camera-ai` on 2026-10-23) and camera AI always run on the same machine. Since 4 November 2026 they exchange JSON files in `edge-data/` at the repository root instead of Firestore: the web admin gives each camera its sessions and seats, the edge nodes write their output beside them, and the web admin reads it back. They never call each other over HTTP. Firestore keeps only what the web admin and the Flutter app need, and camera AI has no Firebase account at all.

The edge node's writes every 10 s used to go to Firestore and passed the Spark plan's 20,000 writes a day: the heartbeats of four idle cameras alone came to about 35,000 a day (estimate of 1 November 2026). Locally they cost nothing.

This page is the contract, what the web admin does with it, and what is still open. Edge-side details: `docs/edge_node.md` (behaviour) and `src/sync/README.md` (files, write guarantees). The decisions behind the Firestore schema, for the team meeting: `docs/team_notes_firestore_schema.md`.

## IDs

- One class has one room and one camera. Cameras exist only on the web admin's camera page. The name entered there, for example `Camera 201`, is the document ID in `cameras` and `seat_regions` and the file name in `edge-data/cameras/`, `edge-data/camera_sessions/` and `edge-data/edge_nodes/`, so it cannot hold `\ / : * ? " < >` or a vertical bar. Camera AI, which runs once on the same machine, starts one edge node for every file in `edge-data/cameras/` (`docs/edge_node.md`, Run). The camera's class is the `classes2` document whose `camera_id` is that name.
- Session IDs are Firestore auto-IDs. The edge node accepts IDs matching `[A-Za-z0-9_-]{1,64}`.
- Seat IDs are `S01`, `S02`, ... numbered row by row: in a class with C columns, the seat in row r and column c is `S` followed by `(r - 1) * C + c` on at least two digits (`S100` and up for very large classes). The web admin writes these keys in `classes2/{c}.seat_map`, and the edge node derives the same IDs from `row_count`/`column_count` (`src/config/class_layout.py::seat_id`, `backend/services/monitoring_service.py::seat_id`). `backend/tests/test_edge_contract.py` fails if the two drift apart.

## Firestore (web admin and app)

| Path | Written by | Read by | Fields |
|---|---|---|---|
| `sessions/{s}` | web admin (create, status changes; `camera_id` at the first start; `reports_at`, `report_count` from the report job) | web admin, app | `class_id`, `teacher_id`, `subject`, `session_date` (`YYYY-MM-DD`), `session_type`, `period`, `start_time`, `end_time` (timetable, `HH:MM`), `room`, `status`, `camera_id` (the class's camera when the session first started), `started_at`, `ended_at`, `created_at`, `reports_at`, `report_count` |
| `sessions/{s}/monitored_students/{seat}` | web admin, when the session first starts (the diagram's `monitored_student`); the scoring worker adds its summary at the end (package A); report job, for sessions started without it | web admin reports, report job; the session's teacher | `student_id`, `row`, `column` (assigned seats only); then `is_present`, `attention_score`, `is_attention`; `note` from the teacher |
| `classes2/{c}` | web admin (`camera_id` from the camera page) | web admin, app | `class_name`, `school_year`, `teacher_id` (homeroom teacher), `subject`, `camera_id` (the camera that watches the class), `row_count`, `column_count` (1 to 50), `status`, `seat_map` (`S01` → `row`, `column`, `student_id` or null, `status`), `created_at`, `updated_at` |
| `students2/{sid}` | web admin | web admin; the parent whose UID is in `parent_id` | student record, `parent_id` (the parent's Firebase UID) |
| `students2/{sid}/reports/{s}` | report job, once per finished session | that student's parent (UC03), admins | `session_id`, `class_id`, `class_name`, `subject`, `session_date`, `start_time`, `end_time`, `avg_concentration`, `level` (`good`, `stable`, `attention`), `observed_min`, `alerts` (count per type), `partial`, `created_at` |
| `cameras/{camera_id}` | web admin camera page | web admin; staff in the app | `camera_name`, `room_name`, `angle_type`, `ip_address`, `rtsp_port`, `updated_at`, `updated_by`. Never the RTSP URL (a legacy `rtsp_url` is deleted when the camera list is read) and no stored status |
| `seat_regions/{camera_id}` | web admin camera page ("Xác định chỗ ngồi") | web admin, which copies them into the camera's session when a session starts | `class_id`, `image_width`, `image_height` (the snapshot's size), `seats` (`S01` → `[x1, y1, x2, y2]` in pixels of the snapshot), `updated_at`, `updated_by` (admin UID); never the snapshot |

Firestore writes per 45-minute lesson are now the status changes, the frozen roster and one report per student: about 65 for a class of 30, where the edge node alone used to write about 950 for 40 seats.

Older collections the edge node or the web admin wrote before 4 November 2026 (`session_results`, `session_evaluations`, `session_windows`, `shadow_session_*`, `edge_nodes`, `sessions/{s}/alerts`, `camera_configs`) are no longer read or written, except `camera_configs`: a camera saved on the camera page moves its URL from there to `edge-data/` and deletes the document. Delete the rest in the Firebase console once nobody needs that test data.

## Local files (web admin ↔ camera AI)

All under `edge-data/` (git-ignored; `src/sync/README.md` has the write guarantees):

| Path | Written by | Read by | Content |
|---|---|---|---|
| `cameras/{camera_id}.json` | web admin camera page | camera AI | `angle_type`, `source` (RTSP URL with the camera's user and password, percent-encoded). The API never returns `source` |
| `camera_sessions/{camera_id}.json` | web admin: first start, then every status change (including the report job's automatic end) | camera AI, every second | `session_id`, `status`, `class_id`, `row_count`, `column_count`, `seat_regions` (`image_width`, `image_height`, `seats`). Never `seat_map` |
| `edge_nodes/{camera_id}.json` | camera AI, every 10 s and on every status change | web live view, pre-start check, camera page, dashboard (UC04, UC10) | `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` |
| `sessions/{s}/result.json` | camera AI, every 10 s of monitoring | web live view (UC07), data status of reports | `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map` (per seat: `concentration`, `interaction`, `status`) |
| `sessions/{s}/evaluations.json` | camera AI, every 5 min of monitoring and at the end | web reports and dashboard (UC03, UC11), report job | per seat: `session_id`, `seat_id`, `captured_at`, `concentration`, `avg_concentration`, `distraction`, `observed_sec` |
| `sessions/{s}/windows.jsonl` | camera AI, every 10 s of monitoring and at the end | the web backend's scoring worker (package A of `docs/backend_scoring_and_schema_proposal.md`) | one window per line: `session_id`, `camera_id`, `run`, `seq`, `start_sec`, `end_sec`, `captured_at`, `monitoring_status`, `seats` (per seat: `normal_sec`, `slumping_sec`, `head_drop_sec`, `last_seen_sec`, `last_state`, `last_behaviour_sec`, `alerts` per type). Fields: `docs/edge_node.md` |
| `sessions/{s}/alerts.jsonl` | camera AI | web live view and dashboard (UC09), report job | one alert per line: `id`, `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec` |
| `sessions/{s}/handled_alerts.json` | web admin | web admin | per alert `id`: `status` (`acknowledged`, `dismissed`), `handled_by` (UID), `handled_at` |
| `sessions/{s}/shadow_result.json`, `shadow_evaluations.json` | the web backend's scoring worker (`backend/jobs/scoring_worker.py`), until the switch in week 4 of `docs/plan_to_2026-12-13.md` | developers, who compare them with the edge's `result.json` and `evaluations.json` | The same fields. At the switch the worker writes `result.json` and `evaluations.json` instead (`scoring_service.RESULTS`, `EVALUATIONS`) |

Field meanings:

- `concentration`: 0–100 score over the last 60 s; null when the seat is `away`. `avg_concentration`: 0–100 score since the session started.
- `distraction`: alerts of any type for the seat in this session. `interaction`: side-conversation alerts for the seat (provisional, see the team notes).
- Seat `status`: `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s).
- `observed_sec`: how long the seat was seen. The web reports ignore seats seen for less than 60 s (someone walking past) and weight averages by it.
- `monitoring_status`: `running`; `completed` (the session was ended); `incomplete` (cancelled, deleted, replaced, edge node shut down or restarted mid-session: the scores cover part of the lesson). A result still `running` after the session ended means the edge node died.
- `captured_at` and the heartbeat's times are UTC timestamps in ISO 8601. `start_sec` counts seconds of monitored time since the session started.
- Report `partial`: the session's data covers only part of the lesson (`monitoring_status` `incomplete`, or still `running` 30 minutes after the end). A student gets a report only if their seat was seen for at least 60 s; a report never names a seat or another student.

No edge file holds a name, a student ID, an image, keypoints or a bounding box, and the edge node never receives `seat_map`. Mapping a `seat_id` to a student happens on the web side only, through `sessions/{s}/monitored_students`, or through the class's current `seat_map` for sessions started before it existed.

`backend/jobs/migrate_schema.py` brings older Firestore data to this layout. It moves:

- `classrooms` cameras to `cameras`;
- `camera_configs.class_id` to `classes2.camera_id`;
- `session_rosters` and session `monitored_students` maps to the subcollection.

It also normalises session dates and drops stray fields. It prints its plan by default and writes only with `--apply`; legacy collections the app still reads are kept.

## Session status

| `status` | Set by | Edge node |
|---|---|---|
| `scheduled` | creating the session | Ignored. |
| `running` | Start, Resume | Builds the seat plan from the session file, opens the camera inside its schedule windows and starts scoring. |
| `paused` | Pause | Closes the camera until the status is `running` again. |
| `completed` | End, or the report job 30 minutes after the timetable end | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| `cancelled` | Cancel (only before the start) | Never reaches the edge node: the session was never given to a camera. |

- Transitions: `scheduled` → `running` or `cancelled`; `running` → `paused` or `completed`; `paused` → `running` or `completed`. The same list is in `backend/routes/session_routes.py::VALID_TRANSITIONS` and in `config/firestore.rules` for the teacher app. The edge node still accepts the older `live` (as `running`) and `ended` (as `completed`).
- The first start sets `started_at`, the end sets `ended_at`. `start_time` and `end_time` stay the timetable times. The edge node ignores all four; the `schedule` windows of camera AI's settings bound when the camera may open.
- At most one `running` or `paused` session per class. The web admin refuses a second start. A camera holds one session at a time: starting another session for the same camera replaces the old one, which the edge node closes as `incomplete`.
- Only the web backend writes the session files. A status changed in the Firebase console or directly by the app does not reach camera AI.
- A `running` session outside the edge node's schedule windows leaves the camera closed, and the heartbeat says `outside_schedule`. A seat plan the edge node cannot use makes the heartbeat say `unavailable`.

## Web admin side

All endpoints need an admin's Firebase ID token (`Authorization: Bearer`, an `admins/{uid}` document).

| Endpoint | Does |
|---|---|
| `PUT /api/admin/schedules/<s>/status` with `{status, force}` | Changes the status along the transitions above. The first start runs the UC04 step 3 checks and answers `409` with a `code`: `class_busy` (another session of the class is `running` or `paused`), `no_seat_plan` (no valid `row_count`/`column_count`), `no_seat_regions` (the class has a camera whose seats were not drawn for this class on the camera page), `edge_offline` (the heartbeat of the class's camera is missing, says offline, or is more than 30 s old). `force: true` skips only `edge_offline`, never `no_seat_regions`: the edge node picks the session up when it comes back. A successful first start freezes `sessions/{s}/monitored_students`, sets `started_at` and `camera_id` (the class's camera), and gives the session to that camera with its seat plan and drawn seats (`edge-data/camera_sessions/{camera_id}.json`). Every later change updates the status in that file; `completed` also sets `ended_at`. |
| `GET /api/admin/schedules/<s>/monitoring` | The session, the heartbeat of its camera (`online` false when it says so or is more than 30 s old), the edge node's live result and the 20 newest alerts. The live view polls it every 10 s; each poll reads one Firestore document (two before the session's first start). |
| `GET /api/admin/schedules/<s>/seats` | The session's seat grid (`S01`, row, column) with student names, from the frozen roster, plus `reports_at`/`report_count` of the parent reports. Loaded once when the live view opens and again when the status changes. |
| `DELETE /api/admin/schedules/<s>` | Deletes a session that is not `running` or `paused` (`409` otherwise), with its `monitored_students`, a legacy `session_rosters` document, its parent reports and its folder `edge-data/sessions/<s>/` (results, evaluations, windows, alerts). |
| `PUT /api/admin/schedules/<s>/alerts/<id>` with `{status}` | Records `acknowledged` or `dismissed`, with `handled_by` and `handled_at`, in `handled_alerts.json`. |
| `GET /api/v1/evaluations/classes-overview`, `GET /api/v1/evaluations/classes/<c>/details` | Reports from the edge nodes' evaluations, mapped to students through each session's roster and averaged over sessions weighted by `observed_sec`. Seats without a student appear as "Ghế S05 (chưa xếp học sinh)". The class details also list every session with its `data_status`: `complete`, `partial` (interrupted), `pending` (the edge node has not closed it yet), `live` or `no_data`. |
| `GET /api/admin/dashboard-stats` | Running and paused sessions with their newest alerts, the concentration distribution over all evaluations, how many camera AI nodes are online, and the latest starts and ends. |
| `GET`, `PUT /api/admin/seat-regions/<camera_id>` with `{class_id, image_width, image_height, seats}` | Reads or saves the seat rectangles of a camera (`camera_id` is its `camera_name`). Every seat must exist in the class's seat plan and every rectangle lie inside the image (`400` otherwise); empty `seats` deletes the document, and lessons of the class cannot start again until seats are drawn. A running session keeps the seats it started with. |
| `GET /api/admin/cameras` (and `DELETE /<camera_id>`) | The documents of `cameras`, each with its class (`configured`, `class_id`, `class_name` from `classes2.camera_id`, never the URL), its `angle_type`, and its edge node's heartbeat (online when fresh). A heartbeat without a `cameras` document, such as one left by a deleted camera, is not listed. Deleting a camera deletes its `cameras` document, its files in `edge-data/cameras/` and `edge-data/camera_sessions/` and a legacy `camera_configs` document, and clears its class's `camera_id`; camera AI stops its edge node within 30 s. Legacy `rtsp_url` values in `cameras` are deleted when the list is read. |
| `POST /api/admin/cameras` with `{room_name, camera_name, class_id, angle_type, ip_address, rtsp_port, stream_path, username, password}` | Adds a camera, and camera AI starts its edge node within 30 s: `cameras/{camera_name}` gets the display fields and `angle_type` (`frontal`, the default, or `top_down`), `edge-data/cameras/{camera_name}.json` the angle and the RTSP URL, and the class its `camera_id`. `400` for a camera name that cannot be a file name, a missing room, a host that is not an IP address or host name (no `user@`, port or path in it), a port outside 1–65535 or a path with spaces; `404` for an unknown class; `409` when the camera name, the class or the room already has a camera. |
| `PUT /api/admin/cameras/<camera_id>` with `{class_id, angle_type, ip_address, rtsp_port, stream_path, username, password}` | Edits a camera; its room and camera name stay as they are. A missing `angle_type` keeps the stored one; a changed one restarts the camera's edge node, so it is refused with `409` while the class has a `running` or `paused` session. A blank `stream_path` keeps the current path, and a blank `username` and `password` keep the current account; filling in either one replaces both. A changed `ip_address` or `rtsp_port` with a blank account is refused with 400, so the stored password is never sent to another host. The server reads the stored URL only to keep those parts and never returns it; for a camera saved before 4 November 2026 it takes that URL from `camera_configs` once, writes it to `edge-data/` and deletes the document. The edge node uses the URL the next time it opens the camera, and a changed class from the next session that starts. Same `400`/`404` checks as adding; `409` when another camera already watches the class. |
| `GET /api/admin/cameras/<camera_id>/snapshot` | Test snapshot, off unless `CAMERA_SNAPSHOT=1` is set in `backend/.env` (`404` otherwise). It returns one JPEG frame grabbed from the stored URL, with `Cache-Control: no-store`. `409` while the class has a `running` or `paused` session; `502` when the camera gives no frame. The camera list marks each camera that has it with `snapshot: true`. It is an exception to "frames never leave the edge node": checklist §3.14. |

Parent report job: `python -m jobs.parent_reports` from `backend/` (one pass; schedule it every 10 minutes with Task Scheduler or cron, or run it with `--every 600`). It handles sessions ended in the last 7 days once the edge node has closed them (or 30 minutes after the end), and `--session <id>` rebuilds one session. Each pass first ends any session still `running` or `paused` more than 30 minutes after its timetable `end_time` on its `session_date` (Vietnam time), and tells its camera: a teacher who forgot to press End no longer leaves the camera watching the room. Sessions without a `session_date` are left alone. The job runs on the same machine as camera AI, since it reads the edge nodes' files.

Frontend:

- The timetable (`frontend/src/components/admin/session/SessionPanel.jsx`) shows each session's status. Clicking a session opens `SessionMonitorModal.jsx`: start, pause, resume, end, cancel or delete; the camera AI status; the live seat grid with names, scores and states; alerts to acknowledge or dismiss; whether the parent reports exist.
- The dashboard and the "Phân tích & đánh giá" page show the data above, including a table of the class's sessions with the interrupted ones marked; the student pages send the admin token too.
- The camera page (`frontend/src/components/admin/camera/CameraManagementPanel.jsx`) shows each camera's class and its state from its edge node. "Thêm camera" (`AddCameraForm.jsx`) takes the room, the camera name, the class, the camera angle, the brand (which fills in the stream path), IP address, port, the camera's user and password. Right-clicking a camera row opens a menu (Chỉnh sửa thông tin, Xác định chỗ ngồi, Xóa camera). The row's "Sửa" button does the same edit for keyboard users. Editing opens the same form with the room and the camera name locked. The password is never shown again. When the test snapshot is on, the row and the menu also offer "Xem hình" (`CameraSnapshotModal.jsx`), and the seat dialog offers "Lấy ảnh từ camera".
- "Xác định chỗ ngồi" on the camera page (`frontend/src/components/admin/camera/SeatRegionModal.jsx`): the admin picks the class, opens a snapshot of the camera from their computer (shown through an object URL, never uploaded) and drags one rectangle per seat.

Tests: `backend/tests` runs the Flask API on camera-ai's `tests/fake_firestore.py` (no Firebase credentials), with a temporary `edge-data/` for every test. `backend/tests/test_edge_contract.py` also runs the real `EdgeRuntime`, wired by `src/main.py::edge_runtime`, on the same folder: the admin starts, pauses and ends a session through the API, the live view, seat names, class report and parent reports must show what the edge node wrote, and deleting the session must leave none of its data. A second test draws seats through the API on a snapshot four times the stream's resolution, the opposite way round from where people sit, and the edge node must assign each person by the drawn rectangles, even after the seats are redrawn mid-session. A third adds the camera through the API, as an admin would, and runs the edge node exactly as `python -m src.main` does. Starting a lesson must be refused until the seats are drawn, and the edge node must then open the URL built from the form and place each person by the drawn rectangles. CI: `.github/workflows/web-ci.yml` (backend tests, frontend build).

## Still open

1. **Teacher app.** The Flutter app (`main`, also at the root of this branch) still reads `monitoring_sessions`, `classrooms` and `enrollments`. Live results and alerts now stay on the web admin's machine, so the app can show them only through the web API. It must also start and end sessions through the web API: the Rules let a session's teacher change `status`, `started_at` and `ended_at`, but a direct write skips the web admin's pre-start checks and roster freeze, and never reaches camera AI.
2. **Linking parents.** Reports become visible to a parent once `students2/{sid}.parent_id` holds the parent's Firebase UID. Nothing writes it yet: the web student form has no parent account field, and the app links parents on its old `students` collection. The parent screens of the app must read `students2/{sid}/reports`.
3. **Read volume.** Each pass of the report job reads every session that ended in the last 7 days: with 4 classes, 6 lessons a day and a pass every 10 minutes, about 20,000 of the Spark plan's 50,000 reads a day. Look back only to the previous pass (plus the 30-minute wait), as the scoring worker does, before running it all day.
4. **Configuration.** `backend/firebase_config.py` still has a hard-coded default Firebase Web API key: load it from the environment and restrict the key in Google Cloud.
5. **Frontend lint.** The existing frontend code still has eslint errors, so CI only builds it. New code is lint-clean.

## Trying it end to end

1. In the web admin, create a class with 1 to 50 rows and columns, and assign students to seats.
2. Start camera AI once with `python -m src.main` (`docs/edge_node.md`). On the camera page, press "Thêm camera", pick the class and angle, and enter the camera's address and account. Within 30 s its heartbeat `edge-data/edge_nodes/{camera_id}.json` says `idle`, and the camera page shows it online. Draw the seats with "Xác định chỗ ngồi" on the camera page; lessons of the class cannot start before.
3. Add a session for that class in the timetable, open it and press "Bắt đầu giám sát". Within 10 to 20 s the live view shows the camera AI as "Đang giám sát" and the seats fill in.
4. Press "Kết thúc": `monitoring_status` turns `completed`, `evaluations.json` appears in `edge-data/sessions/{session}/`, the heartbeat returns to `idle`, and the class shows up in "Phân tích & đánh giá".
5. Run `python -m jobs.parent_reports` in `backend/`: every student seen for at least a minute gets `students2/{sid}/reports/{session}`, and the live view says how many reports exist.

Without an edge node or Firebase project, `backend/tests/test_edge_contract.py` runs the same scenario on the fake database and a temporary folder. For a demo in the browser, `backend/tests/demo_server.py` runs the backend on that database with the real edge runtime and simulated poses (a 3×4 class where one student keeps the head down, one leaves the seat, two talk and one turns back, starting when the session starts), two earlier sessions (one interrupted), drawn seats for its camera and the report job (`/api/demo/snapshot.png` is a drawn empty classroom to try "Xác định chỗ ngồi" with). Start the frontend with `npm run dev` and open `http://localhost:5173/api/demo-login`; `/api/demo/db/<path>` shows the Firestore documents and `/api/demo/edge/<path>` the exchanged files, which live in a temporary folder deleted when the demo stops.
