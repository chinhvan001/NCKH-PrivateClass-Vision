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

- Only modify files under `camera-ai/` and `.github/`, plus `.env`, `.env.example`, `.gitignore` and `CLAUDE.md`. Do not touch anything else in the repo (e.g. `Web`, `flutter_privateclass_vision`).

## Git rules

- Commit messages must NOT include a `Co-Authored-By: Claude ...` trailer (or any other Claude/AI attribution line). PR descriptions must not include a "Generated with Claude Code" line either.

## Repo layout

Only `camera-ai/` contains code. `Web` and `flutter_privateclass_vision` at the root are empty placeholder files.

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
python -m pytest tests -q --ignore=tests/smoke_test.py --ignore=tests/test_head_pose.py

# Single test
python -m pytest tests/test_seat_tracker.py::test_name -q

# Lint/format (pinned in requirements-dev.txt; config in pyproject.toml + .flake8, line length 120; CI runs both)
flake8 src tests tools
black src tests tools

# Visual demo (needs ultralytics + models/*.pt)
python tests/demo_camera_ai.py <video> --seats config/seat_grid.json --engagement-jsonl engagement.jsonl
```

CI excludes `smoke_test.py` (opens a real webcam) and `test_head_pose.py` (legacy facial API). Tests must stay headless: no webcam, GPU, network, model weights, or Firebase credentials (test Firestore code against `tests/fake_firestore.py`). Tests are flat in `tests/test_*.py`; module READMEs that mention `tests/capture/` or `tests/seating/` are outdated.

`tests/demo_camera_ai.py` is a script, not a test (pytest skips it since it isn't named `test_*`). Other tools live in `tools/` (synthetic classroom video generator, SCB-Dataset person-detection evaluation); see `tools/README.md`.

## Architecture

Data flow (headless version in `src/pipeline/engagement_pipeline.py::run_pipeline`; the edge node runs it per session through `src/main.py` -> `src/pipeline/edge_runtime.py::EdgeRuntime`):

```
capture (CameraCapture / CaptureWorker + FrameBuffer)
  -> detection.PoseDetector (YOLOv8-pose, 17 COCO keypoints, optional tiling)
  -> seating (SeatGrid + assign_seats / SeatTracker: shoulder midpoint -> nearest seat)
  -> engagement per seat (posture signals -> PostureMonitor events -> SeatEngagementTracker score)
  -> privacy (anonymize_engagement -> AnonymizedEngagementRecord; dispose_frame in finally)
  -> sync (optional FirestoreSink as on_record/on_alert -> batched Firestore writes)
```

- `PoseProvider` is a Protocol: tests inject a deterministic `ReplayPoseProvider` instead of real inference. Keep new pipeline stages injectable the same way.
- `capture/`: `CaptureWorker` reads on a background thread into a drop-oldest `FrameBuffer` (default size 1). `start()` opens the camera synchronously so `CameraOpenError` surfaces to the caller; transient read failures reconnect with backoff and return `None` instead of raising. Config via `CaptureConfig.from_env()` (`CAMERA_SOURCE`, `CAMERA_FPS`, ...; see `.env.example`).
- `detection/`: the public API exports only `PoseDetector` and `PersonDetector` (YOLO11 person boxes, used for head-count coverage only). `face_detector.py`/`face_landmarker.py` are legacy and deliberately not exported.
- `engagement/`: `posture.py` computes head-drop ratio and torso angle; `posture_monitor.py` handles per-seat baseline calibration, smoothing, and thresholds; `engagement_score.py` turns time spent in each state into a 0–100 score (`rolling_engagement.py` is the windowed variant). `side_conversation.py`, `back_turn.py`, and `hand_activity.py` are optional pose-only alert detectors; back-turn is only valid for `frontal` cameras.
- `seating/`: a `SeatGrid` is tied to one camera mount and must be recalibrated if the camera moves. Use `SeatTracker` for video (continuity + occlusion tolerance) and `assign_seats` for single frames.
- `config/`: `local_schema.py` is a strict JSON schema (`config/local_pipeline.example.json`) that **rejects unknown keys** such as `rtsp_url`, `student_id`, `name`. The camera source is referenced by env var name (`camera.source_env`), never stored inline. `remote_seat_grid.py` loads seat grids from Firestore at `classrooms/{classroom_id}/camera_configs/{camera_id}`, imports `firebase_admin` lazily, keeps the grid in RAM only, and only accepts a newer `config_version`.
- `pipeline/edge_runtime.py`: the Firestore listener only stores `{session_id: state}`; every decision (camera on/off, session start/end, heartbeat, summary) happens in `step()` on the main thread. Records and alerts use monitored seconds since the session start, not wall-clock. Session contract, statuses and limits: `camera-ai/docs/edge_node.md`.
- `sync/`: one `FirestoreSink` per edge node for the whole process (not per session). `add_*`/`set_heartbeat` run inside the frame loop, so they only update a bounded RAM queue; a background thread commits it in batches with backoff. Credentials come only from `GOOGLE_APPLICATION_CREDENTIALS` via `firestore_client_from_env()`, shared with `remote_seat_grid.py`. The Admin SDK bypasses Security Rules: read `camera-ai/docs/firestore_security_review.md` before changing Firestore access. Details: `camera-ai/src/sync/README.md`.
- Sessions belong to the web admin (branch `Web`, Flask + React on the school server); the two sides talk only through Firestore. The edge node listens to top-level `sessions` filtered on `classroom_id`, maps `status` with `sync/firestore_sink.py::WEB_STATUS_TO_STATE` (`live` -> `active`, `completed` -> `ended`), and writes engagement/alerts/summaries under `sessions/{session_id}/`. Contract and open web-side tasks: `camera-ai/docs/web_admin_integration.md`.

## Privacy invariants (enforced by tests, don't break)

- Never write frames to disk: no `cv2.imwrite`/`VideoWriter` in production paths, and no frames in logs or caches. Call `src.privacy.dispose_frame(frame)` in a `finally` after inference (`pipeline.process_frame` does this).
- The edge node opens the camera only while a session is `live` and inside the config's `schedule` windows; pause, end and shutdown close it.
- Any preview or debug display/write must go through `src.privacy.anonymize_preview()` first. The demo blocks video output unless `--allow-persistent-output` is passed.
- No face detection, facial landmarks, embeddings, names, or student IDs in runtime output.
- Never log or put the raw camera source in error messages (RTSP URLs carry credentials); wrap it in `capture.camera_capture.redact_source()`.
- Guard tests live in `tests/test_privacy_guards.py` (no frame-writing calls in `src/`, frames wiped after inference, credential redaction). Open compliance items: `docs/cloud_data_compliance_checklist.md` section 3.
- Output schemas are allowlists. The local export is `AnonymizedEngagementRecord` (no bbox or keypoints). The cloud export is `privacy/cloud_payload.py::make_cloud_payload` (seat_id, keypoints, score in [0,100]). Alerts use `privacy/alert_event.py::make_alert_event` (session_id, seat_id, type in `ALERT_TYPES`, start_sec, duration_sec; session-relative seconds, no wall-clock). End-of-session summaries use `privacy/session_summary.py::make_session_summary`; the device heartbeat is `sync.EdgeHeartbeat`, the only schema allowed wall-clock fields. Add fields only deliberately; see `docs/cloud_data_compliance_checklist.md`.
