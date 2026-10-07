"""FirestoreSink tren FakeFirestore: batch, retry/backoff, hang doi gioi han khi
mat mang (UC02 luong phu), heartbeat, tong ket phien, nghe phien. Khong can
credential, mang hay firebase_admin."""

import logging
import re
import time
from datetime import datetime, timezone

import numpy as np
import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError
from src.capture import CaptureConfig
from src.engagement.engagement_score import EngagementScore
from src.engagement.posture_monitor import PostureThresholds
from src.pipeline import AlertManager, run_pipeline
from src.privacy import anonymize_engagement, make_alert_event, make_session_summary
from src.seating.seat_grid import Seat, SeatGrid
from src.sync import EdgeHeartbeat, FirestoreSink, firestore_client_from_env
from test_end_to_end_pipeline import AlertScenarioProvider, _video

PREFIX = "sessions/s1"
HEARTBEAT = "classrooms/room-1/edge_nodes/cam-1"
RECORD_KEYS = {"seat_id", "observed_at_sec", "engagement_score", "posture_state", "head_drop_events", "slumping_events"}
ALERT_KEYS = {"session_id", "seat_id", "type", "start_sec", "duration_sec"}


def _record(seat_id="A1", t=0.0, state="normal"):
    return anonymize_engagement(EngagementScore(seat_id, 90.0, t, 0.0, 0.0, 0, 0), t, state)


def _alert(session_id="s1"):
    return make_alert_event(session_id, "A1", "head_drop", 1.0, 2.0)


def _heartbeat(status="monitoring"):
    return EdgeHeartbeat(True, status, "s1", 5.0, True, None, datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc))


def _sink(client, **kwargs):
    kwargs.setdefault("record_interval_sec", 0.0)  # tat throttle, tru test throttle
    return FirestoreSink(client, "room-1", "cam-1", **kwargs)


def _split(client):
    alerts = [doc for path, doc in client.docs.items() if "/alerts/" in path]
    records = [doc for path, doc in client.docs.items() if "/engagement/" in path]
    return alerts, records


def test_flush_commits_allowlisted_docs_in_batches_alerts_first():
    client = FakeFirestore()
    sink = _sink(client, batch_size=2)
    for t in range(4):
        sink.add_record("s1", _record(t=float(t)))
    sink.add_alert(_alert())

    assert sink.flush()

    assert [len(paths) for paths in client.commits] == [2, 2, 1]
    assert "/alerts/" in client.commits[0][0]
    assert all(re.fullmatch(PREFIX + r"/(engagement|alerts)/[0-9a-f]{32}", path) for path in client.docs)
    alerts, records = _split(client)
    assert alerts == [_alert().to_dict()]
    assert sorted(doc["observed_at_sec"] for doc in records) == [0.0, 1.0, 2.0, 3.0]
    assert all(set(doc) == RECORD_KEYS for doc in records)
    assert sink.pending == 0


def test_network_error_keeps_queue_and_backs_off_until_success():
    client = FakeFirestore()
    sink = _sink(client, flush_interval_sec=2.0, max_backoff_sec=60.0)
    for t in range(3):
        sink.add_record("s1", _record(t=float(t)))
    client.fail_next(FakeFirestoreError(503))
    client.fail_next(FakeFirestoreError(503))

    assert not sink.flush()
    assert (sink.pending, sink.failures, sink.backoff_sec) == (3, 1, 4.0)
    assert not sink.flush()
    assert (sink.pending, sink.failures, sink.backoff_sec) == (3, 2, 8.0)
    assert client.docs == {}

    assert sink.flush()
    assert (len(client.docs), sink.pending, sink.failures) == (3, 0, 0)

    sink.failures = 50
    assert sink.backoff_sec == 60.0


def test_retry_after_ambiguous_commit_does_not_duplicate_docs():
    client = FakeFirestore()
    sink = _sink(client)
    for t in range(3):
        sink.add_record("s1", _record(t=float(t)))
    client.fail_next(FakeFirestoreError(504), after_write=True)  # server da ghi, client bi timeout

    assert not sink.flush()
    assert sink.flush()
    assert len(client.docs) == 3


def test_full_queue_drops_oldest_records_but_keeps_alerts_and_summaries():
    client = FakeFirestore()
    sink = _sink(client, max_queue=3)
    sink.add_alert(_alert())
    sink.add_summary(make_session_summary("s1", "running", []))
    for t in range(4):
        sink.add_record("s1", _record(t=float(t)))

    assert (sink.pending, sink.dropped) == (3, 3)
    assert sink.flush()
    alerts, records = _split(client)
    assert len(alerts) == 1
    assert client.docs[f"{PREFIX}/summaries/cam-1"]["status"] == "running"
    assert [doc["observed_at_sec"] for doc in records] == [3.0]


