# Proposal: Scoring on the Web Backend, and Aligning Firestore with the Agreed Diagram

Written 2026-10-29 for the team and the mentor. The document has three parts:

- Part 1 designs the move of the concentration scoring from camera-ai to the web backend.
- Part 2 compares the agreed Firestore diagram with the live database and the code, and proposes changes.
- Part 3 splits the work into packages.

Status on 2026-10-30:

- Package B (edge windows) and the code side of Part 2 are implemented.
- Package A is assigned to the new team member.
- The schedule is `docs/plan_to_2026-12-13.md`.

The facts come from these sources:

- The live project `private-class-vision`, read on 2026-10-29. Only field names and types were read, no values.
- The working tree of branch `camera-ai`.
- Branches `Web` (2026-10-27), `main` and `feature-dang-lam` (2026-10-26).

## Part 1. Moving the scoring to the backend

### 1.1 What the edge node computes today

`src/pipeline/engagement_pipeline.py::EngagementEngine` runs these steps on every inferred frame, for each seat that has a person:

1. It assigns each pose to a seat with `SeatTracker`.
2. It computes the head-drop ratio and the torso angle, smoothed over 3 s. The torso baseline comes from the first 5 s of the seat.
3. `PostureMonitor` raises a head-drop or slumping event once a signal stays past its threshold for 5 s.
4. It checks hand activity: are the wrists moving or still?
5. It sets the frame's posture state to `normal`, `slumping` or `head_drop` (`classify_posture_state`).
6. It runs the back-turn and side-conversation detectors (side conversation compares pairs of seats). `AlertManager` turns their output into alert episodes, with a 60 s cooldown and a 2 s gap.

Every 10 s of monitored time, `EdgeRuntime` then does the following:

- It computes the score as 100 × (1 − head_drop share − 0.5 × slumping share) (`compute_score_from_durations`). `concentration` covers the last 60 s and `avg_concentration` the whole session so far.
- It sets the seat status:
  - `away`: not seen for 30 s;
  - `drowsy`: `head_drop`;
  - `distracted`: slumping, or a back turn or side conversation in the last 5 s;
  - `focused` otherwise.
- It counts `observed_sec`, `distraction` (all alerts) and `interaction` (side-conversation alerts).
- It writes `session_results` every 10 s, and `session_evaluations` every 5 minutes and at the end.

### 1.2 Where to cut

| Stays on the edge node | Moves to the backend |
|---|---|
| Steps 1–6 above: pose, seats, signals, baselines, posture events, hand activity, posture state per frame, back-turn and side-conversation detection, alerts | The formula and its constants, the 60 s and whole-session scores, the seat status rules, `observed_sec`, `distraction`, `interaction`, the evaluations, and every document the web and the app read |

Steps 1–6 must stay on the edge node for two reasons:

- They need every frame.
- Their input is keypoints, and keypoints never leave the edge node (team decision, checklist §3.3). They are also too heavy to send: 40 seats × 17 keypoints × 3 values at 2–5 inferred frames per second is 4,000 to 10,000 numbers per second for one class.

Instead, every 10 s the edge node sends how long each seat spent in each posture state. With that, the backend owns every number a teacher or parent sees. It can change those numbers without touching the edge nodes, and it can recompute past sessions from the stored data.

The move does not centralise the posture thresholds: how far a head must drop, and for how long. Changing them still means changing the edge config. If the team wants them central too, the web can write them to `camera_configs/{camera_id}` and the edge node can read them when a session starts. Moving that computation itself would mean sending keypoints.

### 1.3 Transport: Firestore, not HTTP

The edge node writes one document per 10 s of monitoring, and a backend worker turns those documents into results. Firestore is the better transport for three reasons:

- The edge node's `FirestoreSink` already batches, retries and queues while offline. HTTP would need all of that again. It would also need credentials for each edge node on the backend, and a backend that every edge node can reach.
- The sides keep talking only through Firestore, so `backend/tests/test_edge_contract.py` keeps testing both of them together.
- The windows stay stored, so a worker restart or a formula change only means recomputing.

Direct HTTP from the edge node to the backend is the fallback if Firestore costs become a problem (§1.7).

### 1.4 The window document

Path: `session_windows/{session_id}_{run}_{seq}`. The edge node writes it; only the backend reads it, and the Rules deny it to every client.

| Field | Meaning |
|---|---|
| `session_id`, `camera_id` | The session and the edge node. |
| `run` | Random 8-character ID, new each time the edge node starts or resumes the session. A restart resets the edge clock, and `run` keeps the IDs unique. |
| `seq` | 0, 1, 2, … within the run. |
| `start_sec`, `end_sec` | Monitored seconds since the run started. As today, a pause or an outage advances this clock by at most 5 s. |
| `captured_at`, `expire_at` | UTC time from the edge clock. `expire_at` is for the TTL policy. |
| `monitoring_status` | `running`. The last window of a session says `completed` or `incomplete`. |
| `seats` | Seat ID → the fields below. Only seats seen at least once in this window. |

