"""LocalSink va file chung voi web admin: chi schema allowlist, ghi de nguyen tu (ke ca khi Windows
dang khoa file), JSONL chi them, tong hop gop theo ghe, loi dia khong lam dung edge, file tiet cua
camera -> trang thai phien, xoa du lieu tiet cu."""

import json
import logging
import os
import stat
from datetime import datetime, timezone

import pytest

import src.sync.local_store as local_store
from src.capture import CaptureConfig
from src.engagement.posture_monitor import PostureThresholds
from src.pipeline import AlertManager, run_pipeline
from src.privacy import SeatEvaluation, SeatResult, SessionResult, SessionWindow, make_alert_event
from src.seating.seat_grid import Seat, SeatGrid
from src.sync import EdgeHeartbeat, LocalSink, camera_session, camera_source, cameras, prune_sessions, session_states
from test_end_to_end_pipeline import AlertScenarioProvider, _video

NOW = datetime(2026, 10, 2, 0, 30, tzinfo=timezone.utc)


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _result(status="running", concentration=80):
    return SessionResult("s1", "cam-1", NOW, status, (SeatResult("A1", concentration, 0, "focused"),))


def _evaluation(seat_id="A1", avg=80):
    return SeatEvaluation("s1", seat_id, NOW, 75, avg, 1, 600)


def test_sink_writes_exactly_the_allowlisted_schemas(tmp_path):
    sink = LocalSink(tmp_path, "cam-1")
    sink.add_alert(make_alert_event("s1", "A1", "head_drop", 1.0, 2.0))
    sink.add_window(SessionWindow("s1", "cam-1", "0a1b2c3d", 0, 0.0, 10.0, NOW, "running", ()))
    sink.set_result(_result())
    sink.set_heartbeat(EdgeHeartbeat(True, "monitoring", "s1", 5.0, True, None, NOW))

    session = tmp_path / "sessions" / "s1"
    (alert,) = lines(session / "alerts.jsonl")
    assert set(alert) == {"id", "session_id", "seat_id", "type", "start_sec", "duration_sec"}
    (window,) = lines(session / "windows.jsonl")
    assert (window["run"], window["seq"], window["captured_at"]) == ("0a1b2c3d", 0, NOW.isoformat())
    assert json.loads((session / "result.json").read_text(encoding="utf-8"))["result_map"]["A1"]["concentration"] == 80
    heartbeat = json.loads((tmp_path / "edge_nodes" / "cam-1.json").read_text(encoding="utf-8"))
    assert set(heartbeat) == {"online", "status", "session_id", "fps", "camera_ok", "last_frame_at", "updated_at"}
    assert sink.result_exists("s1") and not sink.result_exists("s2")
    if os.name == "posix":  # chi chu tai khoan doc duoc; Windows bo qua mode, dung ACL (src/sync/README.md)
        assert {stat.S_IMODE(path.stat().st_mode) for path in tmp_path.rglob("*") if path.is_file()} == {0o600}

    for bad in ({"session_id": "s1"}, None):
        for method in (sink.add_alert, sink.add_window, sink.set_result, sink.set_heartbeat):
            with pytest.raises(TypeError):
                method(bad)
        with pytest.raises(TypeError):
            sink.set_evaluations([bad])
    with pytest.raises(ValueError):
        sink.result_exists("../s1")
    for camera_id in ("", "a/b", "a\\b", None):
        with pytest.raises(ValueError):
            LocalSink(tmp_path, camera_id)
    with pytest.raises(ValueError):
        EdgeHeartbeat(True, "unconfigured", None, 0.0, None, None, NOW)


def test_overwritten_files_keep_the_latest_version_and_evaluations_merge_per_seat(tmp_path):
    sink = LocalSink(tmp_path, "cam-1")
    sink.set_result(_result(concentration=10))
    sink.set_result(_result("completed", concentration=90))
    sink.set_evaluations([_evaluation("A1", 50), _evaluation("A2", 60)])
    sink.set_evaluations([_evaluation("A1", 70)])  # lan chay sau cua tiet chi thay A1

    session = tmp_path / "sessions" / "s1"
    result = json.loads((session / "result.json").read_text(encoding="utf-8"))
    assert (result["monitoring_status"], result["result_map"]["A1"]["concentration"]) == ("completed", 90)
    evaluations = json.loads((session / "evaluations.json").read_text(encoding="utf-8"))
    assert {seat: data["avg_concentration"] for seat, data in evaluations.items()} == {"A1": 70, "A2": 60}
    assert sorted(path.name for path in session.iterdir()) == ["evaluations.json", "result.json"]  # khong con file tam


