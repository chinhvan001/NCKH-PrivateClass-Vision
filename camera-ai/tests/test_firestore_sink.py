"""FirestoreSink tren FakeFirestore: batch, retry/backoff, hang doi gioi han khi
mat mang (UC02 luong phu), document ghi de (ket qua, tong hop, heartbeat),
expire_at cho TTL, nghe phien theo class_id. Khong can credential, mang hay firebase_admin."""

import logging
import re
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError
from src.capture import CaptureConfig
from src.engagement.posture_monitor import PostureThresholds
from src.pipeline import AlertManager, run_pipeline
from src.privacy import SeatEvaluation, SeatResult, SessionResult, SessionWindow, make_alert_event
from src.seating.seat_grid import Seat, SeatGrid
from src.sync import EdgeHeartbeat, FirestoreSink, firestore_client_from_env
from test_end_to_end_pipeline import AlertScenarioProvider, _video

NOW = datetime(2026, 10, 2, 0, 30, tzinfo=timezone.utc)
EXPIRE_AT = NOW + timedelta(days=30)
HEARTBEAT = "edge_nodes/cam-1"
RESULT = "session_results/s1"
ALERT_KEYS = {"session_id", "seat_id", "type", "start_sec", "duration_sec", "expire_at"}


def _alert(session_id="s1", seat_id="A1"):
    return make_alert_event(session_id, seat_id, "head_drop", 1.0, 2.0)


def _result(status="running", concentration=80):
    return SessionResult("s1", "cam-1", NOW, status, (SeatResult("A1", concentration, 0, "focused"),))


def _evaluation(seat_id="A1", avg=80):
    return SeatEvaluation("s1", seat_id, NOW, 75, avg, 1, 600)


def _heartbeat(status="monitoring"):
    return EdgeHeartbeat("class-1", True, status, "s1", 5.0, True, None, NOW)


def _sink(client, **kwargs):
    kwargs.setdefault("retention_days", 30)
    kwargs.setdefault("now", lambda: NOW)
    return FirestoreSink(client, "cam-1", **kwargs)


def _alerts(client):
    return [doc for path, doc in client.docs.items() if "/alerts/" in path]


def test_flush_sends_alerts_first_then_overwritten_docs_in_batches():
    client = FakeFirestore()
    sink = _sink(client, batch_size=2)
    sink.set_result(_result())
    sink.set_evaluations([_evaluation("A1"), _evaluation("A2")])
    for _ in range(3):
        sink.add_alert(_alert())

    assert sink.flush()

    assert [len(paths) for paths in client.commits] == [2, 2, 2]
    assert all("/alerts/" in path for path in client.commits[0])
    assert sorted(path for path in client.docs if "/alerts/" not in path) == [
        "session_evaluations/s1_A1",
        "session_evaluations/s1_A2",
        RESULT,
    ]
    assert all(re.fullmatch(r"sessions/s1/alerts/[0-9a-f]{32}", path) for path in client.commits[0])
    assert all(set(doc) == ALERT_KEYS for doc in _alerts(client))
    assert sink.pending == 0


def test_session_docs_carry_expire_at_for_ttl_but_heartbeat_does_not():
    client = FakeFirestore()
    sink = _sink(client)
    sink.add_alert(_alert())
    sink.set_result(_result())
    sink.set_evaluations([_evaluation()])
    sink.set_heartbeat(_heartbeat())
    assert sink.flush()

    assert client.docs[RESULT]["expire_at"] == EXPIRE_AT
    assert client.docs["session_evaluations/s1_A1"]["expire_at"] == EXPIRE_AT
    assert _alerts(client)[0]["expire_at"] == EXPIRE_AT
    assert "expire_at" not in client.docs[HEARTBEAT]


def test_windows_are_appended_once_per_run_and_seq_even_after_a_failed_commit():
    client = FakeFirestore()
    sink = _sink(client)
    window = SessionWindow("s1", "cam-1", "0a1b2c3d", 3, 30.0, 40.0, NOW, "running", ())
    sink.add_window(window)
    client.fail_next(FakeFirestoreError(503))
    assert not sink.flush()
    assert sink.flush()

    assert list(client.docs) == ["session_windows/s1_0a1b2c3d_00003"]
    assert client.docs["session_windows/s1_0a1b2c3d_00003"]["expire_at"] == EXPIRE_AT
    with pytest.raises(TypeError):
        sink.add_window(window.to_dict())  # chi nhan object allowlist


