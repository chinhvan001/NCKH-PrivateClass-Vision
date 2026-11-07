"""``python -m src.main``: cai dat sai bi tu choi truoc khi cham toi camera hay model; camera lay tu
file web admin ghi trong edge-data/, moi camera tren web co dung 1 edge node."""

import json

import pytest

import src.main as edge_main
from src.main import CameraSupervisor, list_cameras, main
from test_local_config import valid_config


@pytest.fixture
def web(tmp_path, monkeypatch):
    """Thu muc chung voi web admin: ``add(camera_id, **fields)`` nhu admin them camera tren trang Quan ly camera."""
    root = tmp_path / "edge-data"
    monkeypatch.setattr(edge_main, "DATA_DIR", root)

    def add(camera_id, **fields):
        path = root / "cameras" / f"{camera_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fields), encoding="utf-8")

    add.root = root
    return add


def test_main_exits_2_on_a_bad_settings_file_or_video(tmp_path, web, capsys):
    assert main(["--settings", str(tmp_path / "missing.json")]) == 2
    old = tmp_path / "local_pipeline.json"  # config theo tung camera cu, kem URL camera
    data = valid_config()
    data["camera"]["rtsp_url"] = "rtsp://admin:S3cret@10.0.0.5/stream"
    old.write_text(json.dumps(data), encoding="utf-8")
    assert main(["--settings", str(old)]) == 2
    assert main(["--video", str(tmp_path / "missing.mp4")]) == 2
    assert "S3cret" not in capsys.readouterr().err


def test_check_camera_reads_every_camera_added_on_the_web(tmp_path, web, capsys, synthetic_video):
    assert main(["--check-camera", "0.5"]) == 1  # chua co camera nao tren web
    web("Camera 201", source=synthetic_video)
    web("Camera 202", angle_type="top_down", source=str(tmp_path / "missing.mp4"))
    assert list_cameras(web.root) == {"Camera 201": "frontal", "Camera 202": "top_down"}

    assert main(["--check-camera", "0.5"]) == 1  # Camera 202 khong mo duoc
    output = capsys.readouterr()
    assert "Camera 201" in output.out and "320x240" in output.out and "Camera 202" in output.err
    assert main(["--check-camera", "0.5", "--camera", "Camera 201"]) == 0


def test_video_stands_in_for_the_camera_address(web, capsys, synthetic_video):
    web("Camera 201", angle_type="frontal")  # chua co dia chi tren web
    assert main(["--check-camera", "0.5"]) == 1
    assert main(["--video", synthetic_video, "--check-camera", "0.5"]) == 0
    assert "320x240" in capsys.readouterr().out


class FakeNode:
    def __init__(self, camera_id, angle):
        self.camera_id, self.angle, self.alive, self.stopped = camera_id, angle, True, False

    def is_alive(self):
        return self.alive

    def stop(self):
        self.stopped, self.alive = True, False


def test_supervisor_keeps_one_edge_node_per_camera_on_the_web():
    started = []
    supervisor = CameraSupervisor(lambda camera_id, angle: started.append(FakeNode(camera_id, angle)) or started[-1])
    supervisor.sync({"Camera 201": "frontal", "Camera 202": "frontal"})
    supervisor.sync({"Camera 201": "frontal", "Camera 202": "frontal"})  # khong doi gi
    first, second = started

    supervisor.sync({"Camera 201": "top_down"})  # doi goc Camera 201, xoa Camera 202 tren web
    assert first.stopped and second.stopped
    assert [(node.camera_id, node.angle) for node in started[2:]] == [("Camera 201", "top_down")]

    started[2].alive = False  # thread cua camera chet vi loi: chay lai
    supervisor.sync({"Camera 201": "top_down"})
    assert [node.camera_id for node in started] == ["Camera 201", "Camera 202", "Camera 201", "Camera 201"]
    supervisor.stop_all()
    assert started[3].stopped
