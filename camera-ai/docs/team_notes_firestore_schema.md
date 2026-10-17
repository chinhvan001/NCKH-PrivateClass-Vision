# Team Notes: Moving camera-ai to the Firestore Schema

Written 2026-10-17 for the next team meeting (T0). camera-ai now follows the team's Firestore schema diagram. Where the diagram says nothing, or where following it literally would leak data, camera-ai made a choice and wrote it down here; each one needs the team's confirmation. The contract itself is in `docs/web_admin_integration.md`, the edge behaviour in `docs/edge_node.md`, and the privacy status in `docs/cloud_data_compliance_checklist.md`.

## 1. What camera-ai does now

- **Sessions.** The edge node listens to `sessions` where `class_id` is its class and reacts to `status`: `running` opens the camera, `paused` closes it, `ended` finishes the session, `cancelled` or a deleted document stops it as incomplete. It also accepts the `Web` branch's current `live` and `completed` until the web switches.
- **Seat plan.** At the start of each session it reads `row_count`/`column_count` from `classes/{class_id}` and `row`/`column` from `classes/{class_id}/seats`, never `student_id`. While a class has no seat documents it numbers seats `S1`..`Sn` row by row, matching the `Web` branch's `seat_assignments` keys.
- **Seat positions in the image.** The installer enters the image position of the four corner seats in the edge node's local config; every other seat is placed by a perspective transform. No camera image is ever needed on the web side.
- **Output.**
  - `session_results/{session_id}`: live state of every seat, overwritten every 10 s of monitoring.
  - `session_evaluations/{session_id}_{seat_id}`: per-seat totals, overwritten every 5 minutes and at the end.
  - `sessions/{session_id}/alerts/{id}`: head drop, back turn and side conversation alerts.
  - `edge_nodes/{camera_id}`: heartbeat every 10 s.
- **Volume.** About 950 writes for a 40-seat class and a 45-minute session, against about 10,800 with the previous per-seat records.
- **Retention.** Every session document carries `expire_at`, so a Firestore TTL policy can delete it.
- **Security Rules.** `config/firestore.rules` is rewritten for the schema and tested on the emulator in CI (`rules-tests/`).

## 2. Choices to confirm at the meeting

| # | Topic | What camera-ai did | Why | To confirm |
|---|---|---|---|---|
| 1 | Alerts (UC09) | `sessions/{session_id}/alerts/{id}`: `session_id`, `seat_id`, `type`, `start_sec`, `duration_sec`; the teacher adds `status` (`acknowledged`, `dismissed`) | The diagram has no alert collection, and UC09 needs one | Path and fields |
| 2 | Edge heartbeat (UC04, UC10) | `edge_nodes/{camera_id}`: `class_id`, `online`, `status`, `session_id`, `fps`, `camera_ok`, `last_frame_at`, `updated_at` | The diagram has no device status, and the pre-start check needs one | Path and fields |
| 3 | Session status values | `scheduled` → `running` → `paused` ↔ `running` → `ended`; `cancelled` before the start | The diagram shows only `running` | The full list, and who sets each value |
| 4 | Metrics | `concentration`: score of the last 60 s. `avg_concentration`: score since the start. `distraction`: number of alerts. `interaction`: number of side-conversation alerts. Seat `status`: `focused`, `drowsy`, `distracted`, `away` | The diagram names the fields without defining them | Especially `interaction`: if it should mean participation (raising hands), the edge cannot measure it yet |
| 5 | `session_results` | One document per session (ID = session ID), overwritten every 10 s, plus a new `monitoring_status` field (`running`, `completed`, `incomplete`) | UC04 needs a way to mark a session whose data is partial | The overwrite (no history inside a session) and the extra field |
| 6 | `session_evaluations` | Collection name `session_evaluations`, ID `{session_id}_{seat_id}`, overwritten every 5 minutes and at the end, plus a new `observed_sec` field | Reports must ignore seats where someone only walked past, and weight class averages | Name, ID and the extra field |
| 7 | Seat positions | Four corner seats in the edge node's local config; seats have only `row` and `column` in Firestore | The diagram has no image coordinates, and a web calibration screen would need camera images on the web side | That calibration stays on the edge node |
| 8 | Seat→student mapping | `classes/{class_id}/seats/{seat_id}` documents (`row`, `column`, `student_id`, `status`) instead of a `seat_map` field on the class | Rules cannot hide one field of a document: anyone allowed to read a class (parents included) would see every child's seat | Moving `seat_map` into documents |
| 9 | One camera per class | The edge node is configured with one `class_id` and one `camera_id` | THPT classes keep their room | Classes that change rooms (labs) would need `camera_id` on the session |
| 10 | Timestamps | `captured_at` and `expire_at` are UTC times from the edge clock (keep NTP on); alert times stay as seconds since the session start | The diagram uses timestamps; the session already has `started_at` | That alerts keep `start_sec` |
| 11 | Parent view (UC03) | Parents read only `students/{sid}/reports/{s}`, written by a backend job after each session | Parents must not see other children's seats | That the web team builds the job, and what a report contains |
| 12 | Who reads seats | The Rules draft lets any teacher read seat documents (for the live view) and only the homeroom teacher change them | Subject teachers need names on the live seat map | Or a `teacher_ids` list on the class |
| 13 | Diagram fixes | The second "Teachers" box (bottom left) is a copy of "Parents"; the seat ID example `S01-ClassID` differs from the `Web` branch's `S1` | | Which seat ID format the app and web write |

