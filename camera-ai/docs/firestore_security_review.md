# Firestore Access Review: Edge Node

Prepared 2026-10-04 for the review with the Firebase owner, updated 2026-10-07 for the web admin's session contract. It covers how the camera-ai edge node authenticates to Firestore, and the Security Rules draft for the paths it uses (`config/firestore.rules`). Decisions from the review update `cloud_data_compliance_checklist.md` §3.7.

## 1. Current setup

- The edge node uses the Firebase Admin SDK with a service account key. `sync.firestore_client_from_env()` reads the key path from `GOOGLE_APPLICATION_CREDENTIALS` and fails fast if it is unset or the file is missing. The seat-grid reader uses the same function.
- The key never enters the repository or the local pipeline config: key file names are git-ignored, and `config/local_schema.py` rejects unknown keys. The sink never logs document contents.
- Paths the edge node uses:

| Path | Edge access | Data |
|---|---|---|
| `classrooms/{c}/camera_configs/{cam}` | read | Seat grid. No student data. |
| `classrooms/{c}/edge_nodes/{cam}` | overwrite | `EdgeHeartbeat`. Device status only. |
| `sessions/{s}` | listen (query `classroom_id == c`) | Session `status`, written by the web admin. The document also holds `class_id`, `teacher_uid` and the schedule. |
| `sessions/{s}/engagement/{id}` | create | `AnonymizedEngagementRecord` |
| `sessions/{s}/alerts/{id}` | create | `AlertEvent` |
| `sessions/{s}/summaries/{cam}` | read once, overwrite | `SessionSummary` |

Since 2026-10-07 the session documents are the web admin's top-level `sessions` collection (`docs/web_admin_integration.md`), which lives in the same database as the web admin's `users` and `admins` collections.

## 2. Main finding: Security Rules do not restrict the edge node

Security Rules apply only to requests from client SDKs (Firebase Auth users). Server libraries, the Admin SDK included, bypass them, and only IAM controls their access. IAM cannot be limited to a document path: `roles/datastore.user`, the narrowest predefined role that can write, can read and write the whole database.

So anyone who copies the key from a classroom edge box can read and write every classroom's data, including the seat→student mapping, which is what turns pseudonymous seat IDs back into students (checklist §3.2). The checklist's current wording, "the edge service account may only write records and alerts for its own classroom", cannot be met with the Admin SDK alone.

| Option | What changes | Result | Cost |
|---|---|---|---|
| A. Isolate by database or project | Keep the Admin SDK. Everything the edge reads or writes, including the session documents it listens to, lives in a Firestore database or Firebase project that holds no student data, and the edge account is granted access only there. | A stolen key exposes telemetry of all classrooms, but not the mapping or user accounts. | Low. Confirm that per-database IAM conditions are available, or use a separate project. |
| B. Edge signs in as a Firebase Auth user | A trusted service mints a custom token with claims `{role: "edge", classroom_id}`. The edge exchanges it for an ID token and writes through the REST API, so Rules apply. | Rules can allow each node only `create` under its own classroom, with a field allowlist. | Medium. Token minting and refresh, plus a REST client behind the sink's `client` interface. |
| C. Edge writes through the backend | Follows architecture §5.1 (edge → Flask backend → Firebase). Only the backend holds a service account. | The edge holds a revocable, classroom-scoped API token. | High. The backend does not exist yet. |

Recommendation: A now, so no edge key can reach student data, and B or C before a multi-classroom pilot. Because the edge node now listens to the web admin's `sessions` in the main database, A also needs the web backend to copy each session's `classroom_id` and `status` into the isolated database, and the edge node to write its output there, where the web backend reads it. Without that copy, A is not possible and B or C is needed sooner. Whatever is chosen:

- Give each edge node its own service account, or at least its own key, so a lost device can be revoked alone.
- Never grant Owner, Editor or `roles/firebase.admin`. Consider a custom role with only `datastore.entities.get`, `list`, `create` and `update` instead of `roles/datastore.user`; it drops `delete`. (`list` is needed for the session listener.) Verify the exact permission set with a test write and a test listen.
- Rotate keys on a schedule and disable them when a node is retired.
- Restrict the key file to the service account user (NTFS ACL or `chmod 600`) and enable full-disk encryption on edge nodes (checklist §3.5).

## 3. Rules draft walkthrough

`config/firestore.rules` covers only the paths above and must be merged into the project's rules. It assumes a custom claim `role` and a `teacher_uids` list on each classroom document; confirm or adapt both. The web admin reads and writes through its Flask backend, which uses the Admin SDK, so these Rules bind only the Flutter app and any browser code that reads Firestore directly.

| Path | Admin | Teacher of the classroom | Parent | Edge (Admin SDK) |
|---|---|---|---|---|
| `classrooms/{c}/camera_configs/{cam}` | read, write (field allowlist), delete | read, write (field allowlist) | none | read (bypasses Rules) |
| `classrooms/{c}/edge_nodes/{cam}` | read | read | none | overwrite (bypasses Rules) |
| `sessions/{s}` | read; create, edit and delete through the web backend | read; change only `status`, from `scheduled` to `live` or from `live` to `completed` | none | listen (bypasses Rules) |
| `sessions/{s}/engagement/{id}` | read | read | none | create (bypasses Rules) |
| `sessions/{s}/alerts/{id}` | read | read; update `status` to `acknowledged` or `dismissed` only | none | create (bypasses Rules) |
| `sessions/{s}/summaries/{cam}` | read | read | none | read, overwrite (bypasses Rules) |

"Teacher of the classroom" for a session means the classroom in its `classroom_id`. Client queries on `sessions` must filter on `classroom_id` so the rule can be checked.

Parents get no per-seat data. Their view of their own child (UC03) should come from aggregates, which are not designed yet. Test the rules against the Firestore emulator with `@firebase/rules-unit-testing` before deploying; this repository's CI does not run them.

## 4. Decisions needed

1. Option A, B or C, and by when.
2. Role model: custom claims or user documents? Where is a teacher's list of classrooms stored?
3. Where the seat→student mapping lives, and its rules: teacher and admin only, parents only through their linked child.
4. Retention (checklist §3.6). A TTL policy needs a timestamp field, and these documents deliberately carry no wall-clock time. One option is a TTL on the session document plus a scheduled function that deletes its subcollections.
5. Firestore location, and whether storing students' pseudonymous data outside Vietnam triggers cross-border transfer duties under Vietnamese personal-data rules. Confirm with the mentor.
6. Who owns key rotation and revocation.
