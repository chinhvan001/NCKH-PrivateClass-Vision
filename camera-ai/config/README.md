# Local config schema

Copy `local_pipeline.example.json` to a local file that stays out of Git (for example `local_pipeline.json`). The camera source is not in the JSON: put it in the environment variable named by `camera.source_env`, for example:

```powershell
$env:CAMERA_ROOM_A_01_SOURCE = "rtsp://..."
```

Then start the edge node with `python -m src.main --config config/local_pipeline.json` (see `docs/edge_node.md`).

Sections:

- `camera`: camera ID, classroom ID, resolution, and the **name** of the environment variable holding the camera source.
- `sampling`: capture FPS, and run pose inference on every n-th frame.
- `thresholds`: pose and alert thresholds.
- `schedule`: an IANA timezone and the weekday/time windows in which the camera may be opened. Outside them the edge node keeps the camera closed even if a session is active. The timezone is validated at load; on Windows this needs the `tzdata` package from `requirements.txt`.
- `privacy`: a buffer of exactly one frame, and no persistent output.

The schema rejects unknown keys such as `rtsp_url`, `student_id`, `name`, face models or embeddings, so that data cannot slip into the config by accident.
