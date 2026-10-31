"""EdgeRuntime voi FakeFirestore, CaptureWorker gia va pose replay: vong doi phien
(UC04), camera tam khong kha dung (UC02), heartbeat, session_results va
session_evaluations theo dong ho phien, so do lop chua san sang."""

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

from fake_firestore import FakeFirestore
from src.capture import CameraOpenError, Frame
from src.config import ClassLayoutError, LocalPipelineConfig
from src.pipeline import EdgeRuntime
from src.pipeline.edge_runtime import (
    CAMERA_RETRY_SEC,
    CAMERA_TIMEOUT_SEC,
    CLASS_CHECK_SEC,
    LAYOUT_RETRY_SEC,
    MAX_FRAME_GAP_SEC,
    UNCONFIGURED_CHECK_SEC,
)
from src.seating.seat_grid import Seat, SeatGrid
from src.sync import FirestoreSink
from test_end_to_end_pipeline import _person
from test_local_config import valid_config

SESSION = "sessions/s1"
RESULT = "session_results/s1"
HEARTBEAT = "edge_nodes/CAM-1"
MONDAY_9AM = datetime(2026, 10, 5, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))  # trong lich mon-tue 07:00-17:00
GRID = SeatGrid([Seat("A1", 90.0, 100.0), Seat("A2", 230.0, 100.0)])


class FakeWorker:
    """CaptureWorker gia: lay frame tu danh sach chung; het frame thi get() tra None
    giong camera mat tin hieu."""

    def __init__(self, frames, fail=False):
        self.frames, self.fail = frames, fail
        self.started = self.stopped = False
        self.buffer = self

    def start(self):
        if self.fail:
            raise CameraOpenError("Khong mo duoc camera voi source=rtsp://***@cam/stream.")
        self.started = True

    def stop(self):
        self.stopped = True

    @property
    def is_alive(self):
        return self.started and not self.stopped

    def get(self, timeout=None):
        return self.frames.pop(0) if self.frames else None


class TwoSeatProvider:
    def __init__(self, a1_head_down=False):
        self.calls = 0
        self.a1_head_down = a1_head_down

    def detect(self, image_bgr):
        assert image_bgr.any(), "frame phai con pixel khi inference"
        self.calls += 1
        return [_person(90.0, self.a1_head_down, wrist_dx=0.0), _person(230.0, False, wrist_dx=0.0)]


class Harness:
    def __init__(
        self,
        timestamps=(),
        *,
        inference_every_n_frames=1,
        now=MONDAY_9AM,
        camera_fails=False,
        layout=None,
        web_class=None,
        provider=None,
    ):
        data = valid_config()
        data["sampling"]["inference_every_n_frames"] = inference_every_n_frames
        if web_class is not None:
            data["camera"]["class_id"] = None  # lop admin gan tren web; test chay run() de nghe phien
        self.frames = [Frame(np.full((240, 320, 3), 128, np.uint8), 1000.0 + t, i) for i, t in enumerate(timestamps)]
        self.all_frames = list(self.frames)
        self.workers = []
        self.clock = 0.0
        self.client = FakeFirestore()
        self.sink = FirestoreSink(self.client, "CAM-1", retention_days=30, now=lambda: now)
        self.provider = provider or TwoSeatProvider()
        self.layout = layout or (lambda: GRID)
        self.runtime = EdgeRuntime(
            LocalPipelineConfig.from_dict(data),
            self.provider,
            lambda class_id: self.layout(),
            self.sink,
            self._new_worker,
            web_class=web_class,
            now=lambda: now,
            monotonic=lambda: self.clock,
            poll_sec=0.0,
        )
        self.camera_fails = camera_fails
        self.source_missing = False  # nhu main.py khi camera chua duoc them tren web
        if web_class is None:
            self.sink.watch_sessions("CLASS-1", self.runtime.on_sessions)
        self.session = self.client.document(SESSION)

    def _new_worker(self):
        if self.source_missing:
            raise CameraOpenError("Camera 'CAM-1' chua duoc them tren web admin (trang Quan ly camera).")
        self.workers.append(FakeWorker(self.frames, fail=self.camera_fails))
        return self.workers[-1]

    def set_status(self, status):
        """Web admin doi ``status`` cua phien (schema cua nhom: ``sessions/{s}`` co ``class_id``)."""
        self.session.set({"class_id": "CLASS-1", "status": status})

    def steps(self, count):
        for _ in range(count):
            self.runtime.step()

    def doc(self, path):
        assert self.sink.flush()
        return self.client.docs[path]

    def evaluations(self):
        assert self.sink.flush()
        return {path.split("_", 2)[-1]: doc for path, doc in self.client.docs.items() if "session_evaluations/" in path}