def test_offline_queue_stays_bounded_and_drops_oldest_first():
    client = FakeFirestore()
    sink = _sink(client, max_queue=3, batch_size=2)
    for t in range(3):
        sink.add_record("s1", _record(t=float(t)))
    client.fail_next(FakeFirestoreError(503))
    assert not sink.flush()  # 2 item dang gui duoc tra lai DAU hang doi

    sink.add_record("s1", _record(t=3.0))  # hang doi day -> bo record cu nhat (t=0)

    assert (sink.pending, sink.dropped) == (3, 1)
    assert sink.flush()
    assert sorted(doc["observed_at_sec"] for doc in client.docs.values()) == [1.0, 2.0, 3.0]


def test_rejected_batch_is_dropped_instead_of_blocking_queue():
    client = FakeFirestore()
    sink = _sink(client, batch_size=1)
    sink.add_record("s1", _record(t=0.0))
    sink.add_record("s1", _record(t=1.0))
    client.fail_next(FakeFirestoreError(400))

    assert sink.flush()
    assert (sink.dropped, sink.pending) == (1, 0)
    assert [doc["observed_at_sec"] for doc in client.docs.values()] == [1.0]


def test_records_are_throttled_per_seat_unless_posture_changes():
    client = FakeFirestore()
    sink = _sink(client, record_interval_sec=10.0)
    for session_id, seat_id, t, state in [
        ("s1", "A1", 0.0, "normal"),  # ghe moi -> gui
        ("s1", "A1", 5.0, "normal"),  # < 10s, cung trang thai -> bo
        ("s1", "A1", 6.0, "head_drop"),  # doi trang thai -> gui
        ("s1", "A1", 12.0, "head_drop"),  # 6s tu lan gui truoc -> bo
        ("s1", "A1", 16.0, "head_drop"),  # du 10s -> gui
        ("s1", "B1", 5.0, "normal"),  # ghe khac -> gui
        ("s2", "A1", 1.0, "head_drop"),  # phien moi: record dau cua ghe luon gui
    ]:
        sink.add_record(session_id, _record(seat_id, t, state))

    assert sink.flush()
    sent = sorted((path.split("/")[1], doc["seat_id"], doc["observed_at_sec"]) for path, doc in client.docs.items())
    assert sent == [("s1", "A1", 0.0), ("s1", "A1", 6.0), ("s1", "A1", 16.0), ("s1", "B1", 5.0), ("s2", "A1", 1.0)]


def test_heartbeat_keeps_only_latest_and_survives_failed_flush():
    client = FakeFirestore()
    sink = _sink(client)
    sink.set_heartbeat(_heartbeat("monitoring"))
    client.fail_next(FakeFirestoreError(503))
    assert not sink.flush()

    sink.set_heartbeat(_heartbeat("unavailable"))  # thay ban cu chua gui duoc
    assert sink.pending == 1
    assert sink.flush()
    assert client.docs[HEARTBEAT]["status"] == "unavailable"
    assert set(client.docs[HEARTBEAT]) == {
        "online",
        "status",
        "session_id",
        "fps",
        "camera_ok",
        "last_frame_at",
        "updated_at",
    }
    with pytest.raises(ValueError):
        _heartbeat("recording")


def test_watch_sessions_maps_web_status_for_own_classroom_and_summary_exists():
    client = FakeFirestore()
    sink = _sink(client)
    seen = []
    watch = sink.watch_sessions(seen.append)
    for session_id, classroom_id, status in [
        ("s1", "room-1", "live"),
        ("s2", "room-1", "completed"),
        ("s3", "room-1", "paused"),
        ("s4", "room-1", "cancelled"),
        ("s5", "room-1", "scheduled"),
        ("s6", "room-1", ["live"]),  # document sua tay hong: khong lam chet listener
        ("s7", "room-2", "live"),  # lop khac
    ]:
        client.document(f"sessions/{session_id}").set(
            {"classroom_id": classroom_id, "status": status, "teacher_uid": "ignored"}
        )
    watch.unsubscribe()
    client.document("sessions/s1").set({"classroom_id": "room-1", "status": "completed"})

    assert seen[0] == {}
    assert seen[-1] == {"s1": "active", "s2": "ended", "s3": "paused", "s4": "cancelled", "s5": "scheduled", "s6": None}
    assert not sink.summary_exists("s1")
    client.document(f"{PREFIX}/summaries/cam-1").set({"status": "running"})
    assert sink.summary_exists("s1")


def test_summary_exists_treats_read_failure_as_new_session():
    class Offline(FakeFirestore):
        def document(self, path):
            raise FakeFirestoreError(503)

    assert not _sink(Offline()).summary_exists("s1")