Fields for each seat:

| Field | Meaning |
|---|---|
| `normal_sec`, `slumping_sec`, `head_drop_sec` | Time in each posture state during the window; their sum is the time the seat was seen. A gap of more than 30 s between two sightings counts for nothing. |
| `last_seen_sec` | Monitored second of the last sighting. |
| `last_state` | Posture state at that sighting. |
| `last_behaviour_sec` | Monitored second of the last back turn or side conversation in the window, or null. |
| `alerts` | Number of alerts that started in the window, per type (`head_drop`, `back_turn`, `side_conversation`). |

The window holds no keypoint, box, track ID, image, name or student ID. That is the same rule as for every other edge output, enforced by an allowlist dataclass in `camera-ai/src/privacy/` and its tests. A window for 40 seats is about 3 KB.

Alerts stay as they are: the edge node writes them to `sessions/{s}/alerts`. They need frame timing, and the teacher needs them within seconds. The alert counts in each window let the backend compute `distraction` and `interaction` without reading the alerts.

### 1.5 The backend side

- **`backend/services/scoring_service.py`:** pure functions with no Firestore access. From a session's windows, it computes for each seat:
  - `concentration`: the last 6 windows of the latest run;
  - `avg_concentration`: all windows;
  - `observed_sec`;
  - `status`: `away` when the latest `end_sec` minus `last_seen_sec` is more than 30;
  - `distraction` and `interaction`.

  All constants live in one place: slump credit 0.5, the 60 s score window, away after 30 s, behaviour hold 5 s, minimum observation 60 s.
- **`backend/jobs/scoring_worker.py`:** a long-running process, like the report job, that polls every 5 s.
  - It reads new windows and keeps each running session's totals in memory.
  - It writes `session_results/{s}` after each window, and `session_evaluations` at the end (and every 5 minutes, if the team keeps that).
  - The results are a pure function of the windows, so running it twice or restarting it does no harm. On start, it rebuilds the totals from the stored windows.
- **Report job:** it computes from the windows itself when the worker missed a session, so parent reports never depend on the worker being up.
- **Readers:** the web live view, the reports, the dashboard and the app keep reading the same `session_results` and `session_evaluations`. Nothing changes for them.

### 1.6 Steps

1. Agree on this contract: the fields, the collection name, and who reads it.
2. Build both sides in parallel:
   - Edge: write windows next to the current outputs, behind a local config flag.
   - Backend: the scoring service and the worker, writing to a shadow collection.
   - Contract test: for a replayed session, the backend's numbers must match the edge node's own within 1 point, with equal statuses. The one known difference: `avg_concentration` may differ where a seat was hidden for more than 30 s, because the edge's whole-session tracker counts such a gap and the windows do not. The windows' behaviour is the intended one.
3. Run both outputs on real sessions for a week and compare them.
4. Switch: the worker writes `session_results` and `session_evaluations`, and the edge node stops writing them (flag off).
5. Remove the scoring code from camera-ai. `engagement_score.py` keeps `classify_posture_state`; `rolling_engagement.py` goes.

### 1.7 Costs, failures, retention

- **Writes:** for a 45-minute session of a 40-seat class, the edge node writes 270 more documents (the windows) and the worker reads them. The 270 result writes move from the edge node to the backend. That makes about 1,200 writes per session instead of 950 (team notes §1).
  - The free plan's 20,000 writes per day then covers about 16 sessions a day.
  - Writing evaluations only at the end brings a session back to about 900 writes; the windows already make interrupted sessions recoverable.
- **Latency:** the live view lags 10–15 s instead of 10 s.
- **Worker down:** the live view stops updating, but nothing is lost; the worker catches up on restart.
- **Edge offline:** windows wait in its RAM queue, as alerts do today. If the queue overflows, the session becomes `incomplete`.
- **Retention:** windows are more detailed than results, since they hold per-seat posture time every 10 s. There are two options:
  - delete a session's windows once its parent reports are written;
  - keep them for the validation study (Part 3, package D) for a period agreed with the mentor (checklist §3.6).

### 1.8 Questions for the team

- Does "the scoring" mean only the formula and its windows, as proposed here? Or the posture thresholds too? If so, the thresholds would be pushed to the edge as config.
- Where does the worker run, and is it up during every lesson? A natural place is the school server, next to the report job.
- What should `interaction` mean? Today it counts side-conversation alerts, as a provisional definition. Participation, such as raising hands, would need a new edge detector that sends one more duration per window.

## Part 2. Schema review against the agreed diagram

