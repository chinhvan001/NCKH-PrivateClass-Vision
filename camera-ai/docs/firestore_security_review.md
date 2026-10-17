# Firestore Access Review: Edge Node

Prepared 2026-10-04 for the review with the Firebase owner, updated 2026-10-17 for the team's Firestore schema. It covers how the camera-ai edge node authenticates to Firestore, and the Security Rules draft for the paths camera-ai uses (`config/firestore.rules`). Decisions from the review update `cloud_data_compliance_checklist.md` §3.7.

## 1. Current setup

- The edge node uses the Firebase Admin SDK with a service account key. `sync.firestore_client_from_env()` reads the key path from `GOOGLE_APPLICATION_CREDENTIALS` and fails fast if it is unset or the file is missing. The class seat plan reader (`config/class_layout.py`) uses the same client.
- The key never enters the repository or the local pipeline config: key file names are git-ignored, and `config/local_schema.py` rejects unknown keys. The sink never logs document contents.
- Paths the edge node uses:

| Path | Edge access | Data |
|---|---|---|
| `sessions/{s}` | listen (query `class_id == c`) | Session `status`, written by the web admin or app. The document also holds `teacher_id`, `subject`, `started_at`, `ended_at`. |
| `classes/{c}` | read `row_count`, `column_count` | Class document. |
| `classes/{c}/seats/{seat_id}` | read `row`, `column` | Seat documents also hold `student_id`; the edge node asks for the two fields only. |
| `session_results/{s}` | read once, overwrite | `SessionResult` |
| `session_evaluations/{s}_{seat}` | overwrite | `SeatEvaluation` |
| `sessions/{s}/alerts/{id}` | create | `AlertEvent` |
| `edge_nodes/{camera_id}` | overwrite | `EdgeHeartbeat`. Device status only. |

These paths live in the same database as the team's personal data: `students` (full name, birthday, gender), `parents` (name, email), `teachers` (email, phone) and `admins`.

## 2. Main finding: Security Rules do not restrict the edge node

Security Rules apply only to requests from client SDKs (Firebase Auth users). Server libraries, the Admin SDK included, bypass them, and only IAM controls their access. IAM cannot be limited to a document path: `roles/datastore.user`, the narrowest predefined role that can write, can read and write the whole database.

So anyone who copies the key from a classroom edge box can read and write the whole database: students' names and birthdays, parents' emails, and the seat→student mapping that turns pseudonymous seat IDs back into students (checklist §3.2).

| Option | What changes | Result | Cost |
|---|---|---|---|
| A. Isolate by database or project | Keep the Admin SDK. Everything the edge reads or writes lives in a Firestore database or Firebase project that holds no personal data, and the edge account is granted access only there. | A stolen key exposes the session data of all classes, but no personal data. | High with the team's schema: the web backend would have to mirror every session and seat plan into the second database and read the edge output from there. |
| B. Edge signs in as a Firebase Auth user | An admin mints a custom token per edge node with claims `{role: "edge", class_id, camera_id}`. The edge node exchanges it once for an ID token and a refresh token kept on the device, and writes through the Firestore REST API, so Rules apply. | Rules allow each node only its own class's sessions and seats and its own outputs, with field allowlists. A lost device is revoked in Firebase Auth. | Medium: a one-off token script for admins, and a REST client behind the sink's `client` interface. |
| C. Edge writes through the backend | Follows architecture §5.1 (edge → Flask backend → Firebase). Only the backend holds a service account. | The edge holds a revocable, class-scoped API token. | High: new backend endpoints for every edge read and write. |

Recommendation (changed on 2026-10-17 from A): **B**. With personal data and session data in one database, A needs a mirror that the team does not have, while B needs nothing from the web side. `config/firestore.rules` already holds the edge rules for B, tested on the emulator. Until B ships, run the Admin SDK only against a test project without real student data. Whatever is chosen:

- Give each edge node its own identity (token or key), so a lost device can be revoked alone.
- Never grant Owner, Editor or `roles/firebase.admin` to an edge identity.
- Rotate credentials on a schedule and revoke them when a node is retired.
- Restrict the credential file to the account that runs the pipeline (NTFS ACL or `chmod 600`) and enable full-disk encryption on edge nodes (checklist §3.5).

## 3. Rules draft walkthrough

`config/firestore.rules` covers only the paths camera-ai touches and must be merged into the project's rules. Roles come from documents keyed by Firebase Auth UID: a user is an admin, teacher or parent when `admins/{uid}`, `teachers/{uid}` or `parents/{uid}` exists. The web admin reads and writes through its Flask backend, which uses the Admin SDK, so these Rules bind the Flutter app, any browser code that reads Firestore directly, and the edge node once it uses option B.

| Path | Admin | Teacher | Parent | Edge node (option B claims) |
|---|---|---|---|---|
| `sessions/{s}` | read | read own (`teacher_id`); change only `status`, `started_at`, `ended_at`: `scheduled` → `running` or `cancelled`, `running` → `paused` or `ended`, `paused` → `running` or `ended` | none | read own class (`class_id`) |
| `classes/{c}` | read | read | none | read own class |
| `classes/{c}/seats/{seat}` | read, write (field allowlist), delete | read; write and delete only as the homeroom teacher (`classes/{c}.teacher_id`), field allowlist | none | read own class |
| `session_results/{s}` | read | read for own sessions | none | write for own class's sessions: field allowlist, own `camera_id` |
| `session_evaluations/{e}` | read | read for own sessions | none | write for own class's sessions: ID `{session_id}_{seat_id}`, field allowlist |
| `sessions/{s}/alerts/{id}` | read | read for own sessions; set `status` to `acknowledged` or `dismissed` only | none | create for own class's sessions: field and type allowlists |
| `edge_nodes/{camera_id}` | read | read | none | write own `camera_id` with own `class_id`, field allowlist |
| `students/{sid}/reports/{r}` | read | none | read own child (`students/{sid}.parent_id`) | none |

Client queries must carry the filter a rule depends on: teachers query `sessions` on `teacher_id` and `session_evaluations` on `session_id`; the edge node queries `sessions` on `class_id`.

Parents get no per-seat data; their view of their own child (UC03) comes from `students/{sid}/reports`, written by a report job with the Admin SDK.

`rules-tests/` checks every cell of this table, plus the query filters and a write by another class's edge node, on the Firestore emulator with `@firebase/rules-unit-testing`. CI runs it on every change under `camera-ai/`; locally run `npm ci` and `npm test` in that folder (Node 24 and Java 21 required). The merged project rules need the same tests before they are deployed.

## 4. Decisions needed

1. Confirm option B, and who mints and revokes edge tokens.
2. Who may read seat documents. The draft lets any teacher read them, so subject teachers can map the live seat view to students. Limiting it to a class's own teachers needs a list on the class (for example `teacher_ids`) that Rules can check.
3. Parent reports: confirm that a backend job writes `students/{sid}/reports`, and what a report contains.
4. Retention (checklist §3.6): the period, and enabling Firestore TTL on `expire_at` for `session_results`, `session_evaluations` and the `alerts` collection group.
5. Firestore location, and whether storing students' pseudonymous data outside Vietnam triggers cross-border transfer duties under Vietnamese personal-data rules. Confirm with the mentor.
6. Who owns credential rotation and revocation.
