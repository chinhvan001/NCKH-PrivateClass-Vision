# Cloud Data Compliance Checklist

Last reviewed: 2026-10-02, against branch `camera-ai`.

Requirement sources:

- *C1SE31 Architecture Design v1.0*: §2.2.2 (no raw video stored or transmitted, no facial recognition), QA02 (100% of frames purged from RAM, TLS 1.3 in transit, AES-256 at rest, RBAC), UC01, UC02, UC03 and UC09.
- Privacy invariants in the repository `CLAUDE.md`.

**Rule:** cloud sync (Firestore, FCM) must not be enabled until every item in §3 marked *Blocker* is closed.

## 1. What may leave the edge node

Only three schemas may leave the camera pipeline. Each is built by a single function that rejects bad input. Never build these dicts by hand.

| Schema | Built by | Fields (exact allowlist) | Destination | Status |
|---|---|---|---|---|
| `AnonymizedEngagementRecord` | `privacy.anonymize_engagement()` | `seat_id`, `observed_at_sec`, `engagement_score`, `posture_state`, `head_drop_events`, `slumping_events` | `run_pipeline(on_record=...)`: local JSONL today, Firestore sink planned | Active |
| `AlertEvent` | `privacy.make_alert_event()` | `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec` | `run_pipeline(on_alert=...)` → Firestore/FCM | Schema done, sink not built |
| `CloudEngagementPayload` | `privacy.make_cloud_payload()` | `seat_id`, `keypoints` (`[x, y]` only), `engagement_score` | None (not called by the pipeline) | See §3 item 3 |

Field rules:

- `seat_id` is a calibrated seat position, never a name, student ID or persistent person ID.
- `session_id` is an opaque random ID matching `[A-Za-z0-9_-]{1,64}`. Do not compose it from class, teacher or date names.
- Alert `type` must be one of `head_drop`, `back_turn` or `side_conversation` (`ALERT_TYPES`). `slumping` affects the score only and is never an alert.
- A side conversation produces one alert per seat. There is no pair field.
- Time fields are seconds since the session started, never wall-clock time.

Never sent:

- Frames, crops or previews.
- Face data or embeddings.
- Bounding boxes or keypoint confidences.
- Track IDs.
- Names or student IDs.
- Camera URLs or credentials.
- Wall-clock timestamps.
- Inference logs.

## 2. Controls in place

| Control | Where | Evidence |
|---|---|---|
| No frame is written to disk by production code (`imwrite`, `VideoWriter`, `imencode` are banned in `src/`) | `src/` | `tests/test_privacy_guards.py::test_production_code_never_writes_frames` |
| Each frame's pixel buffer is zeroed after inference, including when inference throws | `run_pipeline` → `dispose_frame()` in `finally` | `test_privacy_guards.py::test_pipeline_wipes_every_frame_after_inference`, `test_frame_wiped_even_when_inference_fails` |
| Any preview or debug image is anonymized (face blur + full-frame pixelation) | `privacy.anonymize_preview()`; the demo refuses `--output` without `--allow-persistent-output` | `tests/test_privacy_anonymize.py`; code review of `tests/demo_camera_ai.py` |
| Export schemas are exact allowlists | `privacy/` | `test_engagement_export.py`, `test_alert_event.py`, `test_cloud_payload.py`, schema asserts in `test_end_to_end_pipeline.py` and `test_demo_camera_ai.py` |
| Local config rejects every unknown key (so `rtsp_url`, `student_id`, `name` cannot be stored) and privacy overrides (`allow_persistent_output`, `frame_buffer_size`); the camera source is referenced by env var name only | `config/local_schema.py` | `tests/test_local_config.py` (covers `rtsp_url` and the two overrides) |
| Camera credentials are redacted from logs and error messages (`rtsp://user:pass@` → `rtsp://***@`) | `capture.camera_capture.redact_source()` | `test_privacy_guards.py::test_redact_source_*`, `test_camera_open_failure_does_not_leak_credentials` |
| Seat grid fetched from Firestore is kept in RAM only, never cached to disk | `config/remote_seat_grid.py` | `tests/test_remote_seat_grid.py`; code review |
| No face detection or landmarks at runtime | `detection/__init__.py` exports only `PoseDetector` and `PersonDetector` | Code review (see §3 item 10) |
| Video files and model weights cannot be committed | `.gitignore` (`*.mp4`, `*.avi`, `*.pt`, `*.tflite`, ...) | `.gitignore` |

## 3. Open issues

