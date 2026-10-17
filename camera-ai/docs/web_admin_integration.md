# Web Admin Integration

The web admin (branch `Web`: Flask backend in `backend/`, React frontend in `frontend/`, hosted on the school server), the Flutter app and the camera-ai edge nodes share one Firebase project. They never call each other over HTTP: the web admin and the app write sessions and seat plans, each edge node listens to the sessions of its class and writes its output beside them. This page is the contract on the team's Firestore schema, the state of the `Web` branch, and the work still open on the web and app side.

Edge-side details: `docs/edge_node.md` (behaviour) and `src/sync/README.md` (paths, delivery). The decisions behind this contract, for the team meeting: `docs/team_notes_firestore_schema.md`.

## IDs

- One class has one room and one camera. The edge node's local config names the class (`camera.class_id`, the `classes` document ID) and the camera (`camera.camera_id`, for example `Camera 201`, which is also the `edge_nodes` document ID).
- Session IDs are Firestore auto-IDs; the edge node accepts IDs matching `[A-Za-z0-9_-]{1,64}`.
- Seat IDs are the document IDs in `classes/{class_id}/seats` (for example `S01-<class_id>`). While a class has no seat documents, the edge node numbers seats `S1`..`Sn` row by row, the way the `Web` branch's `seat_assignments` does today.

## Firestore contract

