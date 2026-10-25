# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication rules

- Chat replies: always in Vietnamese.
- Produced documents (Markdown/docs/reports/READMEs you write or rewrite): always in English. Code comments and docstrings still match the surrounding code (Vietnamese, mostly without diacritics).
- When a task is completed, end the reply with a checklist in this format:

  ```markdown
  # <Task name>
  ## <Checklist item 1>
  ## <Checklist item 2>
  ```

## Edit scope

- Only modify files under `camera-ai/`, `backend/`, `frontend/` and `.github/`, plus `.env`, `.env.example`, `.gitignore` and `CLAUDE.md`. Do not touch anything else in the repo, in particular the Flutter app at the root (`lib/`, `android/`, `ios/`, `pubspec.yaml`, the root `firebase.json` and `firestore.rules`, ...) and `flutter_privateclass_vision`.
- `backend/` and `frontend/` are the web team's code (branch `Web`): change them only for the web ↔ edge integration.

## Git rules

- Commit messages must NOT include a `Co-Authored-By: Claude ...` trailer (or any other Claude/AI attribution line). PR descriptions must not include a "Generated with Claude Code" line either.

## Repo layout

This branch (`camera-ai`) holds three parts: `camera-ai/` (the edge pipeline), `backend/` + `frontend/` (the web admin, merged from branch `Web` on 2026-10-23) and the Flutter app at the root (from `main`). `flutter_privateclass_vision` at the root is an empty placeholder file.

- `backend/`: Flask API on the Firebase Admin SDK (`firebase_config.py`; blueprints in `routes/`, logic in `services/`). Endpoints check an admin's Firebase ID token with `routes/test_helpers.py::require_admin` (or `admin_only` for a whole blueprint).
- `frontend/`: React 19 + Vite; the dev server proxies `/api` to `127.0.0.1:5000`. `src/firebase.js` (exports `auth`, `googleProvider`) is gitignored and must exist locally to build. API calls take headers from `src/utils/AuthSession.js::getAuthHeaders`.

`camera-ai/` is a Python edge pipeline that scores classroom engagement from **pose skeletons only**, keyed by a pseudonymous `seat_id` (a calibrated seat position, never an identity).

## Commands

Run everything from `camera-ai/` (imports are `src.xxx`; `tests/conftest.py` puts `camera-ai/` on `sys.path`). Local venv: `camera-ai/venv` (Python 3.14). Supported: Python 3.12+; CI tests 3.12 and 3.14, so do not use 3.13+-only syntax or stdlib APIs.

```powershell
pip install -r requirements-dev.txt   # runtime (requirements.txt) + pytest/black/flake8

# Model weights are not in git (*.pt is ignored). Ultralytics auto-downloads them on first
# PoseDetector/PersonDetector load; prefetch for offline edge nodes:
python -c "from ultralytics.utils.downloads import attempt_download_asset as d; [d(f'models/{m}') for m in ('yolov8n-pose.pt', 'yolo11s.pt')]"

# Edge node (needs the camera source env var, GOOGLE_APPLICATION_CREDENTIALS and model weights; see docs/edge_node.md)
python -m src.main --config config/local_pipeline.json

# Same as CI (.github/workflows/camera-ai-ci.yml, matrix 3.12 + 3.14, only pytest/numpy/opencv-headless/tzdata + lint tools installed; lint runs on 3.12 only)
python -m pytest tests -q --ignore=tests/smoke_test.py

# Single test
python -m pytest tests/test_seat_tracker.py::test_name -q

# Firestore rules tests: config/firestore.rules on the emulator (Node 24 + Java 21; CI job firestore-rules)
cd rules-tests; npm ci; npm test

# Lint/format (pinned in requirements-dev.txt; config in pyproject.toml + .flake8, line length 120; CI runs both)
flake8 src tests tools
black src tests tools

# Visual demo (needs ultralytics + models/*.pt)
python tests/demo_camera_ai.py <video> --seats config/seat_grid.json --engagement-jsonl engagement.jsonl
```

Web admin, from the repo root (CI: `.github/workflows/web-ci.yml`):

