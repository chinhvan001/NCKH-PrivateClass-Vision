# Cloud Data Compliance Checklist

Last reviewed: 2026-10-17, against branch `camera-ai` on the team's Firestore schema; §3 item 12 against branch `Web` (last commit 2026-09-20).

Requirement sources:

- *C1SE31 Architecture Design v1.0*: §2.2.2 (no raw video stored or transmitted, no facial recognition), QA02 (100% of frames purged from RAM, TLS 1.3 in transit, AES-256 at rest, RBAC), UC01, UC02, UC03, UC04, UC07, UC09 and UC11.
- The team's Firestore schema diagram (2026-10), with camera-ai's proposed changes in `docs/team_notes_firestore_schema.md`.
- Privacy invariants in the repository `CLAUDE.md`.

**Rule:** cloud sync (Firestore, FCM) must not be enabled until every item in §3 marked *Blocker* is closed.

## 1. What may leave the edge node

Only these schemas may leave the edge node. Each is built by a dataclass or function that rejects bad input. Never build these dicts by hand.

| Schema | Built by | Fields (exact allowlist) | Destination | Status |
|---|---|---|---|---|
| `SessionResult` | `privacy.SessionResult` (+ `SeatResult` per seat) | `session_id`, `camera_id`, `captured_at`, `monitoring_status`, `result_map` (per `seat_id`: `concentration`, `interaction`, `status`) | `EdgeRuntime` → `sync.FirestoreSink.set_result()` → `session_results/{session_id}`, every 10 s of monitoring | Built, not enabled |
| `SeatEvaluation` | `privacy.SeatEvaluation` | `session_id`, `seat_id`, `captured_at`, `concentration`, `avg_concentration`, `distraction`, `observed_sec` | `EdgeRuntime` → `sync.FirestoreSink.set_evaluations()` → `session_evaluations/{session_id}_{seat_id}`, every 5 min and at session end | Built, not enabled |
| `AlertEvent` | `privacy.make_alert_event()` | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec` | `EdgeRuntime` → `sync.FirestoreSink.add_alert()` → `sessions/{session_id}/alerts`; FCM not built | Built, not enabled |
| `EdgeHeartbeat` (device status, no student data) | `sync.EdgeHeartbeat` | `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` | `EdgeRuntime` → `sync.FirestoreSink.set_heartbeat()` → `edge_nodes/{camera_id}` | Built, not enabled |
| `AnonymizedEngagementRecord` | `privacy.anonymize_engagement()` | `seat_id`, `observed_at_sec`, `engagement_score`, `posture_state`, `head_drop_events`, `slumping_events` | `run_pipeline(on_record=...)` → local JSONL (demo and evaluation only); never sent to Firestore | Active, local only |

The sink adds one storage field, `expire_at`, to every session document (results, evaluations, alerts), for a Firestore TTL policy (§3 item 6).

Field rules:

- `seat_id` is a seat position from the class seating plan (`classes/{class_id}/seats` document IDs, or `S1`..`Sn` while a class has none), never a name, student ID or persistent person ID.
- `session_id` is an opaque random ID matching `[A-Za-z0-9_-]{1,64}`. Do not compose it from class, teacher or date names.
- Alert `type` must be one of `head_drop`, `back_turn` or `side_conversation` (`ALERT_TYPES`). `slumping` affects the score only and is never an alert.
- A side conversation produces one alert per seat. There is no pair field.
- Seat `status` is one of `focused`, `drowsy`, `distracted`, `away`; `monitoring_status` one of `running`, `completed`, `incomplete`. Scores are whole numbers 0–100 or null; counts are whole numbers.
- `captured_at` and `expire_at` are UTC wall-clock times from the edge clock. They are allowed because the team's schema needs them and the session document already carries `started_at`, so session-relative seconds would protect nothing extra. Results are captured every 10 s and evaluations every 5 minutes, so they carry no finer timing.
- Alert `start_sec` counts seconds of monitored time since the session started, rounded to 0.1 s. Pauses and camera outages advance that clock by at most 5 s.
- The heartbeat's `last_frame_at` and `updated_at` are wall-clock UTC. They describe the device, not a student, and are never copied into session data.

Never sent:

- Frames, crops or previews.
- Face data or embeddings.
- Body keypoints, keypoint confidences or bounding boxes.
- Track IDs.
- Names or student IDs.
- Per-seat engagement records (they stay on the edge node).
- Camera URLs or credentials.
- Wall-clock timestamps other than `captured_at`, `expire_at` and the heartbeat's device fields.
- Inference logs.

## 2. Controls in place

| Control | Where | Evidence |
|---|---|---|
| No frame is written to disk by production code (`imwrite`, `VideoWriter`, `imencode` are banned in `src/`) | `src/` | `tests/test_privacy_guards.py::test_production_code_never_writes_frames` |
| Each frame's pixel buffer is zeroed after inference, including when inference throws; frames skipped by `inference_every_n_frames` are zeroed unprocessed (best-effort, see §3 item 9) | `pipeline.process_frame()` → `dispose_frame()` in `finally`, used by `run_pipeline` and `EdgeRuntime` | `test_privacy_guards.py::test_pipeline_wipes_every_frame_after_inference`, `test_frame_wiped_even_when_inference_fails`; `test_edge_runtime.py::test_only_every_nth_frame_is_inferred_and_every_frame_is_wiped` |
| The camera is open only while a session is `running` and inside the config's schedule windows; pause, end and shutdown close it | `pipeline/edge_runtime.py` | `test_edge_runtime.py::test_session_start_pause_resume_end_controls_camera_and_writes_results`, `test_active_session_outside_schedule_never_opens_camera` |
| Any preview or debug image is anonymized (face blur + full-frame pixelation) | `privacy.anonymize_preview()`; the demo refuses `--output` without `--allow-persistent-output` | `tests/test_privacy_anonymize.py`; code review of `tests/demo_camera_ai.py` |
| Export schemas are exact allowlists | `privacy/`, `sync.EdgeHeartbeat` | `test_session_output.py`, `test_alert_event.py`, `test_engagement_export.py`, `test_firestore_sink.py::test_overwritten_docs_keep_only_the_latest_version_while_offline` (heartbeat fields), schema asserts in `test_end_to_end_pipeline.py` and `test_demo_camera_ai.py` |
| Local config rejects every unknown key (so `rtsp_url`, `student_id`, `name` or a seat-to-student map cannot be stored) and privacy overrides (`allow_persistent_output`, `frame_buffer_size`); the camera source is referenced by env var name only | `config/local_schema.py` | `tests/test_local_config.py` |
| The class seat plan is read from Firestore with field projections: `row_count`/`column_count` of the class and `row`/`column` of each seat, never `student_id`; its size is capped and it is kept in RAM only | `config/class_layout.py` | `tests/test_class_layout.py` |
| Camera credentials are redacted from logs and error messages (`rtsp://user:pass@` → `rtsp://***@`) | `capture.camera_capture.redact_source()` | `test_privacy_guards.py::test_redact_source_*`, `test_camera_open_failure_does_not_leak_credentials` |
| The Firestore sink accepts only allowlisted schema objects and writes exactly their `to_dict()`, plus `expire_at` on session documents | `sync/firestore_sink.py` | `test_firestore_sink.py::test_sink_only_accepts_allowlisted_schemas_and_valid_config`, `test_session_docs_carry_expire_at_for_ttl_but_heartbeat_does_not`, `test_pipeline_streams_alerts_into_firestore_sink` |
| The offline queue is bounded and RAM-only: alerts are capped (oldest dropped first); results, evaluations and the heartbeat keep only their latest version | `sync.FirestoreSink` | `test_firestore_sink.py::test_full_alert_queue_drops_oldest_alerts`, `test_overwritten_docs_keep_only_the_latest_version_while_offline` |
| Sink logs carry only error types and counters, never document contents or server messages | `sync.FirestoreSink.flush()` | `test_firestore_sink.py::test_failure_logs_never_echo_payload` |
| The service account key is read only from `GOOGLE_APPLICATION_CREDENTIALS`; key file names are git-ignored | `sync.firestore_client_from_env()`, `.gitignore` | `test_firestore_sink.py::test_firestore_client_requires_service_account_key_file` |
| No face detection or landmarks at runtime | The legacy MediaPipe face modules are deleted; `src/` imports no face-detection library | `test_privacy_guards.py::test_production_code_has_no_face_detection` |
| Rules draft for the camera-ai paths, with field allowlists and per-role access | `config/firestore.rules` | `rules-tests/` on the Firestore emulator, in CI |
| Video files, model weights and team documents with contact details cannot be committed | `.gitignore` (`*.mp4`, `*.avi`, `*.pt`, `*.tflite`, `camera-ai/docs/C1SE31-*.pdf`, ...) | `.gitignore` |

