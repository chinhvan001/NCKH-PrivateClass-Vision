# Supervisor Demo: Real Camera, Real Data

Written 2026-11-01, updated 2026-11-04: camera AI and the web admin now exchange their data as files in `edge-data/` on the laptop, and only the web admin's own data goes to Firestore. This is the run sheet for showing the supervisor the whole data flow on the real camera and the real Firestore project:

1. An admin adds the camera and draws the seats on the web admin.
2. The admin starts a lesson, and team members act out behaviours in front of the camera.
3. The web admin shows live seat states and alerts.
4. After the lesson, the evaluations and the parent reports appear.

The demo also shows what never leaves the edge node.

```
camera 192.168.1.219 (RTSP, 1280x720)
  -> edge node on the laptop: YOLOv8-pose -> seats -> posture -> scores
     (frames in RAM only, wiped after inference)
  -> edge-data/ on the laptop: heartbeat, results, windows, alerts, evaluations (never in Firestore)
  -> web admin (backend on the laptop): live view every 10 s, alerts, results
  -> Firestore: lessons, the frozen seating, parent reports students2/{student}/reports/{lesson}
```

## Where things stand on 1 November

| Item | State | Before the demo |
|---|---|---|
| Camera | Reachable from the laptop on the camera's network (192.168.1.x). Stream set to 1280x720. Inference runs on the laptop's GPU (RTX 3050) at about 50 ms a frame; it ran at 2.7 frames per second on the CPU. | Ready. Check that the edge log says "tren GPU". |
| Edge node | Checked with the real camera on 31 October and 1 November while it still wrote to Firestore: windows every 10 s, alerts counted, results written. The file exchange passed the offline demo on 4 November. | Check it once with the real camera at the rehearsal. |
| Camera on the web admin | Firestore is still in the old layout: there is no `cameras/Camera 201` and no `camera_id` on class 11B2. | Add the camera again on the camera page (rehearsal step 2). |
| Seats | None drawn on the web. Camera AI takes seats only from the web, and lessons cannot start until they are drawn. | Draw the seats on the web (rehearsal step 3). |
| Class 11B2 | 8 rows × 6 columns. Seats with a student: S01, S02, S05, S07, S08, S12, S14, S15, S16, S20. | Volunteers sit on seats that have a student. |
| Lessons | The next scheduled 11B2 lesson is on 13 November. | Create one for the demo slot. |
| Test snapshot | `CAMERA_SNAPSHOT=1` is set in `backend/.env`. | Needed to draw the seats. Turn it off after the rehearsal. |

Adding the camera again writes the new layout for this one camera:

- `cameras/Camera 201`;
- `edge-data/Camera 201` files on the laptop: `cameras/Camera 201.json` holds the address and password, and the old `camera_configs/Camera 201` is deleted from Firestore;
- `classes2/{11B2}.camera_id`.

Nothing else changes, so the full migration (`backend/jobs/migrate_schema.py --apply`) is not needed for the demo. It stays in week 1 of `docs/plan_to_2026-12-13.md`, to run with the team.

## People

| Role | Who | Task |
|---|---|---|
| Presenter | Project lead | Uses the web admin and explains. |
| Operator | One team member | Runs the backend and camera AI terminals and watches the camera AI log. |
| Volunteers | Four team members, on S01, S02, S07 and S08 | Sit in front of the camera and act out the script. |
| Data viewer | Someone with access to the Firebase console | Shows the documents in Firestore and the files in `edge-data/`. |

Volunteers are team members who agree to be on camera. Nothing is recorded. Do not put students in front of the camera until they have signed the consent form; package D's form is still with the mentor.

## Start the system

Three PowerShell terminals, from the repository root, on the `camera-ai` branch:

```powershell
# 1. Backend on the real Firebase project (backend/.env)
cd backend; ..\camera-ai\venv\Scripts\python app.py

# 2. Web admin: open http://localhost:5173 and sign in with the admin account
cd frontend; npm run dev

# 3. Camera AI, once for every camera on the web (no Firebase key: it reads and writes edge-data/)
cd camera-ai; venv\Scripts\python -m src.main
```

To check the cameras alone first, run the camera AI command with `--check-camera` added. Once Camera 201 is on the web, it should print `1280x720` at about 10 fps.

## Rehearsal: two days before, same room, same laptop

Once the seats are drawn, the camera must not move.

