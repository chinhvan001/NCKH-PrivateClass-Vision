# Detector and posture calibration

On 15 November 2026 the pose detector settings and posture thresholds were checked against two sources:

- **SCB-Dataset (SCB5):** public classroom images with one box per student and a behaviour label.
- **`lop.mov`:** a 159-second classroom video at 2880x1620 and 15 fps, showing 5 students.

Both ran on the RTX 3050 Laptop GPU with `models/yolov8n-pose.pt`, through `tools/calibrate_pose.py` (see Reproduce, at the end). No frame, crop, box or keypoint was written to disk; the reports hold aggregate numbers only.

## Result

Since 17 November a lowered head counts as drowsy only when the student is slumped over; see Clip review and the head-pose fix, below.

Applied: `image_size` 1280 and `tile_size` null, as the defaults (`DEFAULT_SETTINGS` and `config/settings.example.json`). This replaces `image_size` 960 with tiles of 960. Kept: `pose_confidence` 0.2, `head_drop_ratio_threshold` 0.4, `conversation_max_distance_px` 260.

Why one pass at 1280 instead of tiles:

- **More students found:** on SCB it found 79.7% of labelled students with a usable pose, against 73.0% with tiles. For students under 64 px tall, it found 54.5% against 36.5%.
- **No body fragments:** on the video, tiles cut students at tile borders, so the same student was counted twice about 1.5 times per frame. With one pass this fell to 0.11. Hips were visible for 97% of poses, against 52% with tiles.
- **Faster:** a 2880x1620 frame takes 28 ms instead of 189 ms. With tiles, a single camera barely reached 5 inferences a second (the edge node's rate); with one pass, there is room for several cameras.

Not yet run on Camera 201 (1280x720), where one pass at 1280 is the camera's own resolution. Week 3 of `plan_to_2026-12-13.md` checks the new defaults on real lessons.

## Method

**SCB-Dataset.** 300 random validation images (seed 0) from each subset with one box per student:

| Subset | Labels | Students labelled |
|---|---|---|
| Handrise-Read-write | hand-raising, read, write | 2,309 |
| Stand | stand | 512 |
| Talk | talk | 379 |

Discuss (one box per group), BlackBoard-Screen (objects) and the teacher subsets were left out. Most images are 640x480 to 800x450, and some are 1920x1080.

Not every student in an SCB image has a label, so these numbers measure recall only. Precision cannot be measured, and the person boxes proposed in `data/person_gt_review` have not been reviewed yet.

A labelled student counts as found in two ways:

- **IoU ≥ 0.5:** a detected box overlaps the student's box.
- **Usable pose:** a detection has both shoulders at keypoint confidence ≥ 0.3, and their midpoint lies inside the student's box. This is how the edge node assigns a person to a seat, so this is the number that matters.

**Video.** Frames were taken at 5 Hz, as the edge node does (capture at 10 fps, inference on every second frame). There is no ground truth for the video, so:

- **Stable positions:** shoulder midpoints were grouped into positions; a position is stable if someone is there in at least half the frames.
- **Presence:** the share of frames in which a stable position has someone.
- **Duplicates:** pairs of detections in the same frame whose shoulder midpoints are less than half a shoulder width apart, i.e. one student counted twice.

The real `EngagementEngine` and `AlertManager` then ran on the recorded poses. Seats were rectangles around the 5 stable positions, standing in for the ones an admin draws on the web.

## Detector results

SCB, at confidence 0.2:

| Setting | ms per image | IoU ≥ 0.5 | Usable pose | Under 64 px | 64–128 px | Over 128 px |
|---|---|---|---|---|---|---|
| 640 | 19.3 | 58.9% | 67.9% | 11.2% | 56.1% | 80.9% |
| 960 | 21.1 | 64.8% | 76.2% | 36.2% | 68.2% | 85.3% |
| **1280 (new default)** | 26.7 | **66.4%** | **79.7%** | **54.5%** | **77.3%** | 84.3% |
| 960 with tiles of 960 (old default) | 67.9 | 59.6% | 73.0% | 36.5% | 71.5% | 79.1% |

Usable-pose recall at 1280 by confidence:

| Confidence | 0.10 | 0.15 | 0.20 | 0.30 | 0.50 |
|---|---|---|---|---|---|
| Usable pose | 85.5% | 82.6% | 79.7% | 74.0% | 60.3% |
| Under 64 px | 76.6% | 65.1% | 54.5% | 40.4% | 22.8% |

Lowering the confidence to 0.15 would find about 3 more students in 100, mostly small ones. Its cost in false detections cannot be measured on SCB, so 0.2 stays until real lessons show whether students at the back are missed.

Video (`lop.mov`), at confidence 0.2:

| Setting | ms per frame (median) | Max inferences/s | People per frame | Duplicate pairs per frame | Stable positions | Presence | Hips visible |
|---|---|---|---|---|---|---|---|
| 640 | 19.3 | 48 | 4 | 0.11 | 5 | 74% | 99% |
| 960 | 20.0 | 46 | 5 | 0.15 | 5 | 80% | 97% |
| **1280** | 27.6 | 35 | 5 | 0.11 | 5 | **81%** | 97% |
| 960 with tiles of 960 | 188.7 | 5.2 | 8 | 1.52 | 5 | 78% | 52% |

All settings found the same 5 students. With tiles, the 3 extra people per frame were fragments, never a sixth stable position.

**When tiles still help:** with a 4K camera, or a large room where students at the back have shoulders only a few tens of pixels wide, one pass at 1280 shrinks them too far. Then set `tile_size` (for example 960) in a `--settings` file, and measure it on that camera's video with the tool first.

## Posture results

**Head drop on SCB** (`head_drop_ratio`: nose-to-shoulder-line distance divided by shoulder width, frontal formula). Setting 1280, confidence 0.2:

| Label | Students with a usable pose | Median ratio | Below 0.4 | Hips visible |
|---|---|---|---|---|
| hand-raising | 389 | 0.63 | 5.9% | 53% |
| stand | 490 | 0.60 | 18.5% | 93% |
| talk | 355 | 0.60 | 15.2% | 86% |
| read | 903 | 0.31 | 62.4% | 68% |
| write | 413 | 0.08 | 85.9% | 79% |

- The best threshold for separating "looking down at the desk" (read, write) from "head up" (hand-raising) is 0.35 to 0.45 depending on the detector setting (Youden J ≈ 0.64). The current 0.4 sits inside that range, so it stays.
- The comment that sitting upright gives about 1.0–1.5 was wrong: upright students measure about 0.6. `PostureThresholds` now documents the measured values.
- The ratio cannot tell reading from dozing. Writing is softened by hand activity (counted as slumping, partial credit), but reading counts as head drop.
- Hips were visible for 53–93% of students depending on the behaviour, and for 97% on the video without tiles, so the torso (slumping) signal is usable more often than `posture.py` feared.

**Head drop on the video:** the median ratio was 0.41, and 47% of observations were below 0.4. Results by threshold, with the engine at setting 1280:

| `head_drop_ratio_threshold` | Head-drop alerts in 159 s (5 students) | Share of observed time in head drop |
|---|---|---|
| 0.2 | 2 | 0.7% |
| 0.3 | 6 | 5.5% |
| 0.4 (current) | 8 | 20.1% |
| 0.5 | 11 | 33.8% |

Whether 8 alerts are right depends on what the students in the video were doing. The report lists every alert as `minute:second seat type` (`alert_timeline`). Seats are numbered from the top row of the image, left to right.

If most of those alerts are students who were not looking down, this camera sits at a steeper angle than the SCB cameras. A fixed ratio then misfires, and the remedy is a per-seat baseline taken during the first minutes of the session, as the torso signal already has. A lower threshold would not fix it.

**Side conversation:** at the video's resolution, neighbouring students sat 237 px apart (median, 2.1 shoulder widths; the nearest pair 114 px, the farthest 350 px). With the threshold at 180 px no conversation alert fired, at 260 px 2 fired (at 01:26, seats S01 and S02), and at 360 px 3 fired.

`conversation_max_distance_px` is in pixels, so it depends on the camera's resolution and distance: the same room at 1280x720 has distances about 2.25 times smaller. There is no ground truth to tune it, so it stays at 260. Set it per machine to about 2.3 median shoulder widths of that camera; `median_shoulder_width_px` in the video report gives the width.

## Clip review and the head-pose fix (16–17 November)

The SCB numbers above come from public images. On this classroom's own video the posture rules did much worse.

**The review.** `tools/cut_action_clips.py` cut 120 clips of 2 seconds from `lop.mov`, each one student doing one action. The project lead marked each clip right or wrong and gave the real action (`doc/danh_gia_clip.csv`, not in git).

With the rules of 15 November, 38 of 120 clips were right (31.7%):

| Rule's verdict | Right |
|---|---|
| Sitting normally | 15 of 15 |
| Writing (head down, hands moving) | 11 of 28 |
| Head turned | 11 of 37 |
| **Drowsy (head down, hands still)** | **3 of 40** |

Three causes:

- **Turning the head lowers `head_drop_ratio`**, so a turned head read as a lowered one.
- **Seats at the edge of the image look turned all the time.** Their median head turn was −0.29 to −0.48, against about −0.1 near the centre.
- **Hand activity is unreliable.** It missed 12 of 30 writing clips, and it read the jittering keypoints of a slumped student as writing.

**The fix** (`src/engagement/posture_monitor.py`, used by `EngagementEngine`):

- **Drowsy only when slumped over** (`is_slumped_over`). `head_drop` now needs the nose at or below the shoulder line (`slumped_head_ratio_threshold` 0.0), or the head down with the torso tilted more than 15°. Hand activity no longer changes that verdict.
- **A head down short of that is reading or writing.** Below `head_drop_ratio_threshold` (0.4), it counts as `normal` with moving hands and as `slumping` (half credit) otherwise. It is never drowsy.
- **Head turn is measured against the seat's own usual turn** (`RunningMedian`, `head_turn_ratio_threshold` 0.12).
  - A turned head no longer counts as a lowered one (`head_signal_for`).
  - Side conversation uses the same baseline.

**Result on the same 120 clips,** with the edge node's rules applied frame by frame:

- 62 right (51.7%). Drowsy was right 5 times out of 5, and found 5 of the 8 drowsy clips.
- With the thresholds chosen on four seats and tested on the fifth, 51% were right, so the gain does not come only from fitting these clips.
- The rules were still shaped on these clips. The real test is the 160 new clips that do not overlap them, cut on 17 November for a second review.

**Still weak:**

- **Head turn:** predicted 57 times, right 22 times. The nose moves sideways while students write or look around.
- **Reading versus writing.**

Beyond threshold tuning, the next step is a classifier trained on the reviewed clips' keypoint sequences (package D in `plan_to_2026-12-13.md`).

## Second review: 280 clips and the frontal pose (19 November)

**The review.** The lead re-marked the first 120 clips without face blur and marked 160 new ones, 278 in all; 2 were left blank. With the rules of 17 November, 180 of 278 were right (64.7%): 52.5% of the first 120, and 74.1% of the 160 new ones. The new clips were picked with those rules, which favours them.

**What went wrong.** The seat's "usual" head turn was the median of all its frames, which follows the pose a student holds most. One student turned their head 60% of the time and another wrote 50% of the time, so turns and normal sitting were read against the wrong reference. Head turns were also checked before head-down, while a turned head barely lowers `head_drop_ratio` once it is measured against a frontal pose.

**The fix** (`src/engagement/posture.py`, `posture_monitor.py`, `EngagementEngine`):

- `FrontalBaseline` replaces the running median. For each seat it takes the frames whose eye distance, relative to shoulder width (`compute_eye_distance_ratio`), is in the top quarter: the moments the student faces the camera. It keeps the head turn, `head_drop_ratio` and ear height (`compute_ear_eye_offset`) of those frames.
- `is_head_down`: the head is down at the desk when `head_drop_ratio` is at least 0.12 below the frontal pose (`desk_head_drop`), or the ears are at least 0.06 shoulder widths higher above the eyes than in the frontal pose (`desk_ear_rise`). Until a seat has 25 frames with both eyes, the absolute threshold of 0.4 applies, as before.
- Head-down is checked before head turn. A head turn is 0.18 or more from the frontal turn (`head_turn_ratio_threshold`). Side conversation compares turns with the same frontal pose, and keeps its own 0.12.
- Drowsy is unchanged: slumped over only.

**Signals tried.** Separation, as AUC, of each signal against the frontal pose, over the 278 clips:

| Signal | Head turn vs sitting | Head down vs sitting | Head turn vs head down |
|---|---|---|---|
| Nose offset from shoulder midpoint | 0.85 (0.76 against the median) | 0.66 | 0.73 |
| `head_drop_ratio` | 0.60 | 0.85 | 0.88 |
| Ear height over eyes | 0.54 | 0.86 | 0.86 |

**Result.**

| Rules | Same 278 clips (thresholds chosen on them) | New seat, chosen on the other four | Same seats, unseen quarter of the lesson |
|---|---|---|---|
| 17 November | 64.7% | – | – |
| Frontal pose (now) | **71.2%** | **67.3%** | **69.4%** |

The 71.2% is optimistic: its thresholds were chosen on these clips. The last two columns choose them on the other folds and score the held-out one. Split into "on task" (sitting, reading or writing) against "off task" (head turned, slumped over), the frontal rules are right 75.9% and 77.0% of the time on the held-out folds.

**What did not help:**

- **Learned models:** a softmax classifier and a random forest on 65 clip features scored 47–54% on a new seat and 63–66% on an unseen quarter.
- **Larger pose models:** `yolo11s-pose` scored 64.4% and 68.3%, and `yolo11m-pose` 64.4% and 64.0%. `yolov8n-pose` stays the default.
- **Per-seat thresholds:** 62.6%.

**Where the remaining errors come from.** For each of the 80 errors we looked for twins: clips of the same seat whose measurements differ by less than half a rule threshold in total. The measurements are head turn, head drop, ear height, torso angle, how much turn and drop vary within the clip, and hand activity.

- **Same skeleton, different label: 26 errors**, in 16 groups of 66 clips. Each error has a twin that the lead labelled the way the rules predict, so no skeleton-only rule gets both right. For example, one student turned their head left by 0.25–0.29 from frontal, holding still. That was marked "head turn" at 1:45 and 1:53, and "sitting normally" at 2:05–2:11.
- **Action not in the skeleton: 13 errors.** The rules see another action in at least 90% of the clip's frames, and the seat has no twin with the lead's label. The action may be in the eyes, the hands, an object or speech, or the label slipped.
- **Mixed or near a threshold: 41 errors.** The pose changes within the clip or sits near a threshold. Better rules or more data could fix some of these.

If each twin group got its majority label, twins would still cost about 20 clips (7 points). So twins alone do not hold 4-way accuracy under 75%.

**Re-check (20 November).** The lead re-watched the 29 flagged items (79 clips) on a local page, `xem_lai_ngu_canh.html`, kept beside the clips outside the repo.

- **No item depended on context.** 23 were labelling slips, 4 had a skeleton drawn on the wrong person or head, and 2 had other reasons.
- **One note set a labelling convention:** a head that is both down and turned counts as down, which is the order the rules already use.
- **28 labels changed.** 23 of the changes agree with the rules, and 5 go against them.

Merged labels: `danh_gia_clip_sau_xem_lai.csv`. The rules are unchanged, and the thresholds chosen in-sample are still 0.18, −0.12 and −0.06.

| Labels | Same 278 clips | New seat | Unseen quarter of the lesson | On/off task, new seat / unseen quarter |
|---|---|---|---|---|
| Before the re-check | 71.2% | 67.3% | 69.4% | 75.9% / 77.0% |
| After the re-check | **77.7%** | **74.8%** | **76.3%** | 79.1% / 80.6% |

These numbers are not ready to quote yet. Only the clips where the rules and the label disagreed, plus their twins, were re-checked. Any slips among the other 199 clips would lower the scores, so a blind re-check of a random sample of those clips should come first.

**S02 holds half of the 62 remaining errors** (32 of its 64 clips are right). Without S02 the rules get 86% (184 of 214).

- **Right turns:** the lead marks 16 of 17 as head turns.
- **Left turns:** 10 of 21 are marked as sitting normally.
- **Small turns:** 11 clips with less than 0.18 of turn are marked as head turns.

This student's attentive direction may not be toward the camera, which would make the frontal pose the wrong reference for this seat.

## Reproduce

```powershell
cd camera-ai
venv\Scripts\python tools\calibrate_pose.py scb --dataset D:\Document\PCV\Temp-data\archive\SCB-Dataset --output reports\calibration_scb.json
venv\Scripts\python tools\calibrate_pose.py video --video D:\Videos\lop.mov --head-thresholds 0.2 0.3 0.4 0.5 --conversation-px 180 260 360 --output reports\calibration_video.json
```

- Options: `--configs` (`imgsz` or `imgsz:tile`, default `640 960 1280 960:960`), `--per-subset` (300), `--hz` (5).
- Run time: SCB about 4 minutes, the video about 3 minutes with the tile setting, under a minute without it.
- The detector runs once at confidence 0.1, and the results are filtered for each higher level. This is close to, but not exactly, running at that level.
