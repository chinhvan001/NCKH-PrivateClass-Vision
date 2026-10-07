# Module `sync/`

The edge node's Firestore gateway. It uploads the pipeline's anonymized output (engagement records for UC02, alerts for UC09, end-of-session summaries for UC03/UC11), keeps the node's heartbeat current, and listens to the classroom's sessions. It accepts only the allowlisted schemas built in `privacy/`, plus `EdgeHeartbeat`, which carries device status only.

Do not enable it in production until the *Blocker* items in `docs/cloud_data_compliance_checklist.md` §3 are closed.

## Usage

`src/main.py` wires everything; see `docs/edge_node.md`. In short:

```python
from src.sync import FirestoreSink, firestore_client_from_env

sink = FirestoreSink(firestore_client_from_env(), classroom_id, camera_id)
sink.start()  # background flush thread
watch = sink.watch_sessions(runtime.on_sessions)  # {session_id: state} on every change
...
sink.add_record(session_id, record)  # AnonymizedEngagementRecord
sink.add_alert(alert)  # AlertEvent
sink.add_summary(summary)  # SessionSummary
sink.set_heartbeat(heartbeat)  # EdgeHeartbeat
...
watch.unsubscribe()
sink.close()  # stops the thread and flushes one last time
```

One sink lives for the whole process, not per session, so data from a session that ended during an outage is still uploaded once the network returns. The `add_*` and `set_heartbeat` methods only update queues in RAM, so they are safe to call inside the frame loop.

## Credentials

The edge node signs in with a Firebase service account key:

1. Store the key file outside the repository, readable only by the account that runs the pipeline.
2. Set `GOOGLE_APPLICATION_CREDENTIALS` to its path, either in the environment or in `.env`.

`firestore_client_from_env()` fails fast if the variable is unset or the file does not exist. The seat-grid reader (`config/remote_seat_grid.py`) uses the same function. Key files named like `*firebase-adminsdk*.json` or `*service-account*.json` are git-ignored.

The Admin SDK bypasses Firestore Security Rules. See `docs/firestore_security_review.md` for what that means for the edge key.

## Firestore layout

Session documents belong to the web admin (`docs/web_admin_integration.md`). Everything else the edge node writes hangs under them, except the heartbeat, which describes the device:

| Path | Edge node | Content |
|---|---|---|
| `classrooms/{classroom_id}/camera_configs/{camera_id}` | reads | Seat grid, see `config/firestore_seat_grid.md` |
| `classrooms/{classroom_id}/edge_nodes/{camera_id}` | overwrites | `EdgeHeartbeat.to_dict()` |
| `sessions/{session_id}` | listens to those with its `classroom_id` | `status`, written by the web admin (`docs/edge_node.md`) |
| `sessions/{session_id}/engagement/{doc_id}` | creates | `AnonymizedEngagementRecord.to_dict()` |
| `sessions/{session_id}/alerts/{doc_id}` | creates | `AlertEvent.to_dict()` |
| `sessions/{session_id}/summaries/{camera_id}` | reads once, overwrites | `SessionSummary.to_dict()` |

`doc_id` is a random UUID assigned when the item is queued. Documents contain exactly the schema's fields; the sink adds nothing.

## Delivery behaviour

| Concern | Behaviour | Default |
|---|---|---|
| Upload rate | The pipeline emits one record per seat per frame. The sink keeps one per seat every `record_interval_sec`, plus one whenever `posture_state` changes, and starts afresh for each session. Scores and event counters are cumulative, so the skipped records lose nothing. | 10 s |
| Batching | Up to `batch_size` writes per `WriteBatch` commit: heartbeat first, then alerts and summaries, then records. | 500 (Firestore maximum) |
| Flush timing | Every `flush_interval_sec`. A new alert or summary wakes the thread at once, to meet QA01 (alerts in under 1 s). | 2 s |
| Retry | A failed batch goes back to the front of the queue. Retries back off exponentially (doubling per failure, with jitter) up to `max_backoff_sec`. Each attempt times out after 10 s; the SDK's built-in retry is turned off so the sink is the only retry policy. | 60 s cap |
| Duplicates | Document IDs are fixed when an item is queued. Retrying after an ambiguous failure (the server committed but the client timed out) overwrites the same documents instead of duplicating them. | |
| Rejected data | On HTTP 400 or a client-side encoding error, the batch is dropped and logged, so one bad batch cannot block the queue forever. | |
| Offline queue (UC02 alternate flow) | At most `max_queue` items, in RAM. When full, the oldest record is dropped first; alerts and summaries are dropped only when no record is left (QA03). `dropped` counts every dropped item. | 20,000 (about 80 minutes for 40 seats) |
| Heartbeat | Not queued: only the latest one waits for the next flush, so an outage never piles up stale heartbeats. | |
| Session listener | A Firestore watch on `sessions` where `classroom_id` is this node's classroom. It maps the web `status` to the runtime's states (`live` → `active`, `completed` → `ended`, anything else unchanged). It dies when the network drops; the runtime subscribes again once flushes succeed (`docs/edge_node.md`, Known limits). | |
| Logging | Only the error type and queue counters. Never document contents or server error messages, which may echo them. | |

Limits:

- The queue lives in RAM only, so anything not uploaded when the process exits is lost. Persisting it would put classroom data on the edge disk, which then needs encryption (compliance checklist §3.5).
- `close()` flushes once more. If the network is down at that moment, it logs how many items were lost.
- `summary_exists()` reads synchronously, one attempt with a 10 s timeout. If the read fails it answers "no", so a restart during an outage is not detected as an interruption.

## Tests

`tests/fake_firestore.py` provides `FakeFirestore`, an in-memory replacement for the client, so tests need no credentials, network or `firebase_admin`. It rejects what real Firestore rejects (more than 500 writes per batch, malformed document or collection paths, values Firestore cannot encode), calls `on_snapshot` listeners synchronously on every write, and injects commit failures with `fail_next(error, after_write=...)`. See `tests/test_firestore_sink.py` and `tests/test_edge_runtime.py`.