1. **Start.** Start the three processes. Camera AI needs no config file; its log says there is no camera on the web admin yet.
2. **Add the camera.** On the camera page, press "Thêm camera" and fill in:
   - Phòng: the room;
   - Tên camera: `Camera 201`;
   - Lớp: 11B2;
   - Góc đặt camera: "Phía trước lớp";
   - IP: `192.168.1.219`;
   - Port: `554`;
   - Đường dẫn luồng: `/h264/ch1/main/av_stream`;
   - Tài khoản and Mật khẩu: the camera's account.

   Within 30 s the row shows "Sẵn sàng · 11B2". The web never shows the account again.
3. **Seats.** The volunteers sit down. Open the camera's "Xác định chỗ ngồi", press "Lấy ảnh từ camera", draw one rectangle around each volunteer's upper body (S01, S02, S07, S08), and save. Each rectangle must contain the point between the volunteer's shoulders.

   Seat S07 and S08 next to each other: the side-conversation alert needs two seat centres within 260 px.
4. **Lessons.** On "Quản lý lịch học", create an 11B2 lesson for the demo slot and one for now.
5. **Run through.** Run the whole [demo script](#demo-script-about-35-minutes) on the lesson for now. Time it and check the [pass criteria](#pass-criteria).
6. **Clean up.** Delete the rehearsal lesson from its monitor window ("Xóa"). This also deletes its files in `edge-data/` and its reports.
7. **Snapshot off.** Comment out `CAMERA_SNAPSHOT=1` in `backend/.env` and restart the backend.

## Demo day: one hour before

- [ ] The laptop is on the camera's network. `--check-camera` prints 1280x720 at about 10 fps.
- [ ] The Windows clock is synchronised (Settings, Time, Sync now), and the Windows Time service is running. Sign-in fails with "Đăng nhập thất bại." when the clock is behind by even one or two seconds: the backend log shows "Token used too early".
- [ ] The demo slot is inside camera AI's schedule (by default Monday to Saturday, 06:30–18:00). Outside it, the camera stays closed even while a lesson is running.
- [ ] No 11B2 lesson is running or paused. Otherwise the start is refused: "Lớp đang có một tiết khác được giám sát".
- [ ] The edge node is running, and the camera page shows Camera 201 online, "Sẵn sàng · 11B2".
- [ ] The volunteers sit on the seats drawn at the rehearsal, and the camera has not moved.
- [ ] The Firebase console is open on the project's Firestore, and File Explorer on `edge-data/sessions/`.
- [ ] The [fallback](#if-something-goes-wrong) is ready.

## Demo script (about 35 minutes)

| Minutes | Step | Action | What the supervisor sees |
|---|---|---|---|
| 0–5 | Overview | Walk through the data flow above and the privacy rules. | |
| 5–8 | Setup | Camera page: Camera 201, its class, its status. | The camera was added on the web, and its address is never shown again. The seats were drawn once over a snapshot, and the snapshot is now off. |
| 8–10 | Start | "Quản lý lịch học", then the demo lesson, "Mở bảng giám sát" and "Bắt đầu giám sát". | Within about 10 s the edge log shows "Bat dau phien" and "Camera da mo thanh cong". The live view lists the volunteers' seats with student names. |
| 10–20 | Behaviours | The volunteers follow the [script](#volunteer-script). | The live view refreshes every 10 s: seat states, concentration and alerts. |
| 20–22 | Pause | "Tạm dừng", then "Tiếp tục". | The edge log shows "Da giai phong camera" on pause, and the camera opens again on resume. The camera only runs during a running lesson. |
| 22–24 | End | "Kết thúc". | Final seat results. Each volunteer's seat gets an evaluation. |
| 24–29 | Data | Firebase console and `edge-data/`, [what to show](#what-to-show). | Seat IDs, scores and counts only. |
| 29–32 | Reports | The operator runs the report job once: `cd backend; ..\camera-ai\venv\Scripts\python -m jobs.parent_reports`. | The monitor window shows "Báo cáo phụ huynh: đã tạo cho N học sinh". In Firestore: `students2/{student}/reports/{lesson}`. |
| 32– | Questions | | |

### Volunteer script

Times count from "Bắt đầu giám sát". Hold each behaviour well past its threshold: the live view can lag up to 20 s.

| Time | Seat | Behaviour | Expected on the web | Threshold |
|---|---|---|---|---|
| 0:00–1:30 | All | Sit upright and look at the board. | All seats "Tập trung", concentration near 100. | 5 s calibration at the start. |
| 1:30 | S01 | Head down on the desk for 20 s. | S01 "Buồn ngủ", one `head_drop` alert. | Head down for 5 s. |
| 3:00 | S07 and S08 | Turn to face each other and talk for 15 s. | One `side_conversation` alert, both seats "Mất tập trung". | 3 s; seat centres within 260 px. |
| 4:30 | S02 | Turn away from the camera for 15 s. | One `back_turn` alert, S02 "Mất tập trung". | Face hidden for 2 s while the shoulders stay visible. |
| 6:00 | S01 | Leave the camera's view for 60 s, then sit down again. | S01 "Không có mặt" after 30 s, then back to "Tập trung". | 30 s unseen. |
| 8:00 to end | All | Sit normally. | Concentration recovers within a minute. | Concentration covers the last 60 s. |

Repeating a behaviour on the same seat within 60 s merges into the same alert.

### What to show

| Where | Path | Holds | Point to make |
|---|---|---|---|
| Firestore | `sessions/{lesson}` | Status, `camera_id`, start and end times. | |
| Firestore | `sessions/{lesson}/monitored_students/{seat}` | Seat to student, frozen by the web backend when the lesson starts. | The edge node never receives it: names stay on the web side. |
| Firestore | `students2/{student}/reports/{lesson}` | One report per student, after the report job. | The only lesson data that goes to the cloud. |
| `edge-data/` | `camera_sessions/Camera 201.json` | The lesson the web gave the camera: status, seat counts and drawn rectangles. | No student IDs. |
| `edge-data/` | `edge_nodes/Camera 201.json` | Heartbeat: status, fps, camera state. | No address and no image. |
| `edge-data/` | `sessions/{lesson}/result.json` | Each seat's state and concentration, overwritten every 10 s. | Seat IDs and numbers only. |
| `edge-data/` | `sessions/{lesson}/windows.jsonl` | Seconds per seat in each posture, one line per 10 s. | The input for the backend scoring (package A). No keypoints and no boxes. |
| `edge-data/` | `sessions/{lesson}/alerts.jsonl` | Seat, type, and start and duration in lesson seconds. | No images. |
| `edge-data/` | `sessions/{lesson}/evaluations.json` | Final scores per seat. | |

Do not open `edge-data/cameras/Camera 201.json` on screen: it holds the camera's password.

On the laptop, `camera-ai/logs/camera-ai.log` shows the camera as `rtsp://***@192.168.1.219...`, and no image or video file is written anywhere.

### Known limits to state up front

- **Seats, not identities.** A seat is a rectangle on the image, not a person. A volunteer who changes seats is counted for the student of the new seat.
- **Hips are hidden behind the desks.** Slumping is not detected, and the edge log warns that it has no torso baseline. Head drop, turning away, side conversation and absence all work.
- **The numbers are not validated yet.** The scoring constants are starting values until package D validates them.
- **Scoring still runs on the edge node.** The backend scoring from the windows (package A) is in progress.
- **Parents cannot open their reports yet.** Nobody writes `students2.parent_id`, so the reports exist only in Firestore and in the web admin's counter.

## Pass criteria

- The camera opens within 15 s of "Bắt đầu giám sát" and closes within 15 s of "Tạm dừng" or "Kết thúc".
- Each acted behaviour shows on the right seat in the live view within 30 s, with one alert.
- `windows.jsonl` gets a line about every 10 s without gaps, and the last one says `completed`.
- Every volunteer's seat has an evaluation after the end, and the report job writes the reports.
- No image or video file on the laptop, and no camera password in the log.

## If something goes wrong

| Problem | What to do |
|---|---|
| Camera unreachable | Check that the laptop is on 192.168.1.x and run `--check-camera`. If it still fails, switch to the offline demo: stop the real backend, run `camera-ai/venv/Scripts/python backend/tests/demo_server.py`, and open http://localhost:5173/api/demo-login. It uses simulated people and no Firebase, and the steps are the same. |
| "Camera AI của lớp đang offline" at the start | Check that the edge node is running: its heartbeat is older than 30 s. The web offers to start anyway. |
| Seat IDs wrong or missing | The camera or the volunteers moved. Turn the snapshot on, redraw the seats, then turn it off again. |
| Heartbeat says `unavailable` | The seat plan or the camera failed to load. Read the edge log; the edge node retries every 10 s. |
| Sign-in fails | Synchronise the clock, and check `FIREBASE_API_KEY` in `backend/.env`. |

## After the demo

- Stop the edge node with Ctrl+C. A lesson still running is closed as `incomplete`.
- Keep the demo lesson to show again, or delete it from its monitor window. Deleting it removes its windows, results, alerts and reports.
- Keep the snapshot off.
- Write down the timings and any misses in `docs/plan_to_2026-12-13.md`.
```powershell
Set-Service w32time -StartupType Automatic
Start-Service w32time
w32tm /resync /force
```