def test_session_start_pause_resume_end_controls_camera_and_writes_results():
    h = Harness(timestamps=[0.0, 0.5, 1.0, 1.5, 600.0, 600.5])
    h.steps(1)
    assert h.workers == [] and h.doc(HEARTBEAT)["status"] == "idle"
    assert h.doc(HEARTBEAT)["class_id"] == "CLASS-1"

    h.set_status("running")
    h.steps(4)
    assert len(h.workers) == 1 and h.provider.calls == 4
    result = h.doc(RESULT)
    assert (result["monitoring_status"], result["camera_id"], result["result_map"]) == ("running", "CAM-1", {})
    heartbeat = h.doc(HEARTBEAT)
    assert (heartbeat["status"], heartbeat["session_id"], heartbeat["camera_ok"]) == ("monitoring", "s1", True)

    h.set_status("paused")
    h.steps(1)
    assert h.workers[0].stopped and h.doc(HEARTBEAT)["status"] == "paused"

    h.set_status("running")  # 10 phut sau: worker moi, frame t=600
    h.steps(2)
    assert len(h.workers) == 2 and h.provider.calls == 6

    h.set_status("completed")
    h.steps(1)
    assert h.workers[1].stopped
    result = h.doc(RESULT)
    assert result["monitoring_status"] == "completed"
    assert result["result_map"] == {
        "A1": {"concentration": 100, "interaction": 0, "status": "focused"},
        "A2": {"concentration": 100, "interaction": 0, "status": "focused"},
    }
    evaluations = h.evaluations()
    assert sorted(evaluations) == ["A1", "A2"]
    assert (evaluations["A1"]["avg_concentration"], evaluations["A1"]["distraction"]) == (100, 0)
    # Dong ho phien khong dem 10 phut pause: 1.5s + toi da MAX_FRAME_GAP_SEC + 0.5s.
    assert evaluations["A1"]["observed_sec"] == round(1.5 + MAX_FRAME_GAP_SEC + 0.5)
    assert h.doc(HEARTBEAT)["status"] == "idle"


def test_live_results_every_10s_and_alerts_counted_per_seat():
    h = Harness(timestamps=[i * 0.5 for i in range(25)])  # 0 -> 12s
    h.provider.a1_head_down = True  # A1 cui dau, tay tinh tu dau phien
    h.set_status("running")
    h.steps(25)

    live = h.doc(RESULT)
    assert live["monitoring_status"] == "running"
    assert (live["result_map"]["A1"]["status"], live["result_map"]["A2"]["status"]) == ("drowsy", "focused")
    assert h.evaluations() == {}  # tong hop dau tien sau 5 phut giam sat
    assert [doc["type"] for path, doc in h.client.docs.items() if "/alerts/" in path] == ["head_drop"]

    h.set_status("completed")
    h.steps(1)
    evaluations = h.evaluations()
    assert (evaluations["A1"]["distraction"], evaluations["A2"]["distraction"]) == (1, 0)
    assert evaluations["A1"]["avg_concentration"] < evaluations["A2"]["avg_concentration"] == 100


def windows(h):
    assert h.sink.flush()
    return [doc for path, doc in sorted(h.client.docs.items()) if path.startswith("session_windows/s1_")]