| # | Issue | Severity | Proposed resolution |
|---|---|---|---|
| 1 | **Real CCTV footage with identifiable faces is in git history.** `camera-ai/simulated_data/test2.mp4` (third-party watermark) was added in commit `4f948e64`, which is pushed to `origin/camera-ai`. It is untracked now but still downloadable from history. | Blocker | Rewrite history (`git filter-repo --path camera-ai/simulated_data/test2.mp4 --invert-paths`), force-push, have the team re-clone, and ask GitHub to purge cached views. At minimum, confirm the repo is private. |
| 2 | **`seat_id` is pseudonymous, not anonymous.** UC01 maps student accounts to seat IDs in Firestore, and UC03 lets parents view their child's data. The previous version of this checklist said no cloud service may hold that mapping, which contradicts the architecture. | Blocker | Store the seat→student mapping in its own collection, readable only by the class teacher and admin, with parents reaching it only through their linked child. Telemetry and alert collections must never contain a student ID. Firestore Rules must enforce all of this (item 7). |
| 3 | **`CloudEngagementPayload` carries body keypoints.** The architecture says parents see no skeletal information. Records and alerts already cover UC02, UC03, UC07 and UC09 without keypoints. | High | Decide as a team. Recommendation: do not send keypoints to the cloud, and delete `make_cloud_payload` or restrict it to consented research data. |
| 4 | **Timestamp precision and volume.** `observed_at_sec` is rounded to 1 ms, alert times to 0.1 s. The pipeline emits one record per seat per frame. | High | Round records to 1 s. The Firestore sink should aggregate (for example one record per seat every N seconds, or on state change) instead of uploading every frame. |
| 5 | **Encryption (QA02).** Firestore encrypts at rest (AES-256) and the SDK uses TLS by default, but no evidence is recorded. Edge-local files (JSONL exports, `logs/camera-ai.log`, a future offline queue) are unencrypted. | High | Save Google's encryption documentation as release evidence and check the TLS version the edge client negotiates. Enable full-disk encryption on edge nodes (BitLocker or LUKS). |
| 6 | **Retention.** No TTL is configured for records or alerts. | Medium | Set a Firestore TTL policy and agree the retention period with the mentor. |
| 7 | **Firestore Rules and IAM** do not exist yet. | Blocker for sync | The edge service account may only write records and alerts for its own classroom, and read its own seat-grid config. Rules reject unknown fields. Parents may read only their linked child's aggregates (QA02 RBAC). |
| 8 | **Offline queue** (UC02 alternate flow) is not built. | Medium | Queue only allowlisted schema objects; if persisted to disk, item 5 applies. |
| 9 | **Frame wipe is best-effort.** `dispose_frame()` zeroes the frame buffer we own. Copies made inside OpenCV, Ultralytics or torch (resized or letterboxed tensors, GPU memory) are not wiped. | Medium | Word the QA02 claim as "no reference to the frame is retained; the source buffer is zeroed best-effort", not "100% purged from memory". |
| 10 | **Legacy face code is still in the repo:** `detection/face_detector.py`, `detection/face_landmarker.py`, `engagement/head_pose.py` and `tests/test_head_pose.py`. They are not exported, but their presence makes "no face detection" harder to audit. | Low | Delete them, or move them out of `src/`. |
| 11 | **Logs on disk** (`logs/camera-ai.log`, rotating). No payload bodies are logged today. | Low | Future sinks must not log request or record bodies. Add a redaction test when the Firestore sink lands. |

## 4. Release checklist

| Check | Evidence to keep | Done |
|---|---|---|
| Export allowlists (records, alerts) | Tests listed in §2 | [x] |
| No frame written to disk; frames wiped after inference | `test_privacy_guards.py` | [x] |
| Camera credentials not logged | `test_privacy_guards.py` | [x] |
| Real footage purged from git history (§3.1) | Rewritten history; GitHub purge confirmation | [ ] |
| Seat→student mapping isolated and rule-protected (§3.2) | Firestore Rules file and rule tests | [ ] |
| Keypoint upload decision (§3.3) | Team decision record | [ ] |
| Timestamp granularity and upload rate (§3.4) | Sink code and tests | [ ] |
| Encryption in transit and at rest (§3.5) | Provider docs, TLS check, edge disk encryption | [ ] |
| Retention TTL (§3.6) | Firestore TTL config | [ ] |
| Least-privilege Rules and IAM (§3.7) | Rules and IAM review | [ ] |
| Legacy face code removed (§3.10) | Commit | [ ] |
