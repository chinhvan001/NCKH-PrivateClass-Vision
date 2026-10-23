# Team Notes: Moving camera-ai to the Firestore Schema

Written 2026-10-17 for the next team meeting (T0). camera-ai now follows the team's Firestore schema diagram. Where the diagram says nothing, or where following it literally would leak data, camera-ai made a choice and wrote it down here; each one needs the team's confirmation. The contract itself is in `docs/web_admin_integration.md`, the edge behaviour in `docs/edge_node.md`, and the privacy status in `docs/cloud_data_compliance_checklist.md`.

Updated 2026-10-23: the web admin (branch `Web`) is merged into `camera-ai` and both sides now talk through the contract. Where the web admin had already built something differently (`classes2`, `seat_map`, `S01` seat IDs, `completed`), camera-ai follows it; §2 marks what that settled.

## 1. What camera-ai does now

- **Sessions.** The edge node listens to `sessions` where `class_id` is its class and reacts to `status`: `running` opens the camera, `paused` closes it, `completed` finishes the session, `cancelled` or a deleted document stops it as incomplete. It still accepts the older `live` and `ended`.
- **Seat plan.** At the start of each session it reads only `row_count`/`column_count` from `classes2/{class_id}` and numbers the seats `S01`, `S02`, ... row by row, the keys the web admin writes in `seat_map`. It never reads `seat_map`.
- **Seat positions in the image.** The installer enters the image position of the four corner seats in the edge node's local config; every other seat is placed by a perspective transform. No camera image is ever needed on the web side.
- **Output.**
  - `session_results/{session_id}`: live state of every seat, overwritten every 10 s of monitoring.
  - `session_evaluations/{session_id}_{seat_id}`: per-seat totals, overwritten every 5 minutes and at the end.
  - `sessions/{session_id}/alerts/{id}`: head drop, back turn and side conversation alerts.
  - `edge_nodes/{camera_id}`: heartbeat every 10 s.
- **Volume.** About 950 writes for a 40-seat class and a 45-minute session, against about 10,800 with the previous per-seat records.
- **Retention.** Every session document carries `expire_at`, so a Firestore TTL policy can delete it.
- **Security Rules.** `config/firestore.rules` is rewritten for the schema and tested on the emulator in CI (`rules-tests/`).
- **Web admin side (2026-10-23).** Start, pause, resume and end from the timetable, with the pre-start checks of UC04 step 3; the seating frozen into `session_rosters/{s}` at the start; a live view of seats and alerts; reports and the dashboard from `session_evaluations`, with interrupted sessions marked; a parent report job; session deletion with all its edge documents; a camera page fed by the edge heartbeats, with no RTSP URL stored; admin sign-in required on every monitoring, report and student endpoint. Tested together with the real edge runtime (`backend/tests/test_edge_contract.py`).

## 2. Choices to confirm at the meeting

| # | Topic | What camera-ai did | Why | To confirm |
|---|---|---|---|---|
| 1 | Alerts (UC09) | `sessions/{session_id}/alerts/{id}`: `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec`; the web admin or teacher adds `status` (`acknowledged`, `dismissed`), `handled_by`, `handled_at` | The diagram has no alert collection, and UC09 needs one | Path and fields; the web admin uses them |
| 2 | Edge heartbeat (UC04, UC10) | `edge_nodes/{camera_id}`: `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` | The diagram has no device status, and the pre-start check needs one | Path and fields |
| 3 | Session status values | Settled by the web admin: `scheduled` → `running` ↔ `paused` → `completed`; `cancelled` before the start | The diagram shows only `running` | Who sets them in the app |
| 4 | Metrics | `concentration`: score of the last 60 s. `avg_concentration`: score since the start. `distraction`: number of alerts. `interaction`: number of side-conversation alerts. Seat `status`: `focused`, `drowsy`, `distracted`, `away` | The diagram names the fields without defining them | Especially `interaction`: if it should mean participation (raising hands), the edge cannot measure it yet |
| 5 | `session_results` | One document per session (ID = session ID), overwritten every 10 s, plus a new `monitoring_status` field (`running`, `completed`, `incomplete`) | UC04 needs a way to mark a session whose data is partial | The overwrite (no history inside a session) and the extra field |
| 6 | `session_evaluations` | Collection name `session_evaluations`, ID `{session_id}_{seat_id}`, overwritten every 5 minutes and at the end, plus a new `observed_sec` field | Reports must ignore seats where someone only walked past, and weight class averages | Name, ID and the extra field |
| 7 | Seat positions | Four corner seats in the edge node's local config; seats have only `row` and `column` in Firestore | The diagram has no image coordinates, and a web calibration screen would need camera images on the web side | That calibration stays on the edge node |
| 8 | Seat→student mapping | Kept as the web admin built it: `seat_map` on `classes2/{c}`, readable by admins and teachers only (never parents). The edge node reads only the counts. Each session's seating is copied to `session_rosters/{s}` at the start | Rules cannot hide one field of a document, so access to the whole class document has to stay narrow; reports need the seating of that lesson, not today's | Confirmed by the web implementation; seat documents (proposed 2026-10-17) dropped |
| 9 | One camera per class | The edge node is configured with one `class_id` and one `camera_id` | THPT classes keep their room | Classes that change rooms (labs) would need `camera_id` on the session |
| 10 | Timestamps | `captured_at` and `expire_at` are UTC times from the edge clock (keep NTP on); alert times stay as seconds since the session start | The diagram uses timestamps; the session already has `started_at` | That alerts keep `start_sec` |
| 11 | Parent view (UC03) | Parents read only `students2/{sid}/reports/{s}`, written by `backend/jobs/parent_reports.py` after each session: class, subject, date and times, `avg_concentration`, `level`, `observed_min`, alert counts per type, `partial` | Parents must not see other children's seats | The report fields, and who sets `students2.parent_id` |
| 12 | Who reads `classes2` | The Rules draft lets any teacher read every class (for the live view) and only the homeroom teacher or an admin change `seat_map` | Subject teachers need names on the live seat map | Or a `teacher_ids` list on the class |
| 13 | Diagram fixes | The second "Teachers" box (bottom left) is a copy of "Parents". Seat IDs are `S01`, `S02`, ... as the web admin writes them, not `S01-ClassID` | | Update the diagram |
| 14 | `session_rosters/{s}` | New: `class_id`, `seats` (seat → student ID), `created_at`, written by the web admin when a session first starts; read by admins and the session's teacher | Reports and the parent job must map seats to the students of that lesson | The collection, and that the app freezes it too if it starts sessions itself |