def test_sink_only_accepts_allowlisted_schemas_and_valid_config():
    sink = _sink(FakeFirestore())
    with pytest.raises(TypeError):
        sink.add_record("s1", {"seat_id": "A1", "student_id": "SV001", "engagement_score": 80.0})
    with pytest.raises(TypeError):
        sink.add_alert({"session_id": "s1", "seat_id": "A1", "type": "head_drop"})
    with pytest.raises(TypeError):
        sink.add_summary({"session_id": "s1", "status": "completed"})
    with pytest.raises(ValueError):
        sink.add_record("../other", _record())  # session_id thanh duong dan Firestore
    assert sink.pending == 0
    with pytest.raises(ValueError):
        FirestoreSink(FakeFirestore(), "room/1", "cam-1")
    with pytest.raises(ValueError):
        FirestoreSink(FakeFirestore(), "room-1", "")
    with pytest.raises(ValueError):
        FirestoreSink(FakeFirestore(), "room-1", "cam-1", batch_size=501)


def test_failure_logs_never_echo_payload(caplog):
    client = FakeFirestore()
    sink = _sink(client, batch_size=1)
    sink.add_record("s1", _record(seat_id="SEAT-MARKER", t=0.0))
    sink.add_record("s1", _record(seat_id="SEAT-MARKER", t=1.0))
    client.fail_next(FakeFirestoreError(400, "invalid value for SEAT-MARKER"))
    client.fail_next(FakeFirestoreError(503, "unavailable while writing SEAT-MARKER"))

    with caplog.at_level(logging.WARNING, logger="camera_ai.sync"):
        assert not sink.flush()

    assert "FakeFirestoreError" in caplog.text
    assert "SEAT-MARKER" not in caplog.text


def test_alert_wakes_background_thread_without_waiting_for_interval():
    client = FakeFirestore()
    with _sink(client, flush_interval_sec=60.0) as sink:
        sink.add_alert(_alert())
        deadline = time.monotonic() + 2.0
        while not client.docs and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(client.docs) == 1


def test_close_flushes_remaining_queue():
    client = FakeFirestore()
    sink = _sink(client)
    sink.add_record("s1", _record())
    sink.close()
    assert (len(client.docs), sink.pending) == (1, 0)


def test_firestore_client_requires_service_account_key_file(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        firestore_client_from_env()
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "missing.json"))
    with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        firestore_client_from_env()


def test_pipeline_streams_into_firestore_sink(tmp_path):
    video = tmp_path / "sync.mp4"
    _video(video)
    client = FakeFirestore()
    sink = FirestoreSink(client, "room-1", "cam-1")  # mac dinh: 1 record/ghe/10s hoac khi doi trang thai
    seats = [Seat(seat_id, x, 100.0) for seat_id, x in (("A1", 90.0), ("A2", 230.0), ("A3", 370.0), ("A4", 510.0))]

    result = run_pipeline(
        CaptureConfig(source=str(video), target_fps=2.0),
        AlertScenarioProvider(),
        SeatGrid(seats),
        on_record=lambda record: sink.add_record("sess_test", record),
        max_frames=8,
        calibration_duration_sec=0.0,
        posture_thresholds=PostureThresholds(sustained_duration_sec=1.0),
        smoothing_window_sec=1.0,
        alert_manager=AlertManager("sess_test"),
        on_alert=sink.add_alert,
    )
    sink.close()

    alerts, records = _split(client)
    assert sorted((doc["seat_id"], doc["type"]) for doc in alerts) == [
        ("A1", "head_drop"),
        ("A2", "back_turn"),
        ("A3", "side_conversation"),
        ("A4", "side_conversation"),
    ]
    # 32 record (8 frame x 4 ghe) -> moi ghe 1 record dau + A1 luc chuyen sang head_drop.
    assert result.records_emitted == 32
    assert sorted((doc["seat_id"], doc["posture_state"]) for doc in records) == [
        ("A1", "head_drop"),
        ("A1", "normal"),
        ("A2", "normal"),
        ("A3", "normal"),
        ("A4", "normal"),
    ]
    assert all(set(doc) == RECORD_KEYS for doc in records)
    assert all(set(doc) == ALERT_KEYS for doc in alerts)


def test_fake_firestore_rejects_what_real_firestore_rejects():
    client = FakeFirestore()
    with pytest.raises(ValueError):
        client.document("classrooms/room-1/sessions")  # collection, khong phai document
    with pytest.raises(ValueError):
        client.collection("classrooms/room-1")  # document, khong phai collection
    batch = client.batch()
    with pytest.raises(TypeError):
        batch.set(client.document("a/b"), {"count": np.int64(3)})
    for index in range(501):
        batch.set(client.document(f"a/{index}"), {})
    with pytest.raises(FakeFirestoreError) as error:
        batch.commit()
    assert error.value.code == 400
