# Web Admin Integration

The web admin (branch `Web`: Flask backend in `backend/`, React frontend in `frontend/`, hosted on the school server) and the camera-ai edge nodes share one Firebase project. They never call each other over HTTP. The web backend writes session documents; each edge node listens to the sessions of its classroom and writes its output under them. This page is the contract between the two sides, plus the work still open on the web side.

Edge-side details: `docs/edge_node.md` (behaviour) and `src/sync/README.md` (paths, delivery).

## IDs

- The web admin allows one camera per classroom and uses the `classrooms` document ID as the camera ID. In the edge node's local config, set both `camera.classroom_id` and `camera.camera_id` to that ID.
- A session's `classroom_id` is copied from its class (`classes/{class_id}.classroom_id`) when `POST /api/admin/sessions` creates it. A class without a classroom produces sessions that no edge node sees.
- Session IDs are Firestore auto-IDs. The edge node accepts IDs matching `[A-Za-z0-9_-]{1,64}`.

## Firestore contract

| Path | Written by | Read by | Fields |
|---|---|---|---|
| `classrooms/{c}` | web | web; the edge node never reads it | `classroom_name`, `camera_name`, `ip_address`, `rtsp_port`, `rtsp_url`, `row_number`, `column_number`, `status` |
| `sessions/{s}` | web (`backend/routes/session_routes.py`) | edge: `classroom_id` and `status` only | `class_id`, `teacher_uid`, `classroom_id`, `subject`, `date`, `start`, `end`, `status`, `focus` |
| `sessions/{s}/summaries/{cam}` | edge | web | `session_id`, `status`, `class_average`, `seats` (each `seat_id`, `engagement_score`, `observed_sec`, `head_drop_events`, `slumping_events`) |
| `sessions/{s}/alerts/{id}` | edge | web | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec` |
| `sessions/{s}/engagement/{id}` | edge | web, optional (per-seat timeline) | `seat_id`, `observed_at_sec`, `engagement_score`, `posture_state`, `head_drop_events`, `slumping_events` |
| `classrooms/{c}/edge_nodes/{cam}` | edge | web | `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` |
| `classrooms/{c}/camera_configs/{cam}` | nobody yet (task 5) | edge | Seat grid, see `config/firestore_seat_grid.md` |

Edge output carries seat IDs and session-relative seconds only: no names, student IDs, images or wall-clock times (except the heartbeat's device timestamps). Mapping a `seat_id` to a student goes through the seating chart, which stays on the web side.

## Session status

| `status` | Edge node |
|---|---|
| `scheduled` | Ignored. |
| `live` | Opens the camera (inside the edge node's local schedule windows) and starts scoring. |
| `completed` | Closes the camera and writes the summary as `completed`. |
| `cancelled`, or the document is deleted | Closes the camera and writes the summary as `incomplete`. |
| `paused` | Closes the camera until the status is `live` again. The web admin does not offer it yet. |

- Keep at most one `live` session per classroom. If there are several, the edge node takes the one with the smallest ID.
- The edge node ignores `date`, `start` and `end`. Someone has to set `live` and `completed`; nothing starts a session automatically.
- A `live` session outside the edge node's schedule windows leaves the camera closed, and the heartbeat says `outside_schedule`.

## Tasks for the web team

Each task names where to work on branch `Web` and when it counts as done.

1. **Start and end sessions.** `PUT /api/admin/sessions/<id>` already accepts `status`. Add start and end actions to `frontend/src/components/admin/SessionManagementPanel.jsx`, which still shows hard-coded sessions instead of `GET /api/admin/sessions`. Refuse `live` while another session of the same classroom is `live`. Done when setting `live` turns the heartbeat to `monitoring` and setting `completed` turns the summary to `completed`.
2. **Check before starting (UC04 step 3).** Before allowing `live`, check that `classrooms/{c}/camera_configs/{c}` exists and that the heartbeat is online and recent (task 4). Done when starting a session without a seat grid or with an offline edge node shows an error.
3. **Real focus and alerts.** In `build_session_data`, fill `focus` from `sessions/{s}/summaries`. With one camera per classroom, that is the summary's `class_average`; with several, do what `class_average` does over all cameras' seats: average the non-null `engagement_score` values, weighted by `observed_sec`. A summary still `running` after the session ended means the edge node died, so show it as incomplete. Replace the hard-coded `alerts` in `DashboardPanel.jsx` with `sessions/{s}/alerts` of live sessions. Alert `type` is `head_drop`, `back_turn` or `side_conversation`; `start_sec` counts seconds since the session started, not clock time. Done when the dashboard and session list show no sample data for these fields.
4. **Camera health from the heartbeat.** Read `classrooms/{c}/edge_nodes/{c}`. Treat the node as offline when `online` is false or `updated_at` is more than 30 s old; otherwise show `status` (`unavailable` means "temporarily unavailable"). The ffprobe check in `camera_routes.py` can stay as a setup test, but the edge node never reads the `status` it sets. Done when the camera page reflects an edge node that is stopped.
5. **Seat grid.** Add a calibration screen that writes `classrooms/{c}/camera_configs/{c}` in the format of `config/firestore_seat_grid.md`, raising `config_version` on every change. `row_number` and `column_number` alone do not give seat positions in the image. Until then, write the document by hand in the Firebase console.
6. **Session deletion.** `DELETE /api/admin/sessions/<id>` leaves the `engagement`, `alerts` and `summaries` subcollections behind, because Firestore does not delete subcollections with their parent. Delete them as well, or agree on retention first (`cloud_data_compliance_checklist.md` §3.6).
7. **Credentials.** `rtsp_url` stores camera passwords in a Firestore document and the camera and classroom APIs return it in full (`cloud_data_compliance_checklist.md` §3.12). Move it out of client-readable documents and mask the password in responses. `backend/firebase_config.py` also hard-codes the Firebase Web API key; load it from the environment and restrict it in Google Cloud.

## Open questions for the whole team

- The Flutter app reads `monitoring_sessions`, the web admin writes `sessions`. The edge node follows `sessions`; the app should too, or the team picks one collection.
- The root `firestore.rules` draft has no rules for `sessions`, `users` or `admins`. The camera-ai draft for its paths is `config/firestore.rules`; review both with `docs/firestore_security_review.md`.
- Pausing: the edge node supports `paused`, but `update_session` rejects it. Add it to `allowed_statuses` if teachers need to pause.

## Trying it end to end

1. Create a classroom and a class linked to it in the web admin.
2. Set the edge node's `camera.classroom_id` and `camera.camera_id` to the classroom ID, and run it as in `docs/edge_node.md`. The heartbeat appears as `idle`.
3. Create a session for that class (`scheduled`), then set it `live`: the heartbeat turns `monitoring` and `sessions/{s}/summaries/{c}` appears as `running`.
4. Set it `completed`: the summary turns `completed` and the heartbeat returns to `idle`.