## 3. What each part of the team needs to do

**Web admin (`backend/`, `frontend/`).** Merged into `camera-ai` on 2026-10-23, and the monitoring side is built (§1). The web team should review these changes before they go back into `Web`. Still open (details in `docs/web_admin_integration.md`, "Still open"):

- Writing `students2/{sid}.parent_id` so parents can see their children's reports.
- Scheduling `python -m jobs.parent_reports` on the school server (every 10 minutes).
- Taking the Firebase Web API key out of the code, and fixing the frontend's existing eslint errors.

**Flutter app (`main`).**

- Read `sessions` instead of `monitoring_sessions`, with the statuses above.
- Start and end sessions through the web API (pre-start checks, roster), or repeat both in the app.
- The seating screen writes `classes2/{c}.seat_map` instead of `row`/`column` on student documents.
- The teacher live view reads `session_results` and acknowledges alerts (`status`, `handled_by`, `handled_at`).
- Parents find their children with `students2` where `parent_id` is their UID, and read `students2/{sid}/reports`.

**Firebase owner.**

- Merge `camera-ai/config/firestore.rules` into the project's rules and deploy them with the same tests.
- Enable TTL on `expire_at` for `session_results`, `session_evaluations` and the `alerts` collection group once the retention period is agreed.
- Mint one custom token per edge node (option B in `docs/firestore_security_review.md`).
- Until then, give edge nodes access only to a test project without real student data.

**Questions for the mentor.**

- The retention period.
- Parents' consent for storing minors' data, and whether `birthday` and `gender` are needed (checklist §3.13).
- Firestore location and cross-border transfer.
- The QA02 wording in the architecture document (checklist §3.9).

**Everyone.** Re-clone or reset after the `camera-ai` history rewrite (§5), and never push old `camera-ai` commits back.

## 4. camera-ai work that follows

- Edge sign-in with custom tokens (option B), replacing the Admin SDK key.
- A small helper that turns the four corner seats into a seat file for the demo, so installers can check the calibration on the anonymized preview.
- End-to-end test with the web admin and app on a real test Firebase project (the web side already runs against the edge runtime on a fake database in `backend/tests/test_edge_contract.py`).
- FCM push for alerts (UC09), after the alert path is confirmed.

## 5. Git history rewrite of `camera-ai`

- **What.** `camera-ai/simulated_data/test2.mp4`, real CCTV footage with identifiable faces, is removed from the branch history. Only the 22 commits from `4f948e64` (2026-09-27) onward are rewritten; their file contents are unchanged except for the removed video, and `main` and every other branch are untouched.
- **Status.** Force-pushed on 2026-10-17 (`0749529a` → `1bbd73eb`); CI passed on the new tip. No branch on GitHub contains `4f948e64` any more, and the repository has no forks.
- **Still exposed: act now.** The repository is public, and the closed pull request #3 (`camera-ai` → `main`) still has `4f948e64` as its head, so the video can still be downloaded from GitHub. The open pull request #4 also lists the old commits in its "force-pushed" event. The repository owner (`chinhvan001`):
  1. Makes the repository private: Settings → General → Danger Zone → Change repository visibility.
  2. Asks GitHub Support to remove sensitive data: repository `chinhvan001/NCKH-PrivateClass-Vision`, affected pull requests #3 and #4, first affected commit `4f948e64`. Ask them to drop the pull request refs and purge cached views and unreachable commits.
- **Everyone** who has the old branch either re-clones, or runs `git fetch origin`, `git checkout camera-ai` and `git reset --hard origin/camera-ai` (this discards uncommitted changes on that branch). Nobody may merge or push the old `camera-ai` commits, or the video comes back.
- **Optionally, clean the local copy:** `git update-ref -d refs/original/refs/heads/camera-ai`, then `git reflog expire --expire=now --all` and `git gc --prune=now`.