## 3. Open issues

| # | Issue | Severity | Proposed resolution |
|---|---|---|---|
| 1 | **Real CCTV footage with identifiable faces is in git history.** `camera-ai/simulated_data/test2.mp4` (third-party watermark) was added in commit `4f948e64`, which is pushed to `origin/camera-ai`. The history was rewritten locally on 2026-10-10 (only the 22 commits from `4f948e64` onward, tree unchanged), but not pushed yet. | Blocker | Force-push the rewritten branch, have the team re-clone, ask GitHub to purge cached views and pull request refs, and confirm the repo is private. Steps: `docs/team_notes_firestore_schema.md` §5. |
| 2 | **`seat_id` is pseudonymous, not anonymous.** UC01 maps student accounts to seat IDs, and UC03 lets parents view their child's data. The team's schema keeps the mapping in a `seat_map` field of the class document, which any reader of the class sees in full, because Rules cannot hide fields. | Blocker | Keep the mapping in `classes/{c}/seats/{seat_id}` documents (proposed to the team), protected by the Rules draft: written only by the homeroom teacher or an admin, never readable by parents, who see only `students/{sid}/reports`. Edge output never contains a student ID, and the edge node reads only `row`/`column` (§2). Closes when the web and app write seat documents and the Rules are deployed (item 7). |
| 3 | **Body keypoints in the cloud.** `CloudEngagementPayload` (`privacy.make_cloud_payload()`) carried keypoints, while the architecture says parents see no skeletal information. | Closed | Team decision recorded 2026-10-10: no keypoints leave the edge node. `make_cloud_payload` and its test are deleted. |
| 4 | **Timestamp precision and upload volume.** Per-seat records used millisecond times and up to one write per seat every 10 s. | Closed | Records no longer leave the edge node. Results every 10 s and evaluations every 5 min: about 950 writes for 40 seats and 45 minutes, including heartbeats. Local records are rounded to whole seconds (`test_engagement_export.py`). |
| 5 | **Encryption (QA02).** Firestore encrypts at rest (AES-256) and the SDK uses TLS by default, but no evidence is recorded. Edge-local files (JSONL exports, `logs/camera-ai.log`) are unencrypted. The offline queue is RAM-only. | High | Save Google's encryption documentation as release evidence and check the TLS version the edge client negotiates. Enable full-disk encryption on edge nodes (BitLocker or LUKS). |
| 6 | **Retention.** Every session document the edge node writes carries `expire_at` (`privacy.retention_days` in the local config), but no TTL policy is enabled and no period is agreed. | Medium | Agree the period with the mentor; the Firebase owner enables Firestore TTL on `expire_at` for `session_results`, `session_evaluations` and the `alerts` collection group. Web-written data (sessions, seats, reports) needs its own retention rule. |
| 7 | **Firestore Rules and IAM are not deployed.** The draft in `config/firestore.rules` is tested on the emulator. The edge node still uses the Admin SDK, which bypasses Rules: an edge key can read the whole database, including students' names and birthdays, parents' emails and the seat→student mapping. | Blocker for sync | Option B in `docs/firestore_security_review.md`: edge nodes sign in with per-node custom tokens (claims `role`, `class_id`, `camera_id`) so the existing edge Rules apply. Merge the draft into the project's rules and deploy it with the same tests. Parents may read only their own child's reports (QA02 RBAC). |
| 8 | **Offline queue** (UC02 alternate flow): built as a bounded RAM queue in `sync.FirestoreSink`. Items still queued when the process exits are lost. | Closed | Persist to disk only if item 5's encryption is in place. |
| 9 | **Frame wipe is best-effort.** `dispose_frame()` zeroes the frame buffer we own. Copies made inside OpenCV, Ultralytics or torch (resized or letterboxed tensors, GPU memory) are not wiped, so QA02's "100% of raw visual frames are purged immediately from RAM" claims more than the code does. | Low | camera-ai claims only the best-effort wipe (`privacy/frame_lifecycle.py`, `src/capture/README.md`, §2). Team: in the next revision of the architecture document and in the final report, word QA02 as "After keypoint extraction no reference to the frame is retained and the frame buffer is zeroed; copies held briefly inside OpenCV, Ultralytics or torch are freed but not zeroed." Close this item once the architecture document is updated. |
| 10 | **Legacy face code** (`detection/face_detector.py`, `detection/face_landmarker.py`, `detection/config.py`, `engagement/head_pose.py`, `tests/test_head_pose.py`) made "no face detection" harder to audit. | Closed | Deleted. `test_privacy_guards.py::test_production_code_has_no_face_detection` fails if `src/` imports MediaPipe or an OpenCV face detector again. |
| 11 | **Logs on disk** (`logs/camera-ai.log`, rotating). No payload bodies are logged. The Firestore sink logs only error types and counters, covered by `test_failure_logs_never_echo_payload`. | Closed | Keep the same rule for future sinks (FCM). |
| 12 | **The web admin stores camera RTSP URLs, credentials included, in Firestore** (`classrooms/{id}.rtsp_url`, written by `backend/routes/camera_routes.py` and `classroom_routes.py` on branch `Web`) and returns them in its camera and classroom APIs. Anyone who can read `classrooms` and reach the camera's network can watch live video, which bypasses every control in §2. The team's schema has no `classrooms` collection; camera-ai never reads the field and takes its source from an environment variable. | High | Web team: remove `classrooms` with its `rtsp_url` values (web task 8 in `docs/web_admin_integration.md`); if a camera address must stay on the web side, keep it as a secret on the web server and mask the password in API responses. |
| 13 | **Minors' personal data in the same Firestore project.** The schema stores students' `full_name`, `birthday` and `gender`, and parents' names and emails, next to the session data. Most students in grades 10–12 are under 18, some under 16. This is outside camera-ai's code but inside this checklist's scope (cloud data). | High | Confirm with the mentor the legal basis and consent needed under Vietnamese personal-data rules (parents' consent for minors), collect it before a pilot, and drop fields the system does not use (does it need `birthday` and `gender`?). |