def test_network_error_keeps_queue_and_backs_off_until_success():
    client = FakeFirestore()
    sink = _sink(client, flush_interval_sec=2.0, max_backoff_sec=60.0)
    for _ in range(3):
        sink.add_alert(_alert())
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


def test_retry_after_ambiguous_commit_does_not_duplicate_alerts():
    client = FakeFirestore()
    sink = _sink(client)
    for _ in range(3):
        sink.add_alert(_alert())
    client.fail_next(FakeFirestoreError(504), after_write=True)  # server da ghi, client bi timeout

    assert not sink.flush()
    assert sink.flush()
    assert len(client.docs) == 3


def test_overwritten_docs_keep_only_the_latest_version_while_offline():
    client = FakeFirestore()
    sink = _sink(client)
    sink.set_result(_result(concentration=40))
    sink.set_heartbeat(_heartbeat("monitoring"))
    client.fail_next(FakeFirestoreError(503))
    assert not sink.flush()

    sink.set_result(_result(concentration=90))  # thay ban cu chua gui duoc
    sink.set_heartbeat(_heartbeat("unavailable"))
    sink.set_evaluations([_evaluation(avg=10)])
    sink.set_evaluations([_evaluation(avg=70)])
    assert sink.pending == 3
    assert sink.flush()

    assert client.docs[RESULT]["result_map"]["A1"]["concentration"] == 90
    assert client.docs["session_evaluations/s1_A1"]["avg_concentration"] == 70
    heartbeat = client.docs[HEARTBEAT]
    assert heartbeat["status"] == "unavailable"
    assert set(heartbeat) == {
        "class_id",
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


def test_full_alert_queue_drops_oldest_alerts():
    client = FakeFirestore()
    sink = _sink(client, max_queue=2)
    for seat_id in ("A1", "A2", "A3"):
        sink.add_alert(_alert(seat_id=seat_id))

    assert (sink.pending, sink.dropped) == (2, 1)
    assert sink.flush()
    assert sorted(doc["seat_id"] for doc in _alerts(client)) == ["A2", "A3"]


def test_rejected_batch_is_dropped_instead_of_blocking_queue():
    client = FakeFirestore()
    sink = _sink(client, batch_size=1)
    sink.add_alert(_alert(seat_id="A1"))
    sink.add_alert(_alert(seat_id="A2"))
    client.fail_next(FakeFirestoreError(400))

    assert sink.flush()
    assert (sink.dropped, sink.pending) == (1, 0)
    assert [doc["seat_id"] for doc in client.docs.values()] == ["A2"]


def test_watch_sessions_maps_status_for_own_class_and_result_exists():
    client = FakeFirestore()
    sink = _sink(client)
    seen = []
    watch = sink.watch_sessions("class-1", seen.append)
    for session_id, class_id, status in [
        ("s1", "class-1", "running"),
        ("s2", "class-1", "ended"),
        ("s3", "class-1", "paused"),
        ("s4", "class-1", "cancelled"),
        ("s5", "class-1", "scheduled"),
        ("s6", "class-1", ["running"]),  # document sua tay hong: khong lam chet listener
        ("s7", "class-1", "live"),  # gia tri cu cua nhanh Web
        ("s8", "class-1", "completed"),
        ("s9", "class-2", "running"),  # lop khac
    ]:
        client.document(f"sessions/{session_id}").set({"class_id": class_id, "status": status, "teacher_id": "t1"})
    watch.unsubscribe()
    client.document("sessions/s1").set({"class_id": "class-1", "status": "ended"})

    assert seen[0] == {}
    assert seen[-1] == {
        "s1": "active",
        "s2": "ended",
        "s3": "paused",
        "s4": "cancelled",
        "s5": "scheduled",
        "s6": None,
        "s7": "active",
        "s8": "ended",
    }
    assert not sink.result_exists("s1")
    client.document(RESULT).set({"monitoring_status": "running"})
    assert sink.result_exists("s1")


def test_result_exists_treats_read_failure_as_new_session():
    class Offline(FakeFirestore):
        def document(self, path):
            raise FakeFirestoreError(503)

    assert not _sink(Offline()).result_exists("s1")


def test_sink_only_accepts_allowlisted_schemas_and_valid_config():
    sink = _sink(FakeFirestore())
    with pytest.raises(TypeError):
        sink.add_alert({"session_id": "s1", "seat_id": "A1", "type": "head_drop"})
    with pytest.raises(TypeError):
        sink.set_result({"session_id": "s1", "result_map": {"A1": {"student_id": "SV001"}}})
    with pytest.raises(TypeError):
        sink.set_evaluations([{"session_id": "s1", "seat_id": "A1", "student_id": "SV001"}])
    with pytest.raises(ValueError):
        sink.result_exists("../other")  # session_id thanh duong dan Firestore
    assert sink.pending == 0
    with pytest.raises(ValueError):
        _sink(FakeFirestore(), retention_days=0)
    with pytest.raises(ValueError):
        FirestoreSink(FakeFirestore(), "cam/1", retention_days=30)
    with pytest.raises(ValueError):
        FirestoreSink(FakeFirestore(), "", retention_days=30)
    with pytest.raises(ValueError):
        _sink(FakeFirestore(), batch_size=501)


def test_failure_logs_never_echo_payload(caplog):
    client = FakeFirestore()
    sink = _sink(client, batch_size=1)
    sink.add_alert(_alert(seat_id="SEAT-MARKER"))
    sink.add_alert(_alert(seat_id="SEAT-MARKER"))
    client.fail_next(FakeFirestoreError(400, "invalid value for SEAT-MARKER"))
    client.fail_next(FakeFirestoreError(503, "unavailable while writing SEAT-MARKER"))

    with caplog.at_level(logging.WARNING, logger="camera_ai.sync"):
        assert not sink.flush()

    assert "FakeFirestoreError" in caplog.text
    assert "SEAT-MARKER" not in caplog.text


@pytest.mark.parametrize(
    "push", [lambda sink: sink.add_alert(_alert()), lambda sink: sink.set_result(_result("completed"))]
)
def test_alert_and_final_result_wake_background_thread_without_waiting(push):
    client = FakeFirestore()
    with _sink(client, flush_interval_sec=60.0) as sink:
        push(sink)
        deadline = time.monotonic() + 2.0
        while not client.docs and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(client.docs) == 1


def test_close_flushes_remaining_queue():
    client = FakeFirestore()
    sink = _sink(client)
    sink.set_result(_result())
    sink.close()
    assert (len(client.docs), sink.pending) == (1, 0)


def test_firestore_client_requires_service_account_key_file(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        firestore_client_from_env()
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "missing.json"))
    with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        firestore_client_from_env()


def test_pipeline_streams_alerts_into_firestore_sink(tmp_path):
    video = tmp_path / "sync.mp4"
    _video(video)
    client = FakeFirestore()
    sink = _sink(client)
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
    sink.close()

    assert sorted((doc["seat_id"], doc["type"]) for doc in _alerts(client)) == [
        ("A1", "head_drop"),
        ("A2", "back_turn"),
        ("A3", "side_conversation"),
        ("A4", "side_conversation"),
    ]
    assert all(set(doc) == ALERT_KEYS for doc in _alerts(client))


def test_fake_firestore_rejects_what_real_firestore_rejects():
    client = FakeFirestore()
    with pytest.raises(ValueError):
        client.document("classes/class-1/seats")  # collection, khong phai document
    with pytest.raises(ValueError):
        client.collection("classes/class-1")  # document, khong phai collection
    batch = client.batch()
    with pytest.raises(TypeError):
        batch.set(client.document("a/b"), {"count": np.int64(3)})
    for index in range(501):
        batch.set(client.document(f"a/{index}"), {})
    with pytest.raises(FakeFirestoreError) as error:
        batch.commit()
    assert error.value.code == 400