| Path | Written by | Read by | Fields |
|---|---|---|---|
| `sessions/{s}` | web admin, app | edge: `class_id`, `status` | `class_id`, `teacher_id`, `subject`, `started_at`, `ended_at`, `status` |
| `classes/{c}` | web admin | edge: `row_count`, `column_count` | `class_name`, `school_year`, `teacher_id` (homeroom teacher), `row_count`, `column_count`, `created_at` |
| `classes/{c}/seats/{seat_id}` | app (homeroom teacher), web admin | edge: `row`, `column`; teachers; report job | `row`, `column` (from 1), `student_id` (or null), `status` (`empty`, `assigned`) |
| `session_results/{s}` | edge, overwritten every 10 s of monitoring | teacher dashboard (UC07) | `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map` (per seat: `concentration`, `interaction`, `status`), `expire_at` |
| `session_evaluations/{s}_{seat}` | edge, every 5 min and at session end | teacher and admin reports (UC03, UC11), report job | `session_id`, `seat_id`, `captured_at`, `concentration`, `avg_concentration`, `distraction`, `observed_sec`, `expire_at` |
| `sessions/{s}/alerts/{id}` | edge creates; teacher sets `status` | teacher (UC09) | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec`, `expire_at`; `status` (`acknowledged`, `dismissed`) once handled |
| `edge_nodes/{camera_id}` | edge, every 10 s | web admin, app (UC04, UC10) | `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` |
| `students/{sid}/reports/{s}` | report job (to build) | that student's parent (UC03) | to define |

Field meanings:

- `concentration`: 0–100 score over the last 60 s; null when the seat is `away`. `avg_concentration`: 0–100 score since the session started.
- `distraction`: alerts of any type for the seat in this session. `interaction`: side-conversation alerts for the seat (provisional, see the team notes).
- Seat `status`: `focused`; `drowsy` (head down with still hands); `distracted` (unclear head-down posture, or a back turn or side conversation in the last 5 s); `away` (nobody seen for 30 s).
- `observed_sec`: how long the seat was seen. Drop seats where someone only walked past, and weight class averages by it.
- `monitoring_status`: `running`; `completed` (the session was ended); `incomplete` (cancelled, deleted, edge node shut down or restarted mid-session: the scores cover part of the lesson). A result still `running` after the session ended means the edge node died.
- `captured_at`, `expire_at` and the heartbeat's times are UTC timestamps from the edge clock. `start_sec` counts seconds of monitored time since the session started.

No edge document holds a name, a student ID, an image, keypoints or a bounding box. Mapping a `seat_id` to a student goes through `classes/{c}/seats`, on the web and app side only.

## Session status

| `status` | Edge node |
|---|---|
| `scheduled` | Ignored. |
| `running` | Loads the class seat plan, opens the camera inside its schedule windows and starts scoring. |
| `paused` | Closes the camera until the status is `running` again. |
| `ended` | Closes the camera, writes the final evaluations and sets `monitoring_status` to `completed`. |
| `cancelled`, or the document is deleted | Closes the camera and sets `monitoring_status` to `incomplete`. |

- Until the `Web` branch switches, the edge node also accepts `live` (as `running`) and `completed` (as `ended`).
- Keep at most one `running` session per class. If there are several, the edge node takes the one with the smallest ID.
- The edge node ignores `started_at` and `ended_at`. Someone has to set `running` and `ended`; nothing starts a session automatically.
- A `running` session outside the edge node's schedule windows leaves the camera closed, and the heartbeat says `outside_schedule`. A class whose seat plan cannot be loaded makes the heartbeat say `unavailable`.

## State of the `Web` branch

Reviewed on 2026-10-17. The branch has six commits, the last on 2026-09-20 ("Update new database"), and has not been updated for the schema yet.

| Area | Built | Differs from the schema |
|---|---|---|
| Login | Google and email/password through Firebase Auth; admin rights from `admins/{uid}` | Nothing. |
| Teacher accounts | Create, edit and delete teachers (`teachers/{uid}`) | Nothing. |
| Classes and seats | Class CRUD and a seat editor (`GET`/`PUT /api/admin/classes/<id>/seats`) | `row_number`/`column_number` instead of `row_count`/`column_count`; seat assignments are a `seat_assignments` map (`S1` → student ID) on the class document, not seat documents; classes link to a `classroom_id`. |
| Classrooms and cameras | `classrooms` CRUD with camera fields, connection test with ffprobe | The schema has no `classrooms`. `rtsp_url`, passwords included, is stored in Firestore and returned by the API (compliance checklist §3.12). The ffprobe path is hard-coded to `D:\Tools\ffmpeg`. |
| Sessions | REST create, update, delete; statuses `scheduled`, `live`, `completed`, `cancelled` | Uses `teacher_uid`, `classroom_id`, `date`/`start`/`end` strings, `live`/`completed` and `focus`. The session management page still shows hard-coded sessions. |
| Dashboard, session detail, evaluations | Screens only | Hard-coded sample data; nothing reads edge output yet. |
| Configuration | | The Firebase Web API key is hard-coded in `backend/firebase_config.py`. |

The Flutter app (on `main`) reads `monitoring_sessions`, `classrooms` and `enrollments`, and stores seat rows and columns on student documents; it needs the same migration.

## Tasks for the web and app teams

Each task names where to work and when it counts as done.

1. **Sessions on the schema.** Write `teacher_id`, `started_at`/`ended_at` timestamps and `status` `running`/`ended` (`paused` if teachers pause), and stop writing `classroom_id`, `date`, `start`, `end` and `focus`. Wire start and end buttons in `frontend/src/components/admin/SessionManagementPanel.jsx` to the API instead of the hard-coded list, and refuse `running` while another session of the class runs. The app reads `sessions` instead of `monitoring_sessions`. Done when setting `running` turns the heartbeat to `monitoring` and setting `ended` turns `monitoring_status` to `completed`.
2. **Seat plans as documents.** Write `classes/{c}/seats/{seat_id}` (`row`, `column`, `student_id`, `status`) from the web seat editor and the app's seating screen, instead of `seat_assignments` on the class or `row`/`column` on student documents; rename `row_number`/`column_number` to `row_count`/`column_count`. Done when a session's `result_map` uses the new seat IDs.
3. **Check before starting (UC04 step 3).** Before allowing `running`, check that the class has seat documents and that `edge_nodes/{camera_id}` is online with `updated_at` less than 30 s old. Done when starting a session without a seat plan or with an offline edge node shows an error.
4. **Live view and alerts (UC07, UC09).** Listen to `session_results/{s}` and `sessions/{s}/alerts` of running sessions; map seat IDs to students through the seat documents; acknowledging or dismissing writes the alert's `status`. Replace the sample data in `DashboardPanel.jsx`. Done when the dashboard shows no sample data.
5. **Reports and exports (UC03, UC11).** Query `session_evaluations` filtered on `session_id`, weight class averages by `observed_sec`, and mark sessions whose `monitoring_status` is `incomplete` (or still `running` after the end) as partial. Done when the evaluation pages show edge data.
6. **Parent reports.** A backend job (Flask scheduled task or Cloud Function) joins each finished session's evaluations with its seat documents and writes `students/{sid}/reports/{s}`, which parents read. Define the report fields first. Done when a parent sees their child's report and no other child's.
7. **Camera health (UC10).** Show `edge_nodes/{camera_id}`: offline when `online` is false or `updated_at` is more than 30 s old, otherwise `status` (`unavailable` means "temporarily unavailable"). Keep the ffprobe check only as a setup test, with its path in configuration. Done when the camera page reflects a stopped edge node.
8. **Remove the old collections.** Delete `classrooms` (and with it the stored `rtsp_url` passwords: the camera source lives only on the edge node), `enrollments` and `monitoring_sessions`, with a one-off script that migrates existing documents (`teacher_uid` → `teacher_id`, `live` → `running`, `completed` → `ended`). Load the Firebase Web API key from the environment and restrict it in Google Cloud. Done when no code reads the old collections.
9. **Session deletion.** Deleting a session also deletes its `session_results`, `session_evaluations` and `alerts` documents, unless the retention period is enforced by TTL instead (compliance checklist §3.6).

## Open questions

The team still has to confirm the points listed in `docs/team_notes_firestore_schema.md` §2 (alert and heartbeat paths, status values, metric meanings, seat documents, who may read seats, one camera per class).

## Trying it end to end

1. Create a class with `row_count`/`column_count` and seat documents (or only the counts: the edge node then uses `S1`..`Sn`).
2. Set the edge node's `camera.class_id`, `camera.camera_id` and corner seats, and run it as in `docs/edge_node.md`. The heartbeat `edge_nodes/{camera_id}` appears as `idle`.
3. Create a session for that class (`scheduled`), then set it `running`: the heartbeat turns `monitoring` and `session_results/{s}` appears with `monitoring_status` `running`, filling every 10 s.
4. Set it `ended`: `monitoring_status` turns `completed`, one `session_evaluations` document per seat appears, and the heartbeat returns to `idle`.
