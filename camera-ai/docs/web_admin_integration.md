# Web Admin Integration

The web admin (Flask backend in `backend/` using the Admin SDK, React frontend in `frontend/`, merged from branch `Web` into `camera-ai` on 2026-10-23), the Flutter app and the camera-ai edge nodes share one Firebase project. They never call each other over HTTP. The web admin writes sessions and seat plans; each edge node listens to the sessions of its class and writes its output beside them; the web admin reads that output back. This page is the contract, what the web admin does with it, and what is still open.

Edge-side details: `docs/edge_node.md` (behaviour) and `src/sync/README.md` (paths, delivery). The decisions behind this contract, for the team meeting: `docs/team_notes_firestore_schema.md`.

## IDs

- One class has one room and one camera. The edge node's local config names the class (`camera.class_id`, the `classes2` document ID) and the camera (`camera.camera_id`, for example `Camera 201`, also the `edge_nodes` document ID).
- Session IDs are Firestore auto-IDs. The edge node accepts IDs matching `[A-Za-z0-9_-]{1,64}`.
- Seat IDs are `S01`, `S02`, ... numbered row by row: in a class with C columns, the seat in row r and column c is `S` followed by `(r - 1) * C + c` on at least two digits (`S100` and up for very large classes). The web admin writes these keys in `classes2/{c}.seat_map`, and the edge node derives the same IDs from `row_count`/`column_count` (`src/config/class_layout.py::seat_id`, `backend/services/monitoring_service.py::seat_id`). `backend/tests/test_edge_contract.py` fails if the two drift apart.

## Firestore contract

| Path | Written by | Read by | Fields |
|---|---|---|---|
| `sessions/{s}` | web admin (create, status changes); teacher app (status changes) | edge: `class_id`, `status` | `class_id`, `teacher_id`, `subject`, `session_date`, `session_type`, `period`, `start_time`, `end_time` (timetable, `HH:MM`), `room`, `status`, `started_at`, `ended_at`, `created_at` |
| `classes2/{c}` | web admin | edge: `row_count`, `column_count` only; web admin | `class_name`, `school_year`, `teacher_id` (homeroom teacher), `subject`, `row_count`, `column_count` (1 to 50), `status`, `seat_map` (`S01` → `row`, `column`, `student_id` or null, `status`), `created_at`, `updated_at` |
| `session_rosters/{s}` | web admin, when the session first starts | web admin reports | `class_id`, `seats` (`S01` → student ID, assigned seats only), `created_at` |
| `session_results/{s}` | edge, every 10 s of monitoring | web live view (UC07) | `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map` (per seat: `concentration`, `interaction`, `status`), `expire_at` |
| `session_evaluations/{s}_{seat}` | edge, every 5 min of monitoring and at the end | web reports and dashboard (UC03, UC11) | `session_id`, `seat_id`, `captured_at`, `concentration`, `avg_concentration`, `distraction`, `observed_sec`, `expire_at` |
| `sessions/{s}/alerts/{id}` | edge creates; web admin or teacher handles | web live view and dashboard (UC09) | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec`, `expire_at`; once handled also `status` (`acknowledged`, `dismissed`), `handled_by` (UID), `handled_at` |
| `edge_nodes/{camera_id}` | edge, every 10 s and on every status change | web live view, pre-start check, dashboard (UC04, UC10) | `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` |
| `students/{sid}/reports/{s}` | report job (to build) | that student's parent (UC03) | to define |

Field meanings:

- `concentration`: 0–100 score over the last 60 s; null when the seat is `away`. `avg_concentration`: 0–100 score since the session started.
- `distraction`: alerts of any type for the seat in this session. `interaction`: side-conversation alerts for the seat (provisional, see the team notes).
- Seat `status`: `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s).
- `observed_sec`: how long the seat was seen. The web reports ignore seats seen for less than 60 s (someone walking past) and weight averages by it.
- `monitoring_status`: `running`; `completed` (the session was ended); `incomplete` (cancelled, deleted, edge node shut down or restarted mid-session: the scores cover part of the lesson). A result still `running` after the session ended means the edge node died.
- `captured_at`, `expire_at` and the heartbeat's times are UTC timestamps from the edge clock (keep NTP on). `start_sec` counts seconds of monitored time since the session started.