def test_windows_carry_posture_seconds_per_seat_every_10s_and_close_with_the_session():
    h = Harness(timestamps=[i * 0.5 for i in range(25)])  # 0 -> 12s
    h.provider.a1_head_down = True
    h.set_status("running")
    h.steps(25)
    h.set_status("completed")
    h.steps(1)

    first, last = windows(h)
    assert first["run"] == last["run"] and (first["seq"], last["seq"]) == (0, 1)
    assert (first["start_sec"], first["end_sec"], first["monitoring_status"]) == (0.0, 10.0, "running")
    assert (last["start_sec"], last["end_sec"], last["monitoring_status"]) == (10.0, 12.0, "completed")
    assert set(first) == {
        "session_id", "camera_id", "run", "seq", "start_sec", "end_sec", "captured_at", "monitoring_status", "seats",
        "expire_at",
    }  # fmt: skip
    a1, a2 = first["seats"]["A1"], first["seats"]["A2"]
    # Lan thay dau tien chua tinh thoi gian; sau do moi frame 0.5 s thuoc trang thai vua xac nhan.
    assert (a2["normal_sec"], a2["slumping_sec"], a2["head_drop_sec"], a2["last_state"]) == (10.0, 0.0, 0.0, "normal")
    assert a1["normal_sec"] + a1["slumping_sec"] + a1["head_drop_sec"] == 10.0
    assert a1["head_drop_sec"] > 0 and last["seats"]["A1"]["last_state"] == "head_drop"
    assert last["seats"]["A2"]["normal_sec"] == 2.0 and last["seats"]["A2"]["last_seen_sec"] == 12.0
    alerts = [doc for path, doc in h.client.docs.items() if "/alerts/" in path]
    assert sum(window["seats"]["A1"]["alerts"].get("head_drop", 0) for window in (first, last)) == len(alerts) == 1


class HidingProvider:
    """A2 luon ngoi; A1 chi thay o frame 0-2 va tu frame 40 (frame cach nhau 1 s)."""

    def __init__(self):
        self.calls = 0

    def detect(self, image_bgr):
        index, self.calls = self.calls, self.calls + 1
        people = [_person(230.0, False, wrist_dx=0.0)]
        if index <= 2 or index >= 40:
            people.append(_person(90.0, False, wrist_dx=0.0))
        return people


def test_a_seat_hidden_for_more_than_30s_gets_no_time_for_the_gap():
    h = Harness(timestamps=[float(t) for t in range(46)], provider=HidingProvider())
    h.set_status("running")
    h.steps(46)
    h.set_status("completed")
    h.steps(1)

    docs = windows(h)
    assert [(doc["start_sec"], doc["end_sec"]) for doc in docs] == [(0, 10), (10, 20), (20, 30), (30, 40), (40, 45)]
    a1 = [doc["seats"].get("A1") for doc in docs]
    # Thay lai o giay 40 sau 38 s vang: khoang trong khong thuoc trang thai nao.
    assert [None if seat is None else seat["normal_sec"] for seat in a1] == [2.0, None, None, 0.0, 5.0]
    assert a1[3]["last_seen_sec"] == 40.0
    assert [doc["seats"]["A2"]["normal_sec"] for doc in docs] == [10.0, 10.0, 10.0, 10.0, 5.0]


def test_restart_mid_session_starts_a_new_run_so_window_ids_never_collide():
    h = Harness(timestamps=[0.0, 0.5])
    h.set_status("running")
    h.steps(2)
    h.runtime.close()  # tien trinh tat giua phien, phien van running tren web

    h.frames += [Frame(np.full((240, 320, 3), 128, np.uint8), 2000.0 + t, 10 + i) for i, t in enumerate([0.0, 0.5])]
    again = EdgeRuntime(
        LocalPipelineConfig.from_dict(valid_config()),
        h.provider,
        lambda class_id: GRID,
        h.sink,
        h._new_worker,
        now=lambda: MONDAY_9AM,
        monotonic=lambda: h.clock,
        poll_sec=0.0,
    )
    h.sink.watch_sessions("CLASS-1", again.on_sessions)
    again.step()
    again.step()
    again.close()

    docs = windows(h)
    assert len(docs) == 2 and docs[0]["run"] != docs[1]["run"]
    assert [doc["seq"] for doc in docs] == [0, 0]
    assert [doc["monitoring_status"] for doc in docs] == ["incomplete", "incomplete"]