```powershell
# Backend tests: firebase_admin is stubbed with camera-ai's FakeFirestore (backend/tests/conftest.py), so no
# credentials; test_edge_contract.py runs the real EdgeRuntime too. Needs Flask, flask-cors, requests in the venv.
camera-ai/venv/Scripts/python -m pytest backend/tests -q

# Parent report job (from backend/, real Firebase config): one pass; schedule every 10 min or add --every 600
cd backend; python -m jobs.parent_reports

# Offline demo (no Firebase, camera or model): backend on the fake database + the real EdgeRuntime with simulated
# poses + the report job; writes a stub frontend/src/firebase.js if missing. Then `npm run dev` in frontend/ and
# open http://localhost:5173/api/demo-login; /api/demo/db/<path> shows the stored documents.
camera-ai/venv/Scripts/python backend/tests/demo_server.py

# Frontend build (needs frontend/src/firebase.js); `npm run lint` still fails on errors in the existing code,
# keep new code clean. Import paths must match file names exactly: CI builds on case-sensitive Linux.
cd frontend; npm ci; npm run build
```

CI excludes `smoke_test.py` (opens a real webcam). Tests must stay headless: no webcam, GPU, network, model weights, or Firebase credentials (test Firestore code against `tests/fake_firestore.py`). Tests are flat in `tests/test_*.py`; module READMEs that mention `tests/capture/` or `tests/seating/` are outdated.