No edge document holds a name, a student ID, an image, keypoints or a bounding box, and the edge node never reads `seat_map`. Mapping a `seat_id` to a student happens on the web side only, through `session_rosters/{s}`, or through the class's current `seat_map` for sessions started before rosters existed.

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
| `PUT /api/admin/schedules/<s>/status` with `{status, force}` | Changes the status along the transitions above. The first start runs the UC04 step 3 checks and answers `409` with a `code`: `class_busy` (another session of the class is `running` or `paused`), `no_seat_plan` (no valid `row_count`/`column_count`), `edge_offline` (no heartbeat of the class with `online` true and `updated_at` less than 30 s old). `force: true` skips only `edge_offline`: the edge node picks the session up when it comes back. A successful first start freezes `session_rosters/{s}` and sets `started_at`; `completed` sets `ended_at`. |
| `GET /api/admin/schedules/<s>/monitoring` | The session, the class's latest heartbeat (`online` false when it says so or is more than 30 s old), `session_results/{s}` and the 20 newest alerts. The live view polls it every 10 s. |
| `GET /api/admin/schedules/<s>/seats` | The session's seat grid (`S01`, row, column) with student names, from the frozen roster. Loaded once when the live view opens and again when the status changes. |
| `PUT /api/admin/schedules/<s>/alerts/<id>` with `{status}` | Sets `acknowledged` or `dismissed`, with `handled_by` and `handled_at`. |
| `GET /api/v1/evaluations/classes-overview`, `GET /api/v1/evaluations/classes/<c>/details` | Reports from `session_evaluations`, mapped to students through each session's roster and averaged over sessions weighted by `observed_sec`. Seats without a student appear as "Ghế S05 (chưa xếp học sinh)". |
| `GET /api/admin/dashboard-stats` | Running and paused sessions with their newest alerts, the concentration distribution over all evaluations, how many camera AI nodes are online, and the latest starts and ends. |

Frontend:

- The timetable (`frontend/src/components/admin/session/SessionPanel.jsx`) shows each session's status. Clicking a session opens `SessionMonitorModal.jsx`: start, pause, resume, end or cancel; the camera AI status; the live seat grid with names, scores and states; alerts to acknowledge or dismiss.
- The dashboard and the "Phân tích & đánh giá" page show the data above; the student pages now send the admin token too.

Tests: `backend/tests` runs the Flask API on camera-ai's `tests/fake_firestore.py` (no Firebase credentials). `backend/tests/test_edge_contract.py` also runs the real `EdgeRuntime` and `FirestoreSink` on the same fake database: the admin starts, pauses and ends a session through the API, and the live view, seat names and reports must show what the edge node wrote. CI: `.github/workflows/web-ci.yml` (backend tests, frontend build).

## Still open

1. **Teacher app.** The Flutter app (`main`, also at the root of this branch) still reads `monitoring_sessions`, `classrooms` and `enrollments`. It needs to read `sessions`, `session_results` and alerts, and to start and end sessions. The Rules let a session's teacher change `status`, `started_at` and `ended_at` along the same transitions, but a direct write skips the web admin's pre-start checks and roster freeze: have the app call the web API, or repeat both in the app.
2. **Parent reports.** A backend job writes `students/{sid}/reports/{s}` from each finished session's evaluations and roster. Define the report fields first. Done when a parent sees their child's report and no other child's.
3. **Camera page.** `classrooms` still stores `rtsp_url` with camera passwords and the camera page tests them with ffprobe at a hard-coded path (compliance checklist §3.12). The edge node never uses them: it takes its camera source from its own environment. Show `edge_nodes` on that page instead and remove `rtsp_url` from Firestore.
4. **Session deletion.** There is no delete endpoint. One that is added must also delete the session's `session_results`, `session_evaluations`, alerts and `session_rosters` documents, unless TTL covers them (checklist §3.6).
5. **Partial sessions.** Reports do not mark sessions whose `monitoring_status` is `incomplete` yet.
6. **Read volume.** The evaluation overview and the dashboard read every `session_evaluations` document on each load. Filter on `captured_at` once the data grows.
7. **Configuration.** `backend/firebase_config.py` still has a hard-coded default Firebase Web API key: load it from the environment and restrict the key in Google Cloud.
8. **Frontend lint.** The existing frontend code has 42 eslint errors, so CI only builds it. New code is lint-clean.

## Trying it end to end

1. In the web admin, create a class with 1 to 50 rows and columns, and assign students to seats.
2. Set the edge node's `camera.class_id` to the class document ID, its `camera.camera_id` and corner seats, and run it as in `docs/edge_node.md`. Its heartbeat `edge_nodes/{camera_id}` appears as `idle`.
3. Add a session for that class in the timetable, open it and press "Bắt đầu giám sát". Within 10 to 20 s the live view shows the camera AI as "Đang giám sát" and the seats fill in.
4. Press "Kết thúc": `monitoring_status` turns `completed`, one `session_evaluations` document per seat appears, the heartbeat returns to `idle`, and the class shows up in "Phân tích & đánh giá".

Without an edge node or Firebase project, `backend/tests/test_edge_contract.py` runs the same scenario on the fake database.