def test_replace_retries_while_another_process_holds_the_file(tmp_path, monkeypatch):
    real_replace, calls = os.replace, []

    def busy_twice(source, target):
        calls.append(target)
        if len(calls) <= 2:
            raise PermissionError(13, "Access is denied")  # Windows: backend dang doc file
        real_replace(source, target)

    monkeypatch.setattr(local_store.os, "replace", busy_twice)
    LocalSink(tmp_path, "cam-1").set_result(_result())
    assert len(calls) == 3 and (tmp_path / "sessions" / "s1" / "result.json").exists()


def test_disk_errors_are_counted_and_logged_without_payload(tmp_path, caplog):
    blocked = tmp_path / "sessions"
    blocked.write_text("khong phai thu muc", encoding="utf-8")  # mkdir loi nhu dia day/bi khoa
    sink = LocalSink(tmp_path, "cam-1")
    with caplog.at_level(logging.ERROR, logger="camera_ai.sync"):
        sink.set_result(_result())
        sink.add_alert(make_alert_event("s1", "A7", "head_drop", 1.0, 2.0))
    assert sink.dropped == 2
    assert "A7" not in caplog.text and "result.json" in caplog.text


def test_web_files_give_cameras_sources_and_session_states(tmp_path):
    (tmp_path / "cameras").mkdir()
    (tmp_path / "cameras" / "Camera 201.json").write_text(
        json.dumps({"angle_type": "top_down", "source": "rtsp://u:p@cam/1"}), encoding="utf-8"
    )
    (tmp_path / "cameras" / ".Camera 202.json.0f.tmp").write_text("{", encoding="utf-8")  # web dang ghi do
    assert cameras(tmp_path) == {"Camera 201": {"angle_type": "top_down", "source": "rtsp://u:p@cam/1"}}
    assert (camera_source(tmp_path, "Camera 201"), camera_source(tmp_path, "Camera 202")) == ("rtsp://u:p@cam/1", None)

    assert camera_session(tmp_path, "Camera 201") is None and session_states(None) == {}
    order = tmp_path / "camera_sessions" / "Camera 201.json"
    order.parent.mkdir()
    for status, state in [("running", "active"), ("paused", "paused"), ("completed", "ended"), (3, None)]:
        order.write_text(json.dumps({"session_id": "s1", "status": status}), encoding="utf-8")
        assert session_states(camera_session(tmp_path, "Camera 201")) == {"s1": state}
    assert session_states({"session_id": "../s1", "status": "running"}) == {}


def test_prune_removes_only_sessions_older_than_retention(tmp_path):
    sink = LocalSink(tmp_path, "cam-1")
    sink.set_result(_result())
    sink.set_result(SessionResult("s2", "cam-1", NOW, "running", ()))
    old = tmp_path / "sessions" / "s1" / "result.json"
    os.utime(old, (old.stat().st_mtime - 31 * 86400,) * 2)

    assert prune_sessions(tmp_path, 30) == 1
    assert sorted(path.name for path in (tmp_path / "sessions").iterdir()) == ["s2"]
    assert prune_sessions(tmp_path / "missing", 30) == 0


def test_pipeline_streams_alerts_into_the_sink(tmp_path):
    video = tmp_path / "sync.mp4"
    _video(video)
    sink = LocalSink(tmp_path, "cam-1")
    seats = [Seat(seat_id, x, 100.0) for seat_id, x in (("A1", 90.0), ("A2", 230.0), ("A3", 370.0), ("A4", 510.0))]

    run_pipeline(
        CaptureConfig(source=str(video), target_fps=2.0),
        AlertScenarioProvider(),
        SeatGrid(seats),
        on_record=lambda record: None,
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=1.0,
        alert_manager=AlertManager("sess_test"),
        on_alert=sink.add_alert,
    )

    alerts = lines(tmp_path / "sessions" / "sess_test" / "alerts.jsonl")
    assert sorted((alert["seat_id"], alert["type"]) for alert in alerts) == [
        ("A1", "head_drop"),
        ("A2", "back_turn"),
        ("A3", "side_conversation"),
        ("A4", "side_conversation"),
    ]
    assert len({alert["id"] for alert in alerts}) == 4
