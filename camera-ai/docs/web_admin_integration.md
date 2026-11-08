# Web Admin Integration

The web admin (Flask backend in `backend/` using the Admin SDK, React frontend in `frontend/`, merged from branch `Web` into `camera-ai` on 2026-10-23), the Flutter app and the camera-ai edge nodes share one Firebase project. They never call each other over HTTP. The web admin writes sessions and seat plans; each edge node listens to the sessions of its class and writes its output beside them; the web admin reads that output back. This page is the contract, what the web admin does with it, and what is still open.

Edge-side details: `docs/edge_node.md` (behaviour) and `src/sync/README.md` (paths, delivery). The decisions behind this contract, for the team meeting: `docs/team_notes_firestore_schema.md`.

## IDs

- One class has one room and one camera. The edge node's local config names the camera (`camera.camera_id`, for example `Camera 201`). That name is also the document ID of `cameras`, `edge_nodes`, `camera_configs` and `seat_regions`. The camera's class is the `classes2` document whose `camera_id` is that name, set on the web admin's camera page, and the camera's RTSP URL comes from the same page. The local config's `camera.class_id` and `camera.source_env` override both.
- Session IDs are Firestore auto-IDs. The edge node accepts IDs matching `[A-Za-z0-9_-]{1,64}`.
- Seat IDs are `S01`, `S02`, ... numbered row by row: in a class with C columns, the seat in row r and column c is `S` followed by `(r - 1) * C + c` on at least two digits (`S100` and up for very large classes). The web admin writes these keys in `classes2/{c}.seat_map`, and the edge node derives the same IDs from `row_count`/`column_count` (`src/config/class_layout.py::seat_id`, `backend/services/monitoring_service.py::seat_id`). `backend/tests/test_edge_contract.py` fails if the two drift apart.

## Firestore contract

