from src.config.remote_seat_grid import FirestoreSeatGridSource, RuntimeConfigPoller, SeatGridResolver


class Reader:
    def __init__(self, payload):
        self.payload = payload

    def get(self, path):
        return self.payload


def payload(version=1):
    return {
        "schema_version": 1,
        "config_version": version,
        "camera_id": "cam-1",
        "classroom_id": "room-1",
        "camera_angle_type": "top_down",
        "seats": [{"seat_id": "A1", "center_x": 10, "center_y": 20}],
    }


def test_fetch_validates_and_returns_angle_and_grid():
    result = FirestoreSeatGridSource(Reader(payload())).fetch("cam-1", "room-1")
    assert result.camera_angle_type == "top_down"
    assert result.grid.get_seat("A1").center_x == 10


def test_resolver_keeps_newest_version_in_memory():
    reader = Reader(payload(2))
    resolver = SeatGridResolver(FirestoreSeatGridSource(reader), "cam-1", "room-1")
    assert resolver.refresh().config_version == 2
    reader.payload = payload(1)
    assert resolver.refresh().config_version == 2


def test_poller_applies_new_pose_config_without_restart():
    class Pose:
        def __init__(self):
            self.applied = []

        def apply_runtime_config(self, **kwargs):
            self.applied.append(kwargs)

    pose = Pose()
    data = payload(2)
    data["pose"] = {
        "min_confidence": 0.2,
        "iou_threshold": 0.5,
        "image_size": 960,
        "max_detections": 100,
        "tile_size": None,
        "tile_overlap": 0.2,
    }
    poller = RuntimeConfigPoller(
        SeatGridResolver(FirestoreSeatGridSource(Reader(data)), "cam-1", "room-1"), pose, interval_sec=1
    )
    assert poller.refresh_once().config_version == 2
    assert pose.applied[0]["min_confidence"] == 0.2