def test_camera_loss_reports_temporarily_unavailable_until_frames_return():
    h = Harness(timestamps=[0.0])
    h.set_status("running")
    h.steps(1)
    assert h.doc(HEARTBEAT)["status"] == "monitoring"

    h.clock += CAMERA_TIMEOUT_SEC + 1  # khong co frame moi
    h.steps(1)
    heartbeat = h.doc(HEARTBEAT)
    assert (heartbeat["status"], heartbeat["camera_ok"]) == ("unavailable", False)

    h.frames.append(Frame(np.full((240, 320, 3), 128, np.uint8), 1010.0, 1))
    h.steps(1)
    assert h.doc(HEARTBEAT)["status"] == "monitoring"


def test_camera_that_cannot_open_is_unavailable_and_retried_later():
    h = Harness(camera_fails=True)
    h.set_status("running")
    h.steps(2)
    assert len(h.workers) == 1  # chua toi luc thu lai
    heartbeat = h.doc(HEARTBEAT)
    assert (heartbeat["status"], heartbeat["camera_ok"]) == ("unavailable", False)

    h.clock += CAMERA_RETRY_SEC
    h.steps(1)
    assert len(h.workers) == 2


def test_missing_class_layout_reports_unavailable_and_retries_later():
    attempts = []

    def layout():
        attempts.append(None)
        if len(attempts) == 1:
            raise ClassLayoutError("Khong co document classes/CLASS-1.")
        return GRID

    h = Harness(timestamps=[0.0], layout=layout)
    h.set_status("running")
    h.steps(2)
    assert (len(attempts), h.workers) == (1, [])
    assert h.doc(HEARTBEAT)["status"] == "unavailable"
    assert RESULT not in h.client.docs

    h.clock += LAYOUT_RETRY_SEC
    h.steps(1)
    assert len(attempts) == 2 and len(h.workers) == 1
    assert h.doc(RESULT)["monitoring_status"] == "running"


def test_deleted_session_is_incomplete():
    h = Harness(timestamps=[0.0, 0.5])
    h.set_status("running")
    h.steps(2)
    h.session.delete()
    h.steps(1)
    assert h.workers[0].stopped and h.doc(RESULT)["monitoring_status"] == "incomplete"


def test_other_class_is_ignored_and_cancelled_session_is_incomplete():
    h = Harness(timestamps=[0.0, 0.5])
    h.client.document("sessions/other").set({"class_id": "CLASS-2", "status": "running"})
    h.steps(1)
    assert h.workers == []

    h.set_status("running")
    h.steps(2)
    h.set_status("cancelled")
    h.steps(1)
    assert h.workers[0].stopped and h.doc(RESULT)["monitoring_status"] == "incomplete"


def test_shutdown_mid_session_marks_incomplete_and_reports_offline():
    h = Harness(timestamps=[0.0, 0.5])
    h.set_status("running")
    h.steps(2)
    h.runtime.close()

    result = h.doc(RESULT)
    assert (result["monitoring_status"], len(result["result_map"])) == ("incomplete", 2)
    assert sorted(h.evaluations()) == ["A1", "A2"]
    heartbeat = h.doc(HEARTBEAT)
    assert (heartbeat["online"], heartbeat["status"]) == (False, "idle")
    assert h.workers[0].stopped


def test_restart_mid_session_keeps_session_incomplete_even_when_ended_normally():
    h = Harness(timestamps=[0.0, 0.5])
    h.client.document(RESULT).set({"monitoring_status": "running"})  # tien trinh truoc chet giua phien
    h.set_status("running")
    h.steps(2)
    h.set_status("completed")
    h.steps(1)
    assert h.doc(RESULT)["monitoring_status"] == "incomplete"


