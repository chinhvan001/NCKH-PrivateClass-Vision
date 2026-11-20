# Module `sync/`

The edge node's link to the web admin. Camera AI and the web admin always run on the same machine, so they exchange JSON files in one folder instead of going through Firestore. Camera AI needs no Firebase account, and its frequent writes (every 10 s) cost nothing against the Firebase project's daily quota. The web side of the same files is `backend/services/edge_store.py`.

The sink accepts only the allowlisted schemas built in `privacy/`, plus `EdgeHeartbeat`, which carries device status only.

## Folder

`edge-data/` at the repository root (`DATA_DIR`). Both sides compute the same path from their own location, so run them from the same checkout. The folder is git-ignored. It holds camera passwords and classroom results, so it must stay on this machine: back it up only to encrypted storage, and enable full-disk encryption (compliance checklist §3.5).

Both sides create its files readable by their owner only (mode `0o600`). Windows ignores that mode, so once the folder exists (after the first camera is added), limit it to the account that runs camera AI and the web backend, from the repository root:

```powershell
icacls edge-data /inheritance:r /grant:r "${env:USERNAME}:(OI)(CI)F"
```

| Path | Written by | Read by | Content |
|---|---|---|---|
| `cameras/{camera_id}.json` | web admin camera page (add, edit) | camera AI: the list every 30 s; `source` each time a camera opens | `angle_type`, `source` (RTSP URL with the camera's user and password, percent-encoded). Never logged, never returned by the web API |
| `camera_sessions/{camera_id}.json` | web admin, when a session starts and at every status change | camera AI, every second | The camera's current session: `session_id`, `status` (as on the web: `running`, `paused`, `completed`), `class_id`, `row_count`, `column_count`, `seat_regions` (`image_width`, `image_height`, `seats`), copied from the class and from `seat_regions/{camera_id}` when the session starts. Never the class's `seat_map` |
| `edge_nodes/{camera_id}.json` | camera AI | web admin: camera page, pre-start check, live view, dashboard | `EdgeHeartbeat.to_dict()` |
| `sessions/{session_id}/result.json` | camera AI, overwritten | web admin live view and reports | `SessionResult.to_dict()` |
| `sessions/{session_id}/evaluations.json` | camera AI, overwritten | web admin reports and dashboard | `{seat_id: SeatEvaluation.to_dict()}`. Seats seen only before an edge restart keep their last evaluation |
| `sessions/{session_id}/windows.jsonl` | camera AI, one line per window | the web backend's scoring worker | `SessionWindow.to_dict()` |
| `sessions/{session_id}/alerts.jsonl` | camera AI, one line per alert | web admin live view, dashboard, reports | `{"id": ..., **AlertEvent.to_dict()}`; `id` is random, set once |
| `sessions/{session_id}/handled_alerts.json` | web admin | web admin | `{alert_id: {status, handled_by, handled_at}}` |
| `sessions/{session_id}/shadow_*.json` | the web backend's scoring worker | developers | Scores the backend computes from the windows (package A) |

Times are ISO 8601 UTC strings.

## Usage

`src/main.py` wires everything (`edge_runtime`, `web_sessions`); see `docs/edge_node.md`. In short:

```python
from src.sync import DATA_DIR, LocalSink, camera_session, session_states

sink = LocalSink(DATA_DIR, camera_id)
states = session_states(camera_session(DATA_DIR, camera_id))  # {session_id: state} for EdgeRuntime
sink.set_result(result)  # SessionResult
sink.set_evaluations(evaluations)  # SeatEvaluation per seat
sink.add_window(window)  # SessionWindow
sink.add_alert(alert)  # AlertEvent
sink.set_heartbeat(heartbeat)  # EdgeHeartbeat
```

## Behaviour

| Concern | Behaviour |
|---|---|
| Write rate | Results and one window every 10 s of monitored time, evaluations every 5 minutes and at the end, the heartbeat at least every 10 s. A local write takes a few milliseconds, so the sink writes at once inside the frame loop: no queue, no background thread. |
| Overwritten files | Written to a temporary file in the same folder, then moved over the old one (`os.replace`), so a reader sees the old or the new version, never half a file. On Windows the move fails while the other process has the file open, and the writer retries every 10 ms for up to half a second. |
| Appended files | One edge node writes each session's `windows.jsonl` and `alerts.jsonl`, a line at a time. The web reader skips a last line that is still being written. |
| Disk errors | A failed write is logged with the file name and error type only, counted in `dropped` and skipped. The edge node keeps running. |
| Session changes | The web admin sets `status` in `camera_sessions/{camera_id}.json`. `EdgeRuntime.run()` reads the file again every second (`SESSION_POLL_SEC`) and maps `status` with `WEB_STATUS_TO_STATE` (`running` → `active`, `completed` → `ended`, the older `live`/`ended` the same way). A file it cannot read keeps the last known state. A new session for the camera replaces the old one: an unfinished old session is closed as `incomplete`. |
| Retention | `prune_sessions` deletes the folder of every session with no file newer than `privacy.retention_days`. `python -m src.main` runs it at start and then daily. |
| Logging | File names, error types and counters only. Never file contents. |

Limits:

- Changes made to Firestore outside the web backend, for example a session status edited in the Firebase console or by the app, do not reach camera AI. The app must start and end sessions through the web API.
- Two processes of the web side can change the same camera's session file: the web backend and the report job, when it closes a forgotten session. The backend serialises its own writes with a lock; a clash with the job at the same instant leaves whichever write came last.

## Tests

`tests/test_local_store.py` covers the sink (allowlist, atomic overwrite with the Windows retry, merged evaluations, disk errors, pruning) and the web files. `tests/test_edge_runtime.py` runs `EdgeRuntime` on a temporary folder. `backend/tests/test_edge_contract.py` runs the web backend and a real `EdgeRuntime`, wired like `src/main.py`, on the same temporary folder.
