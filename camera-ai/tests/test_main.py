"""``python -m src.main`` tu choi config sai truoc khi cham toi camera, model hay Firebase."""

import json

from src.main import main
from test_local_config import valid_config


def test_main_exits_2_on_missing_or_invalid_config(tmp_path, monkeypatch, capsys):
    assert main(["--config", str(tmp_path / "missing.json")]) == 2

    data = valid_config()
    data["camera"]["rtsp_url"] = "rtsp://admin:S3cret@10.0.0.5/stream"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    assert main(["--config", str(bad)]) == 2

    monkeypatch.delenv("CAMERA_1_SOURCE", raising=False)
    no_source = tmp_path / "no_source.json"
    no_source.write_text(json.dumps(valid_config()), encoding="utf-8")
    assert main(["--config", str(no_source)]) == 2

    assert "S3cret" not in capsys.readouterr().err