def test_active_session_outside_schedule_never_opens_camera():
    sunday = datetime(2026, 10, 4, 9, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    h = Harness(timestamps=[0.0], now=sunday)
    h.set_status("running")
    h.steps(3)
    assert h.workers == [] and h.provider.calls == 0
    assert h.doc(HEARTBEAT)["status"] == "outside_schedule"


def test_only_every_nth_frame_is_inferred_and_every_frame_is_wiped():
    h = Harness(timestamps=[0.0, 0.25, 0.5, 0.75], inference_every_n_frames=2)
    h.set_status("running")
    h.steps(4)
    assert h.provider.calls == 2
    assert all(not np.any(frame.image) for frame in h.all_frames)


def test_dead_session_listener_is_resubscribed_once_firestore_is_reachable():
    h = Harness()
    watches = []

    def subscribe(class_id, callback):
        watches.append(h.sink.watch_sessions(class_id, callback))
        return watches[-1]

    rounds = []

    def should_stop():
        rounds.append(None)
        if len(rounds) == 2:
            watches[0].is_active = False  # listener chet khi mat mang
            h.sink.failures = 1  # sink cung dang ghi loi: chua dang ky lai
        if len(rounds) == 4:
            assert len(watches) == 1
            h.sink.failures = 0  # co mang lai
        return len(rounds) > 5

    h.runtime.run(subscribe, should_stop)
    assert len(watches) == 2
    assert not watches[1].is_active  # run() huy dang ky khi thoat
    assert h.doc(HEARTBEAT)["online"] is False


def test_class_set_on_the_web_admin_is_followed_and_only_changed_between_sessions():
    web = {"class_id": None}
    h = Harness([float(t) for t in range(30)], web_class=lambda: web["class_id"])
    callbacks = []

    def subscribe(class_id, callback):
        callbacks.append(callback)
        return h.sink.watch_sessions(class_id, callback)

    def scenario():
        yield
        assert (h.doc(HEARTBEAT)["status"], h.doc(HEARTBEAT)["class_id"]) == ("unconfigured", None)
        h.client.document("sessions/s2").set({"class_id": "CLASS-2", "status": "running"})
        web["class_id"] = "CLASS-1"  # admin them camera tren web
        h.clock += UNCONFIGURED_CHECK_SEC
        yield
        assert (h.doc(HEARTBEAT)["status"], h.doc(HEARTBEAT)["class_id"]) == ("idle", "CLASS-1")
        h.set_status("running")
        yield
        yield
        assert h.doc(HEARTBEAT)["status"] == "monitoring"
        web["class_id"] = "CLASS-2"  # admin doi lop giua tiet: tiet dang giam sat khong bi cat
        h.clock += CLASS_CHECK_SEC
        yield
        assert (h.doc(HEARTBEAT)["class_id"], h.doc(HEARTBEAT)["session_id"]) == ("CLASS-1", "s1")
        h.set_status("completed")
        yield
        assert h.doc(RESULT)["monitoring_status"] == "completed"
        yield  # het tiet roi moi doi lop, va nghe cac tiet cua CLASS-2
        assert (h.doc(HEARTBEAT)["status"], h.doc(HEARTBEAT)["class_id"]) == ("idle", "CLASS-2")
        callbacks[0]({"s1": "active"})  # snapshot den tre cua listener lop cu: bo qua
        yield
        assert (h.doc(HEARTBEAT)["class_id"], h.doc(HEARTBEAT)["session_id"]) == ("CLASS-2", "s2")

    steps = scenario()
    h.runtime.run(subscribe, lambda: next(steps, True) is True)
    assert len(callbacks) == 2


def test_camera_source_missing_on_the_web_is_unavailable_and_retried():
    h = Harness([0.0])
    h.source_missing = True
    h.set_status("running")
    h.steps(1)
    assert (h.doc(HEARTBEAT)["status"], h.doc(HEARTBEAT)["camera_ok"]) == ("unavailable", False)
    h.source_missing = False
    h.clock += CAMERA_RETRY_SEC
    h.steps(1)
    assert h.workers[0].started and h.doc(HEARTBEAT)["status"] == "monitoring"