| Path | Written by | Read by | Fields |
|---|---|---|---|
| `sessions/{s}` | web admin (create, status changes; `camera_id` at the first start; `reports_at`, `report_count` from the report job); teacher app (status changes) | edge: `class_id`, `status` | `class_id`, `teacher_id`, `subject`, `session_date` (`YYYY-MM-DD`), `session_type`, `period`, `start_time`, `end_time` (timetable, `HH:MM`), `room`, `status`, `camera_id` (the class's camera when the session first started), `started_at`, `ended_at`, `created_at`, `reports_at`, `report_count` |
| `sessions/{s}/monitored_students/{seat}` | web admin, when the session first starts (the diagram's `monitored_student`); the scoring worker adds its summary at the end (package A); report job, for sessions started without it | web admin reports, report job; the session's teacher | `student_id`, `row`, `column` (assigned seats only); then `is_present`, `attention_score`, `is_attention`; `note` from the teacher. A subcollection, so the edge node, which listens to session documents, never receives it |
| `classes2/{c}` | web admin (`camera_id` from the camera page) | edge: a query on `camera_id` for its class, then `row_count`, `column_count` only; web admin | `class_name`, `school_year`, `teacher_id` (homeroom teacher), `subject`, `camera_id` (the camera that watches the class), `row_count`, `column_count` (1 to 50), `status`, `seat_map` (`S01` → `row`, `column`, `student_id` or null, `status`), `created_at`, `updated_at` |
| `session_results/{s}` | edge, every 10 s of monitoring | web live view (UC07) | `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map` (per seat: `concentration`, `interaction`, `status`), `expire_at` |
| `session_evaluations/{s}_{seat}` | edge, every 5 min of monitoring and at the end | web reports and dashboard (UC03, UC11) | `session_id`, `seat_id`, `captured_at`, `concentration`, `avg_concentration`, `distraction`, `observed_sec`, `expire_at` |
| `session_windows/{s}_{run}_{seq}` | edge, every 10 s of monitoring and at the end | the web backend's scoring worker (package A of `docs/backend_scoring_and_schema_proposal.md`); no client | `session_id`, `camera_id`, `run`, `seq`, `start_sec`, `end_sec`, `captured_at`, `monitoring_status`, `seats` (per seat: `normal_sec`, `slumping_sec`, `head_drop_sec`, `last_seen_sec`, `last_state`, `last_behaviour_sec`, `alerts` per type), `expire_at`. Fields: `docs/edge_node.md`. Deleted with the session |
| `sessions/{s}/alerts/{id}` | edge creates; web admin or teacher handles | web live view and dashboard (UC09) | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec`, `expire_at`; once handled also `status` (`acknowledged`, `dismissed`), `handled_by` (UID), `handled_at` |
| `edge_nodes/{camera_id}` | edge, every 10 s and on every status change | web live view, pre-start check, dashboard (UC04, UC10) | `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` |
| `students2/{sid}` | web admin | web admin; the parent whose UID is in `parent_id` | student record, `parent_id` (the parent's Firebase UID) |
| `students2/{sid}/reports/{s}` | report job, once per finished session | that student's parent (UC03), admins | `session_id`, `class_id`, `class_name`, `subject`, `session_date`, `start_time`, `end_time`, `avg_concentration`, `level` (`good`, `stable`, `attention`), `observed_min`, `alerts` (count per type), `partial`, `created_at` |
| `cameras/{camera_id}` | web admin camera page | web admin; staff in the app | `camera_name`, `room_name`, `ip_address`, `rtsp_port`, `updated_at`, `updated_by`. Never the RTSP URL (a legacy `rtsp_url` is deleted when the camera list is read) and no stored status: the live status is `edge_nodes/{camera_id}` |
| `camera_configs/{camera_id}` | web admin camera page ("Thêm camera") | edge: `source`, when it opens the camera | `source` (RTSP URL, camera user and password percent-encoded), `updated_at`, `updated_by` (admin UID). Rules deny every client, admins included; the API never returns `source` |
| `seat_regions/{camera_id}` | web admin camera page ("Xác định chỗ ngồi") | edge, when a session starts: every field but `updated_at`, `updated_by` | `class_id`, `image_width`, `image_height` (the snapshot's size), `seats` (`S01` → `[x1, y1, x2, y2]` in pixels of the snapshot), `updated_at`, `updated_by` (admin UID); never the snapshot |

Field meanings:

- `concentration`: 0–100 score over the last 60 s; null when the seat is `away`. `avg_concentration`: 0–100 score since the session started.
- `distraction`: alerts of any type for the seat in this session. `interaction`: side-conversation alerts for the seat (provisional, see the team notes).
- Seat `status`: `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s).
- `observed_sec`: how long the seat was seen. The web reports ignore seats seen for less than 60 s (someone walking past) and weight averages by it.
- `monitoring_status`: `running`; `completed` (the session was ended); `incomplete` (cancelled, deleted, edge node shut down or restarted mid-session: the scores cover part of the lesson). A result still `running` after the session ended means the edge node died.
- `captured_at`, `expire_at` and the heartbeat's times are UTC timestamps from the edge clock (keep NTP on). `start_sec` counts seconds of monitored time since the session started.
- Report `partial`: the session's data covers only part of the lesson (`monitoring_status` `incomplete`, or still `running` 30 minutes after the end). A student gets a report only if their seat was seen for at least 60 s; a report never names a seat or another student.

No edge document holds a name, a student ID, an image, keypoints or a bounding box, and the edge node never reads `seat_map`. Mapping a `seat_id` to a student happens on the web side only, through `sessions/{s}/monitored_students`, or through the class's current `seat_map` for sessions started before it existed. The edge node finds its class with a query on `classes2.camera_id` that asks for that one field.

`backend/jobs/migrate_schema.py` brings older data to this layout. It moves:

- `classrooms` cameras to `cameras`;
- `camera_configs.class_id` to `classes2.camera_id`;
- `session_rosters` and session `monitored_students` maps to the subcollection.

It also normalises session dates and drops stray fields. It prints its plan by default and writes only with `--apply`; legacy collections the app still reads are kept.

## Session status

| `status` | Set by | Edge node |
|---|---|---|
| `scheduled` | creating the session | Ignored. |
| `running` | Start, Resume | Loads the class seat plan, opens the camera inside its schedule windows and starts scoring. |
| `paused` | Pause | Closes the camera until the status is `running` again. |
| `completed` | End | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| `cancelled`, or the document is deleted | Cancel (only before the start) | Closes the camera and sets `monitoring_status` to `incomplete`. |

- Transitions: `scheduled` → `running` or `cancelled`; `running` → `paused` or `completed`; `paused` → `running` or `completed`. The same list is in `backend/routes/session_routes.py::VALID_TRANSITIONS` and in `config/firestore.rules` for the teacher app. The edge node still accepts the older `live` (as `running`) and `ended` (as `completed`).
- The first start sets `started_at`, the end sets `ended_at`. `start_time` and `end_time` stay the timetable times. The edge node ignores all four; the `schedule` windows in its local config bound when the camera may open.
- At most one `running` or `paused` session per class. The web admin refuses a second start; if the app creates one anyway, the edge node takes the session with the smallest ID.
- A `running` session outside the edge node's schedule windows leaves the camera closed, and the heartbeat says `outside_schedule`. A class whose seat plan cannot be loaded makes the heartbeat say `unavailable`.

## Web admin side

All endpoints need an admin's Firebase ID token (`Authorization: Bearer`, an `admins/{uid}` document).

| Endpoint | Does |
|---|---|
| `PUT /api/admin/schedules/<s>/status` with `{status, force}` | Changes the status along the transitions above. The first start runs the UC04 step 3 checks and answers `409` with a `code`: `class_busy` (another session of the class is `running` or `paused`), `no_seat_plan` (no valid `row_count`/`column_count`), `edge_offline` (no heartbeat of the class with `online` true and `updated_at` less than 30 s old). `force: true` skips only `edge_offline`: the edge node picks the session up when it comes back. A successful first start freezes `sessions/{s}/monitored_students` and sets `started_at` and `camera_id` (the class's camera); `completed` sets `ended_at`. |
| `GET /api/admin/schedules/<s>/monitoring` | The session, the class's latest heartbeat (`online` false when it says so or is more than 30 s old), `session_results/{s}` and the 20 newest alerts. The live view polls it every 10 s. |
| `GET /api/admin/schedules/<s>/seats` | The session's seat grid (`S01`, row, column) with student names, from the frozen roster, plus `reports_at`/`report_count` of the parent reports. Loaded once when the live view opens and again when the status changes. |
| `DELETE /api/admin/schedules/<s>` | Deletes a session that is not `running` or `paused` (`409` otherwise), with its alerts, `monitored_students`, `session_results`, `session_evaluations`, `session_windows`, a legacy `session_rosters` document and parent reports. |
| `PUT /api/admin/schedules/<s>/alerts/<id>` with `{status}` | Sets `acknowledged` or `dismissed`, with `handled_by` and `handled_at`. |
| `GET /api/v1/evaluations/classes-overview`, `GET /api/v1/evaluations/classes/<c>/details` | Reports from `session_evaluations`, mapped to students through each session's roster and averaged over sessions weighted by `observed_sec`. Seats without a student appear as "Ghế S05 (chưa xếp học sinh)". The class details also list every session with its `data_status`: `complete`, `partial` (interrupted), `pending` (the edge node has not closed it yet), `live` or `no_data`. |
| `GET /api/admin/dashboard-stats` | Running and paused sessions with their newest alerts, the concentration distribution over all evaluations, how many camera AI nodes are online, and the latest starts and ends. |
| `GET`, `PUT /api/admin/seat-regions/<camera_id>` with `{class_id, image_width, image_height, seats}` | Reads or saves the seat rectangles of a camera (`camera_id` is its `camera_name`). Every seat must exist in the class's seat plan and every rectangle lie inside the image (`400` otherwise); empty `seats` deletes the document, so the edge node goes back to its corner seats. A running session keeps the seats it started with. |
| `GET /api/admin/cameras` (and `DELETE /<camera_id>`) | The documents of `cameras` (`declared` true), each with its class (`configured`, `class_id`, `class_name` from `classes2.camera_id`, never the URL) and its edge node's heartbeat (online when fresh), plus edge nodes not added on the web (`declared` false). Deleting a camera deletes its `cameras` and `camera_configs` documents and clears its class's `camera_id`, so its edge node goes back to `unconfigured`. Legacy `rtsp_url` values in `cameras` are deleted when the list is read. |
| `POST /api/admin/cameras` with `{room_name, camera_name, class_id, ip_address, rtsp_port, stream_path, username, password}` | Adds a camera: `cameras/{camera_name}` gets the display fields, `camera_configs/{camera_name}` the RTSP URL, and the class its `camera_id`. `400` for a missing room, a host that is not an IP address or host name (no `user@`, port or path in it), a port outside 1–65535 or a path with spaces; `404` for an unknown class; `409` when the camera name, the class or the room already has a camera. |
| `PUT /api/admin/cameras/<camera_id>` with `{class_id, ip_address, rtsp_port, stream_path, username, password}` | Edits a camera; its room and camera name stay as they are. A blank `stream_path` keeps the current path, and a blank `username` and `password` keep the current account; filling in either one replaces both. A changed `ip_address` or `rtsp_port` with a blank account is refused with 400, so the stored password is never sent to another host. The server reads the stored URL only to keep those parts and never returns it. The edge node picks up the class between sessions and the URL the next time it opens the camera. Same `400`/`404` checks as adding; `409` when another camera already watches the class. |
| `GET /api/admin/cameras/<camera_id>/snapshot` | Test snapshot, off unless `CAMERA_SNAPSHOT=1` is set in `backend/.env` (`404` otherwise). It returns one JPEG frame grabbed from the stored URL, with `Cache-Control: no-store`. `409` while the class has a `running` or `paused` session; `502` when the camera gives no frame. The camera list marks each camera that has it with `snapshot: true`. It is an exception to "frames never leave the edge node": checklist §3.14. |

Parent report job: `python -m jobs.parent_reports` from `backend/` (one pass; schedule it every 10 minutes with Task Scheduler or cron, or run it with `--every 600`). It handles sessions ended in the last 7 days once the edge node has closed them (or 30 minutes after the end), and `--session <id>` rebuilds one session. Each pass first ends any session still `running` or `paused` more than 30 minutes after its timetable `end_time` on its `session_date` (Vietnam time): a teacher who forgot to press End no longer leaves the camera watching the room. Sessions without a `session_date` are left alone.

Frontend:

- The timetable (`frontend/src/components/admin/session/SessionPanel.jsx`) shows each session's status. Clicking a session opens `SessionMonitorModal.jsx`: start, pause, resume, end, cancel or delete; the camera AI status; the live seat grid with names, scores and states; alerts to acknowledge or dismiss; whether the parent reports exist.
- The dashboard and the "Phân tích & đánh giá" page show the data above, including a table of the class's sessions with the interrupted ones marked; the student pages send the admin token too.
- The camera page (`frontend/src/components/admin/camera/CameraManagementPanel.jsx`) shows each camera's class and its state from its edge node; an edge node not added yet shows as "Chờ thêm camera trên web" with a "Thêm" button. "Thêm camera" (`AddCameraForm.jsx`) takes the room, the camera name, the class, the brand (which fills in the stream path), IP address, port, the camera's user and password. Right-clicking a camera row opens a menu (Chỉnh sửa thông tin, Xác định chỗ ngồi, Xóa camera). The row's "Sửa" button does the same edit for keyboard users. Editing opens the same form with the room and the camera name locked. The password is never shown again. When the test snapshot is on, the row and the menu also offer "Xem hình" (`CameraSnapshotModal.jsx`), and the seat dialog offers "Lấy ảnh từ camera".
- "Xác định chỗ ngồi" on the camera page (`frontend/src/components/admin/camera/SeatRegionModal.jsx`): the admin picks the class, opens a snapshot of the camera from their computer (shown through an object URL, never uploaded) and drags one rectangle per seat.

Tests: `backend/tests` runs the Flask API on camera-ai's `tests/fake_firestore.py` (no Firebase credentials). `backend/tests/test_edge_contract.py` also runs the real `EdgeRuntime` and `FirestoreSink` on the same fake database: the admin starts, pauses and ends a session through the API, the live view, seat names, class report and parent reports must show what the edge node wrote, and deleting the session must leave none of its documents. A second test draws seats through the API on a snapshot four times the stream's resolution, the opposite way round from the corner seats, and the edge node must assign each person by the drawn rectangles. A third adds the camera through the API for an edge node whose config leaves the class and the source to the web admin: the edge node must report `unconfigured`, then follow that class and open the URL built from the form. CI: `.github/workflows/web-ci.yml` (backend tests, frontend build).

## Still open

1. **Teacher app.** The Flutter app (`main`, also at the root of this branch) still reads `monitoring_sessions`, `classrooms` and `enrollments`. It needs to read `sessions`, `session_results` and alerts, and to start and end sessions. The Rules let a session's teacher change `status`, `started_at` and `ended_at` along the same transitions, but a direct write skips the web admin's pre-start checks and roster freeze: have the app call the web API, or repeat both in the app.
2. **Linking parents.** Reports become visible to a parent once `students2/{sid}.parent_id` holds the parent's Firebase UID. Nothing writes it yet: the web student form has no parent account field, and the app links parents on its old `students` collection. The parent screens of the app must read `students2/{sid}/reports`.
3. **Deleting a session while its edge node is offline.** An edge node that missed the end can still write its last result after it reconnects. Those documents carry `expire_at`, so they go once the TTL policy is enabled (checklist §3.6).
4. **Read volume.** The evaluation overview and the dashboard read every `session_evaluations` document on each load. Filter on `captured_at` once the data grows.
5. **Configuration.** `backend/firebase_config.py` still has a hard-coded default Firebase Web API key: load it from the environment and restrict the key in Google Cloud.
6. **Frontend lint.** The existing frontend code still has eslint errors, so CI only builds it. New code is lint-clean.

## Trying it end to end

1. In the web admin, create a class with 1 to 50 rows and columns, and assign students to seats.
2. Copy `config/local_pipeline.example.json`, set `camera.camera_id` and run the edge node as in `docs/edge_node.md`. It appears on the camera page as "Chờ thêm camera trên web": press "Thêm", pick the class and enter the camera's address and account. Within 15 s its heartbeat `edge_nodes/{camera_id}` turns `idle` with that class. Draw the seats with "Xác định chỗ ngồi" on the camera page, or give the edge node its corner seats.
3. Add a session for that class in the timetable, open it and press "Bắt đầu giám sát". Within 10 to 20 s the live view shows the camera AI as "Đang giám sát" and the seats fill in.
4. Press "Kết thúc": `monitoring_status` turns `completed`, one `session_evaluations` document per seat appears, the heartbeat returns to `idle`, and the class shows up in "Phân tích & đánh giá".
5. Run `python -m jobs.parent_reports` in `backend/`: every student seen for at least a minute gets `students2/{sid}/reports/{session}`, and the live view says how many reports exist.

Without an edge node or Firebase project, `backend/tests/test_edge_contract.py` runs the same scenario on the fake database. For a demo in the browser, `backend/tests/demo_server.py` runs the backend on that database with the real edge runtime and simulated poses (a 3×4 class where one student keeps the head down, one leaves the seat, two talk and one turns back, starting when the session starts), two earlier sessions (one interrupted), drawn seats for its camera and the report job (`/api/demo/snapshot.png` is a drawn empty classroom to try "Xác định chỗ ngồi" with); start the frontend with `npm run dev` and open `http://localhost:5173/api/demo-login`.