## 4. Release checklist

| Check | Evidence to keep | Done |
|---|---|---|
| Export allowlists (results, evaluations, alerts, heartbeat) | Tests listed in §2 | [x] |
| No frame written to disk; frames wiped after inference | `test_privacy_guards.py`, `test_edge_runtime.py` | [x] |
| Camera closed outside running sessions and schedule windows | `test_edge_runtime.py` | [x] |
| Camera credentials not logged | `test_privacy_guards.py` | [x] |
| Real footage purged from git history (§3.1) | Rewritten history pushed; GitHub purge confirmation | [ ] |
| Seat→student mapping isolated and rule-protected (§3.2) | Seat documents written by web and app; Rules deployed with `rules-tests/` | [ ] |
| Keypoint upload decision (§3.3) | Team decision 2026-10-10 (no keypoints); `make_cloud_payload` deleted | [x] |
| Upload volume and timing (§3.4) | `test_edge_runtime.py::test_live_results_every_10s_and_alerts_counted_per_seat` | [x] |
| Encryption in transit and at rest (§3.5) | Provider docs, TLS check, edge disk encryption | [ ] |
| Retention TTL (§3.6) | `expire_at` written (`test_session_docs_carry_expire_at_for_ttl_but_heartbeat_does_not`); TTL policy enabled; period agreed | [ ] |
| Least-privilege Rules and IAM (§3.7) | Edge custom tokens; `config/firestore.rules` merged and deployed with `rules-tests/` | [ ] |
| Offline queue bounded and RAM-only (§3.8) | `test_firestore_sink.py` | [x] |
| Sinks do not log payloads (§3.11) | `test_firestore_sink.py::test_failure_logs_never_echo_payload` | [x] |
| Legacy face code removed (§3.10) | Commit; `test_production_code_has_no_face_detection` | [x] |
| Camera credentials not readable from Firestore by clients (§3.12) | `classrooms` removed on branch `Web` | [ ] |
| Consent and minimisation for minors' personal data (§3.13) | Mentor confirmation, consent forms, schema without unused fields | [ ] |