### 2.1 What the live database holds (2026-10-29)

- **Legacy collections.** The diagram's collections exist, but older ones sit next to them: `classes` (13 docs), `students` (43), `enrollments` (41), `class_members` (1), `monitoring_sessions` (5) and `classrooms` (3).
  - The Flutter app (branches `main` and `feature-dang-lam`) still reads `classes`, `students`, `enrollments`, `monitoring_sessions` and `classrooms`.
  - The web's student page reads `class_members`.
- **Two camera models at once.**
  - `cameras/p302` and `cameras/p303` are seed documents in the diagram's shape, linked from `classes2.camera_id` of 12A1 and 12B2.
  - The camera page writes `classrooms` and `camera_configs` instead; this is where Camera 201 for 11B2 lives.
  - No code writes `cameras`, `classes2.camera_id`, `sessions.camera_id` or `sessions.monitored_students`: all of them are seed data.
- **Mixed types.** `students2.birthday` is a timestamp or a string, and `students2.is_active` a bool or a string. `sessions.session_date`, `start_time` and `end_time` are timestamps or strings.
- **Broken or stray data:**
  - `classes2/AU8lrCJ2ytRgnBAe0nhh` has a `seat_map` with 4 seats but no `class_name` and no grid, so the timetable shows its ID as a class name;
  - a stray `classes2.seatmap` field sits next to `seat_map`;
  - one `teachers` field is named after an email address;
  - `parents` has both `e-mail` and `email`;
  - `sessions` still has the legacy fields `aggregated_evaluation`, `class_attention_score` and `day_of_week`;
  - some camera names in `cameras` end with newlines.
- **A stuck session.** A session left `running` since 2026-10-02, without timetable fields, kept the 11B2 camera on until it was ended by hand on 2026-10-28.
- **Open Rules.** The deployed Rules let anyone read the whole database without signing in (checklist §3.7).

### 2.2 Collection by collection

General rule: keep the live collection and field names, because the code and the app already use them, and fix the diagram's labels instead. Renaming would mean migrating every document and every reader, for nothing.

