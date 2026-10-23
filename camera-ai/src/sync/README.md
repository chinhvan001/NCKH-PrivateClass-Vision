# Module `sync/`

The edge node's Firestore gateway, on the team's Firestore schema. It uploads the pipeline's anonymized output (live seat states for UC07, per-seat evaluations for UC03/UC11, alerts for UC09), keeps the node's heartbeat current, and listens to its class's sessions. It accepts only the allowlisted schemas built in `privacy/`, plus `EdgeHeartbeat`, which carries device status only.

Do not enable it in production until the *Blocker* items in `docs/cloud_data_compliance_checklist.md` §3 are closed.

## Usage

`src/main.py` wires everything; see `docs/edge_node.md`. In short:

```python
from src.sync import FirestoreSink, firestore_client_from_env

sink = FirestoreSink(firestore_client_from_env(), class_id, camera_id, retention_days=365)
sink.start()  # background flush thread
watch = sink.watch_sessions(runtime.on_sessions)  # {session_id: state} on every change
...
sink.set_result(result)  # SessionResult, overwrites session_results/{session_id}
sink.set_evaluations(evaluations)  # SeatEvaluation per seat
sink.add_alert(alert)  # AlertEvent
sink.set_heartbeat(heartbeat)  # EdgeHeartbeat
...
watch.unsubscribe()
sink.close()  # stops the thread and flushes one last time
```

One sink lives for the whole process, not per session, so data from a session that ended during an outage is still uploaded once the network returns. All `add_*`/`set_*` methods only update queues in RAM, so they are safe to call inside the frame loop.

## Credentials

The edge node signs in with a Firebase service account key:

1. Store the key file outside the repository, readable only by the account that runs the pipeline.
2. Set `GOOGLE_APPLICATION_CREDENTIALS` to its path, either in the environment or in `.env`.

`firestore_client_from_env()` fails fast if the variable is unset or the file does not exist. The class layout reader (`config/class_layout.py`) uses the same client. Key files named like `*firebase-adminsdk*.json` or `*service-account*.json` are git-ignored.

The Admin SDK bypasses Firestore Security Rules. See `docs/firestore_security_review.md` for what that means for the edge key, and for the custom-token option that replaces it.

## Firestore layout

Sessions, classes and seats belong to the web admin and the app (`docs/web_admin_integration.md`).

| Path | Edge node | Content |
|---|---|---|
| `sessions/{session_id}` | listens to those with its `class_id` | `status`, written by the web admin or app (`docs/edge_node.md`) |
| `classes2/{class_id}` | reads `row_count`, `column_count` at session start | `config/class_layout.py`; a field projection, so `seat_map` (seat → student) is never read |
| `session_results/{session_id}` | reads once at session start, then overwrites | `SessionResult.to_dict()` + `expire_at` |
| `session_evaluations/{session_id}_{seat_id}` | overwrites | `SeatEvaluation.to_dict()` + `expire_at` |
| `sessions/{session_id}/alerts/{doc_id}` | creates | `AlertEvent.to_dict()` + `expire_at` |
| `edge_nodes/{camera_id}` | overwrites | `EdgeHeartbeat.to_dict()` |

`doc_id` is a random UUID assigned when the alert is queued. Documents contain exactly the schema's fields; the sink adds only `expire_at` (queue time + `retention_days`) to session documents, for a Firestore TTL policy.

## Delivery behaviour

| Concern | Behaviour | Default |
|---|---|---|
| Upload rate | The runtime writes `session_results` every 10 s of monitored time and `session_evaluations` every 5 minutes and at session end. Per-seat records never leave the edge node. For 40 seats and a 45-minute session this is about 950 writes including heartbeats. | |
| Overwritten documents | Results, evaluations and the heartbeat keep only their latest version per path in RAM. A newer version replaces one that has not been sent, so an outage never piles up stale snapshots. | |
| Batching | Up to `batch_size` writes per `WriteBatch` commit: alerts first, then overwritten documents. | 500 (Firestore maximum) |
| Flush timing | Every `flush_interval_sec`. A new alert or an end-of-session result wakes the thread at once, to meet QA01 (alerts in under 1 s). | 2 s |
| Retry | A failed batch goes back to the queue. Retries back off exponentially (doubling per failure, with jitter) up to `max_backoff_sec`. Each attempt times out after 10 s; the SDK's built-in retry is turned off so the sink is the only retry policy. | 60 s cap |
| Duplicates | Alert IDs are fixed when an alert is queued, and the other documents have deterministic paths. Retrying after an ambiguous failure (the server committed but the client timed out) overwrites the same documents instead of duplicating them. | |
| Rejected data | On HTTP 400 or a client-side encoding error, the batch is dropped and logged, so one bad batch cannot block the queue forever. | |
| Offline queue (UC02 alternate flow) | Alerts: at most `max_queue`, in RAM; when full the oldest is dropped and counted in `dropped`. Overwritten documents: one per path. | 20,000 alerts |
| Session listener | A Firestore watch on `sessions` where `class_id` is this node's class. It maps `status` to the runtime's states (`running` → `active`, `completed` → `ended`, and the older `live`/`ended` the same way; anything else unchanged). It dies when the network drops; the runtime subscribes again once flushes succeed (`docs/edge_node.md`, Known limits). | |
| Logging | Only the error type and queue counters. Never document contents or server error messages, which may echo them. | |

Limits:

- The queue lives in RAM only, so anything not uploaded when the process exits is lost. Persisting it would put classroom data on the edge disk, which then needs encryption (compliance checklist §3.5).
- `close()` flushes once more. If the network is down at that moment, it logs how many items were lost.
- `result_exists()` reads synchronously, one attempt with a 10 s timeout. If the read fails it answers "no", so a restart during an outage is not detected as an interruption.

## Tests

`tests/fake_firestore.py` provides `FakeFirestore`, an in-memory replacement for the client, so tests need no credentials, network or `firebase_admin`. It rejects what real Firestore rejects (more than 500 writes per batch, malformed paths, values Firestore cannot encode), applies field projections like Firestore (`get(field_paths=...)`, `select()`), logs what a client read in `reads`, calls `on_snapshot` listeners synchronously on every write, and injects commit failures with `fail_next(error, after_write=...)`. See `tests/test_firestore_sink.py`, `tests/test_class_layout.py` and `tests/test_edge_runtime.py`.