## 3. What each part of the team needs to do

**Web admin (branch `Web`).** The branch was last changed on 2026-09-20 and still uses the earlier model. The review and nine concrete tasks are in `docs/web_admin_integration.md` ("State of the `Web` branch" and "Tasks for the web and app teams"). In short:

- Sessions on the schema: `teacher_id`, `started_at`/`ended_at`, statuses `running`/`ended`, start and end buttons.
- Seat documents instead of `seat_assignments`.
- Pre-start check on the heartbeat.
- Live view and alerts from `session_results` and `alerts`.
- Reports from `session_evaluations`.
- The parent report job.
- Camera health from `edge_nodes`.
- Removing `classrooms` (which stores camera passwords in Firestore), `enrollments` and `monitoring_sessions`.
- Taking the Firebase Web API key out of the code.

**Flutter app (`main`).**

- Read `sessions` instead of `monitoring_sessions`.
- The seating screen writes seat documents instead of `row`/`column` on student documents.
- The teacher live view reads `session_results` and acknowledges alerts.
- Parents read `students/{sid}/reports`.

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
- End-to-end test with the web admin and app on a test Firebase project, once tasks 1–4 of the web list are done.
- FCM push for alerts (UC09), after the alert path is confirmed.

## 5. Git history rewrite of `camera-ai`

- **What.** `camera-ai/simulated_data/test2.mp4`, real CCTV footage with identifiable faces, is removed from the branch history. Only the 22 commits from `4f948e64` (2026-09-27) onward are rewritten; their file contents are unchanged except for the removed video, and `main` and every other branch are untouched.
- **Status.** Force-pushed on 2026-10-17 (`0749529a` → `1bbd73eb`); CI passed on the new tip. No branch on GitHub contains `4f948e64` any more, and the repository has no forks.
- **Still exposed: act now.** The repository is public, and the closed pull request #3 (`camera-ai` → `main`) still has `4f948e64` as its head, so the video can still be downloaded from GitHub. The open pull request #4 also lists the old commits in its "force-pushed" event. The repository owner (`chinhvan001`):
  1. Makes the repository private: Settings → General → Danger Zone → Change repository visibility.
  2. Asks GitHub Support to remove sensitive data: repository `chinhvan001/NCKH-PrivateClass-Vision`, affected pull requests #3 and #4, first affected commit `4f948e64`. Ask them to drop the pull request refs and purge cached views and unreachable commits.
- **Everyone** who has the old branch either re-clones, or runs `git fetch origin`, `git checkout camera-ai` and `git reset --hard origin/camera-ai` (this discards uncommitted changes on that branch). Nobody may merge or push the old `camera-ai` commits, or the video comes back.
- **Optionally, clean the local copy:** `git update-ref -d refs/original/refs/heads/camera-ai`, then `git reflog expire --expire=now --all` and `git gc --prune=now`.