| Diagram | Live database and code | Proposal |
|---|---|---|
| `session` | `sessions` | Adopt `camera_id`, copied from the class when the session is created. The edge node then listens to `sessions` where `camera_id` is its own, so a class can use another room for one lesson (team notes item 9). Store `session_date` as `YYYY-MM-DD` and `start_time`/`end_time` as `HH:MM` strings; `started_at`/`ended_at` stay timestamps. Drop `aggregated_evaluation`, `class_attention_score` and `day_of_week`. Add the status values (`scheduled`, `running`, `paused`, `completed`, `cancelled`) to the diagram. |
| `session.monitored_student` (map, key = seat ID) | 2 seed sessions carry `monitored_students`. The web freezes the seating into `session_rosters/{s}`, and the edge node writes `session_evaluations` | Keep the content, but as a subcollection `sessions/{s}/monitored_students/{seat_id}` rather than a map in the session document (reasons below). The web writes `student_id`, `row` and `column` at the first start, replacing `session_rosters`. At the end, the scoring worker adds `is_present` (seen for at least 60 s), `attention_score` (`avg_concentration`) and `is_attention` (score of at least 70, the reports' "stable" level); the teacher writes `note`. Once the worker writes it, it can also replace `session_evaluations`, with `observed_sec` and `distraction` added. |
| `classes2` | Same, plus `subject` and a stray `seatmap` | Make `camera_id` the only link between a class and a camera; today the link is `camera_configs/{camera}.class_id`. The web refuses a camera that another class already uses. The edge node finds its class with `where camera_id == own camera_id` and a projection on `row_count`/`column_count`, so it still never reads `seat_map`. Delete `seatmap`, and repair or delete `AU8lrCJ2ytRgnBAe0nhh`. Either add `subject` to the diagram or drop it. |
| `cameras` | 2 seed docs. The camera page uses `classrooms` + `camera_configs`. The app reads `camera_status` and `row_number` from `classrooms` | Adopt `cameras/{camera_id}`, with the document ID equal to the edge node's `camera_id`, the key that `edge_nodes`, `seat_regions` and `session_results.camera_id` already use.<br>Keep `room_name`, `camera_name`, `ip_address`, `rtsp_port`, and add the stream path.<br>Do not store `rtsp_url`: it carries the camera's password, and the app can read `cameras`. Keep it in `camera_configs/{camera_id}.source`, which is denied to every client.<br>Do not store `camera_status`: read it from `edge_nodes/{camera_id}`, because a stored copy goes stale.<br>The seat grid belongs to the class (`classes2.row_count`/`column_count`, which the edge node reads). Keep `row_number`/`column_number` only as the room's capacity, and have the web refuse a class grid larger than that.<br>Drop `class_name`.<br>Move the camera page from `classrooms` to `cameras`. |
| `session_result` | `session_results`, written by the edge node | Keep the name and the fields. Add `session_id` (the diagram has no link to the session), `monitoring_status` and `expire_at` to the diagram. The writer becomes the scoring worker (Part 1). |
| `student2` | `students2` | Rename the diagram's `fullname` to `full_name`. Store `birthday` as a timestamp and `is_active` as a bool. Drop `gender` unless a screen needs it (checklist §3.13). Add `class_id`: the diagram gives no class to a student who is not seated yet, which is why the web still reads the legacy `class_members`; `seat_map` stays the seating. `parent_id` must hold the parent's Auth UID; nothing writes it yet. |
| `parent` | `parents` | Use the parent's Auth UID as the document ID. Merge `e-mail` into `email`. Drop `birthday`, which is not in the diagram. |
| `teacher` | `teachers`, plus `users` in two backend routes | Delete the field named after an email. Add `uid`, `auth_provider` and `auth_status` (used by the web's invite flow) to the diagram. Settle `teachers` versus `users` in the backend. |
| `admin` | `admins` | Keep. The fields match the diagram. |

`monitored_students` should be a subcollection, not a map in the session document, for three reasons:

1. Every edge node listens to session documents, and a listener receives whole documents. Student IDs inside them would reach the edge node, which must never see them.
2. Rules cannot hide one field. Anyone allowed to read a session, the teacher app's timetable for instance, would read every student's score.
3. Writing scores into the session document would rewrite it while the edge node and the app are listening to it, waking both of them every time.

### 2.3 What the diagram should add

| Path | Why |
|---|---|
| `sessions/{s}/alerts/{id}` | Alerts (UC09). |
| `edge_nodes/{camera_id}` | Heartbeat: the camera's status and the pre-start check. |
| `camera_configs/{camera_id}` | The RTSP URL with the camera's account, denied to every client. |
| `seat_regions/{camera_id}` | Seat rectangles drawn on the web. |
| `students2/{sid}/reports/{s}` | The parents' view (UC03). |
| `session_evaluations/{s}_{seat}` | Until `monitored_students` replaces it. |
| `session_windows/{id}` | Only if Part 1 is adopted. |

Also fix the diagram's typos: `sesion_type`, `mnoitored_student`, `concetration`, and `create_at`, `update_at`, `create_day`. The live names are `created_at`, `updated_at` and `create_date`.

### 2.4 Order of work

1. Deploy the Rules (checklist §3.7) and export a backup (`gcloud firestore export`).
2. Clean the data of §2.1 with one script that has a dry-run mode.
3. Merge the `Web` branch's commit of 2026-10-27. It changes the camera, class and student pages, which the `camera-ai` working tree also changes.
4. Web: `cameras`, `classes2.camera_id`, `sessions.camera_id` and `monitored_students`; the edge node follows `camera_id`. One pull request per side, tested together in `test_edge_contract.py`.
5. App: read the new collections (team notes §3).
6. Retire the legacy collections once nothing reads them.

Part 1 can run beside steps 4–6, because it only adds `session_windows`.

Stuck sessions also need a guard:

- The web should flag or end a session still `running` more than an hour after its `end_time`.
- The edge node should ignore a `running` session whose `session_date` is not today.

## Part 3. Work packages

| Package                   | Content                                                                                                                                                                                                                                 | Needs                                          | Done when                                                                                      |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| A. Backend scoring        | §1.5: scoring service, worker, report-job fallback, parity test                                                                                                                                                                         | Python; the contract agreed                    | Parity within 1 point on the demo replay; tests run without credentials; a restart is harmless |
| B. Edge windows           | §1.4: allowlist, window accumulation, dual-write flag, privacy tests                                                                                                                                                                    | camera-ai internals and the privacy invariants | Windows appear on the fake database and in a real session; the guard tests pass                |
| C. Schema alignment       | §2.2 on the web side, plus the cleanup script with a dry run                                                                                                                                                                            | Flask/React; the web team                      | The contract test passes; the dry-run report is reviewed before the real run                   |
| D. Validation study       | Label 10-s windows of consented or public classroom video (SCB-Dataset tools in `tools/`), compare the labels with the computed status and score, and tune the slump credit and thresholds, which are still unvalidated starting values | Data work; no production access                | Agreement figures for the research report, and proposed constants                              |
| E. Rules and edge sign-in | Deploy the Rules; custom tokens for edge nodes (security review, option B)                                                                                                                                                              | The Firebase owner                             | `rules-tests/` passes on the deployed rules                                                    |

A new team member starts with the offline demo (`backend/tests/demo_server.py`), the test suites, `docs/edge_node.md`, this document and the checklist. They work on a separate test Firebase project, never with the production service account key.
