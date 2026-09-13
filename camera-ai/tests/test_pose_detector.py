"""
test_pose_detector.py -- Unit test cho PoseDetector._parse_results()
(src/detection/pose_detector.py)

Vi sandbox phat trien khong cai duoc torch/ultralytics that (loi dung luong
dia/RAM), bo test nay dung CAC LOP GIA LAP mo phong dung cau truc du lieu tra
ve tu Ultralytics (result.keypoints.xy, result.keypoints.conf, result.boxes.xyxy,
result.boxes.conf -- deu la doi tuong co ham .tolist(), giong torch.Tensor).

Day la kiem thu PHAN LOGIC CHUYEN DOI DU LIEU (parse), KHONG PHAI kiem thu do
chinh xac cua model YOLOv8-pose that -- viec do BAT BUOC phai tu lam tren may
co cai duoc ultralytics.
"""

import pytest

from src.detection.pose_detector import COCO_KEYPOINT_NAMES, PersonPose, PoseDetector


class _FakeTensor:
    """Gia lap toi thieu mot torch.Tensor -- chi can .tolist()."""

    def __init__(self, data):
        self._data = data

    def tolist(self):
        return self._data


class _FakeKeypoints:
    def __init__(self, xy, conf):
        self.xy = _FakeTensor(xy)
        self.conf = _FakeTensor(conf) if conf is not None else None


class _FakeBoxes:
    def __init__(self, xyxy, conf):
        self.xyxy = _FakeTensor(xyxy)
        self.conf = _FakeTensor(conf)


class _FakeResult:
    def __init__(self, keypoints, boxes):
        self.keypoints = keypoints
        self.boxes = boxes


def _make_person_raw(base_x=0.0):
    """Sinh du lieu 17 keypoint gia lap cho 1 nguoi, moi diem co toa do khac
    nhau de de kiem tra thu tu khong bi xao tron."""
    xy = [[base_x + i, base_x + i * 2] for i in range(17)]
    conf = [0.9 - i * 0.01 for i in range(17)]
    return xy, conf


def test_parse_results_empty_list_returns_empty():
    assert PoseDetector._parse_results([]) == []


def test_parse_results_none_keypoints_returns_empty():
    result = _FakeResult(keypoints=None, boxes=_FakeBoxes([[0, 0, 10, 10]], [0.9]))
    assert PoseDetector._parse_results([result]) == []


def test_parse_results_none_boxes_returns_empty():
    xy, conf = _make_person_raw()
    kp = _FakeKeypoints([xy], [conf])
    result = _FakeResult(keypoints=kp, boxes=None)
    assert PoseDetector._parse_results([result]) == []


def test_parse_single_person():
    xy, conf = _make_person_raw(base_x=10.0)
    kp = _FakeKeypoints(xy=[xy], conf=[conf])
    boxes = _FakeBoxes(xyxy=[[5, 5, 100, 200]], conf=[0.87])
    result = _FakeResult(keypoints=kp, boxes=boxes)

    people = PoseDetector._parse_results([result])

    assert len(people) == 1
    person = people[0]
    assert isinstance(person, PersonPose)
    assert person.bbox == (5.0, 5.0, 100.0, 200.0)
    assert person.confidence == pytest.approx(0.87)
    assert len(person.keypoints) == 17
    # Diem dau tien (nose): x=10, y=10 theo cong thuc _make_person_raw(base_x=10)
    assert person.keypoints[0][0] == pytest.approx(10.0)
    assert person.keypoints[0][1] == pytest.approx(10.0)
    # Diem cuoi (right_ankle, index 16): x=10+16=26, y=10+32=42
    assert person.keypoints[16][0] == pytest.approx(26.0)
    assert person.keypoints[16][1] == pytest.approx(42.0)


def test_parse_multiple_people_30_students():
    """Test quan trong nhat cho dung bai toan cua du an: nhieu nguoi cung luc
    trong 1 khung hinh (mo phong 30 hoc sinh) -- xac nhan khong bi tron/mat
    du lieu giua cac nguoi."""
    n_people = 30
    all_xy = []
    all_kconf = []
    all_boxes = []
    all_bconf = []

    for person_idx in range(n_people):
        xy, conf = _make_person_raw(base_x=float(person_idx * 100))
        all_xy.append(xy)
        all_kconf.append(conf)
        all_boxes.append([person_idx * 100.0, 0.0, person_idx * 100.0 + 50, 100.0])
        all_bconf.append(0.5 + person_idx * 0.01)

    kp = _FakeKeypoints(xy=all_xy, conf=all_kconf)
    boxes = _FakeBoxes(xyxy=all_boxes, conf=all_bconf)
    result = _FakeResult(keypoints=kp, boxes=boxes)

    people = PoseDetector._parse_results([result])

    assert len(people) == n_people
    for person_idx, person in enumerate(people):
        expected_nose_x = float(person_idx * 100)
        assert person.keypoints[0][0] == pytest.approx(expected_nose_x)
        assert person.bbox[0] == pytest.approx(person_idx * 100.0)
        assert person.confidence == pytest.approx(0.5 + person_idx * 0.01)


def test_parse_handles_missing_keypoint_confidence():
    """Mot so phien ban Ultralytics/che do co the tra ve keypoints.conf =
    None (khong co diem tin cay rieng tung keypoint) -- khong duoc crash,
    phai gan mac dinh 1.0."""
    xy, _ = _make_person_raw()
    kp = _FakeKeypoints(xy=[xy], conf=None)
    boxes = _FakeBoxes(xyxy=[[0, 0, 50, 50]], conf=[0.9])
    result = _FakeResult(keypoints=kp, boxes=boxes)

    people = PoseDetector._parse_results([result])

    assert len(people) == 1
    assert all(c == 1.0 for (_, _, c) in people[0].keypoints)


def test_no_people_detected_returns_empty_list():
    kp = _FakeKeypoints(xy=[], conf=[])
    boxes = _FakeBoxes(xyxy=[], conf=[])
    result = _FakeResult(keypoints=kp, boxes=boxes)

    assert PoseDetector._parse_results([result]) == []


def test_get_keypoint_by_name():
    xy, conf = _make_person_raw()
    person = PersonPose(
        keypoints=[(float(x), float(y), c) for (x, y), c in zip(xy, conf)],
        bbox=(0.0, 0.0, 10.0, 10.0),
        confidence=0.9,
    )
    nose = person.get_keypoint("nose")
    left_shoulder = person.get_keypoint("left_shoulder")

    assert nose == person.keypoints[0]
    assert left_shoulder == person.keypoints[COCO_KEYPOINT_NAMES.index("left_shoulder")]
    assert person.get_keypoint("khong_ton_tai") is None


def test_open_raises_clear_error_when_ultralytics_missing(monkeypatch):
    """Gia lap truong hop chua cai 'ultralytics' -- phai nem PoseDetectorError
    ro rang, khong phai ImportError tho."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "ultralytics":
            raise ImportError("No module named 'ultralytics'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from src.detection.pose_detector import PoseDetector, PoseDetectorError

    detector = PoseDetector()
    with pytest.raises(PoseDetectorError, match="ultralytics"):
        detector.open()