`tests/demo_camera_ai.py` is a script, not a test (pytest skips it since it isn't named `test_*`). Other tools live in `tools/` (synthetic classroom video generator, SCB-Dataset person-detection evaluation); see `tools/README.md`.

## Architecture

Data flow (headless version in `src/pipeline/engagement_pipeline.py::run_pipeline`; the edge node runs it per session through `src/main.py` -> `src/pipeline/edge_runtime.py::EdgeRuntime`):

```
capture (CameraCapture / CaptureWorker + FrameBuffer)
  -> detection.PoseDetector (YOLOv8-pose, 17 COCO keypoints, optional tiling)
  -> seating (SeatGrid + assign_seats / SeatTracker: shoulder midpoint -> nearest seat)
  -> engagement per seat (posture signals -> PostureMonitor events -> SeatEngagementTracker score)
  -> privacy (dispose_frame in finally; per-seat AnonymizedEngagementRecord stays local)
  -> sync (EdgeRuntime -> FirestoreSink: session_results, session_evaluations, alerts, heartbeat; batched writes)
```

- `PoseProvider` is a Protocol: tests inject a deterministic `ReplayPoseProvider` instead of real inference. Keep new pipeline stages injectable the same way.
- `capture/`: `CaptureWorker` reads on a background thread into a drop-oldest `FrameBuffer` (default size 1). `start()` opens the camera synchronously so `CameraOpenError` surfaces to the caller; transient read failures reconnect with backoff and return `None` instead of raising. Config via `CaptureConfig.from_env()` (`CAMERA_SOURCE`, `CAMERA_FPS`, ...; see `.env.example`).
- `detection/`: the public API exports only `PoseDetector` and `PersonDetector` (YOLO11 person boxes, used for head-count coverage only). There is no face detection code; `tests/test_privacy_guards.py` fails if `src/` imports a face-detection library.
- `engagement/`: `posture.py` computes head-drop ratio and torso angle; `posture_monitor.py` handles per-seat baseline calibration, smoothing, and thresholds; `engagement_score.py` turns time spent in each state into a 0–100 score (`rolling_engagement.py` is the windowed variant). `side_conversation.py`, `back_turn.py`, and `hand_activity.py` are optional pose-only alert detectors; back-turn is only valid for `frontal` cameras.
- `seating/`: a `SeatGrid` is tied to one camera mount and must be recalibrated if the camera moves. Use `SeatTracker` for video (continuity + occlusion tolerance) and `assign_seats` for single frames. `seat_layout.py` places seats from row/column with a perspective homography of the four calibrated corner seats.
- `config/`: `local_schema.py` is a strict JSON schema, version 2 (`config/local_pipeline.example.json`), that **rejects unknown keys** such as `rtsp_url`, `student_id`, `name`. The camera source is referenced by env var name (`camera.source_env`), never stored inline; `camera.class_id`/`camera_id` name the class and the heartbeat document; `seating.corner_seats` holds the calibration. `class_layout.py` reads only `row_count`/`column_count` of `classes2/{c}` at session start (a field projection: never the class's `seat_map`, which maps seats to students), numbers seats `S01`, `S02`, ... row by row like the web admin's `seat_map` keys, caps the plan at 50x50 and keeps it in RAM only.
- `pipeline/edge_runtime.py`: the Firestore listener only stores `{session_id: state}`; every decision (camera on/off, session start/end, heartbeat, results) happens in `step()` on the main thread. `session_results` every 10 s and `session_evaluations` every 5 min of monitored time (plus at the end); alerts use monitored seconds since the session start. A seat plan that fails to load reports `unavailable` and retries. Session contract, statuses and limits: `camera-ai/docs/edge_node.md`.
- `sync/`: one `FirestoreSink` per edge node for the whole process (not per session). `add_alert`/`set_*` run inside the frame loop, so they only update RAM (bounded alert queue, latest-only overwritten documents); a background thread commits in batches with backoff and adds `expire_at` to session documents. Credentials come only from `GOOGLE_APPLICATION_CREDENTIALS` via `firestore_client_from_env()`; `main.py` shares the client with `class_layout.py`. The Admin SDK bypasses Security Rules: read `camera-ai/docs/firestore_security_review.md` before changing Firestore access. Details: `camera-ai/src/sync/README.md`.
- The project follows the team's Firestore schema as the web admin built it (Flutter app on `main`); the sides talk only through Firestore. The edge node listens to top-level `sessions` filtered on `class_id`, maps `status` with `sync/firestore_sink.py::WEB_STATUS_TO_STATE` (`running` -> `active`, `completed` -> `ended`; the older `live`/`ended` too), and writes `session_results/{s}`, `session_evaluations/{s}_{seat}`, `sessions/{s}/alerts` and `edge_nodes/{camera_id}`. The web side of the contract is `backend/services/monitoring_service.py` (pre-start checks, `session_rosters/{s}` frozen at the start, live view, alerts, edge status, session deletion with its edge documents, `data_status` for interrupted sessions) plus `services/evaluation_service.py`/`dashboard_service.py` and the parent report job (`services/report_service.py`, `jobs/parent_reports.py`, writing `students2/{sid}/reports/{s}`); the camera page never stores RTSP URLs (they live only in the edge node's environment); `backend/tests/test_edge_contract.py` runs both sides on one fake database, so change them together. Contract and open web/app tasks: `camera-ai/docs/web_admin_integration.md`; choices still to confirm with the team: `camera-ai/docs/team_notes_firestore_schema.md`.

## Privacy invariants (enforced by tests, don't break)

- Never write frames to disk: no `cv2.imwrite`/`VideoWriter` in production paths, and no frames in logs or caches. Call `src.privacy.dispose_frame(frame)` in a `finally` after inference (`pipeline.process_frame` does this).
- The edge node opens the camera only while a session is `running` and inside the config's `schedule` windows; pause, end and shutdown close it.
- Any preview or debug display/write must go through `src.privacy.anonymize_preview()` first. The demo blocks video output unless `--allow-persistent-output` is passed.
- No face detection, facial landmarks, embeddings, names, or student IDs in runtime output.
- Never log or put the raw camera source in error messages (RTSP URLs carry credentials); wrap it in `capture.camera_capture.redact_source()`.
- Guard tests live in `tests/test_privacy_guards.py` (no frame-writing calls or face-detection imports in `src/`, frames wiped after inference, credential redaction). Open compliance items: `docs/cloud_data_compliance_checklist.md` section 3.
- Output schemas are allowlists. Firestore gets only `privacy/session_output.py` (`SessionResult` with per-seat `SeatResult`, `SeatEvaluation`: seat IDs, 0–100 scores, counts, seat status, `captured_at`), alerts from `privacy/alert_event.py::make_alert_event` (session_id, seat_id, type in `ALERT_TYPES`, start_sec, duration_sec in session-relative seconds) and the device heartbeat `sync.EdgeHeartbeat`; the sink adds only `expire_at`. Per-seat `AnonymizedEngagementRecord` (no bbox or keypoints) stays local (JSONL). Keypoints never leave the edge node (team decision, checklist §3.3). Add fields only deliberately; see `docs/cloud_data_compliance_checklist.md`.
