"""
pose_detector.py -- Module detection/: phat hien pose (khung xuong 17 diem
COCO) nhieu nguoi cung luc bang YOLOv8-pose (Ultralytics).

THAY THE cho FaceDetector/FaceLandmarker (huong facial-landmark cu) theo dung
quyet dinh pivot sang skeleton/pose-based (xem Algorithm-Pivot-Proposal.docx,
04/09/2026) -- tuan theo dung Proposal chinh thuc, khong dung facial biometric.

============================================================================
LY DO CHON YOLOv8-pose THAY VI MEDIAPIPE POSE:
============================================================================
MediaPipe Pose Landmarker co tham so num_poses nhung model goc CHI duoc huan
luyen/kiem dinh cho 1 nguoi (xac nhan chinh thuc tu google-ai-edge/mediapipe
issue #5842) -- khong bao loi khi num_poses>1, chi am tham cho ket qua khong
dang tin cay. YOLOv8-pose co kien truc object-detection mo rong, xu ly
multi-instance la ban chat thiet ke (huan luyen tren COCO-Pose voi 156.165
nguoi, nhieu anh chua hang chuc nguoi/anh) -- phu hop truc tiep voi lop hoc
30-40 hoc sinh trong 1 khung hinh.


"""

import logging
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger("camera_ai.detection")

# Ten 17 keypoint theo dung thu tu chuan COCO-Pose (khop voi thu tu output
# cua YOLOv8-pose) -- dung de truy cap keypoint theo ten thay vi nho chi so.
COCO_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


@dataclass
class PersonPose:
    """Mot nguoi (hoc sinh) phat hien duoc trong 1 khung hinh.

    keypoints: danh sach 17 phan tu (x, y, confidence), toa do PIXEL tuyet
        doi -- KHAC voi MediaPipe (normalized 0.0-1.0), YOLOv8-pose tra ve
        pixel truc tiep, khong can tu nhan voi width/height. Thu tu dung
        theo COCO_KEYPOINT_NAMES o tren.
    bbox: (x1, y1, x2, y2) -- toa do goc tren-trai va goc duoi-phai, pixel.
    confidence: do tin cay tong the cua viec phat hien nguoi nay (khac voi
        confidence rieng tung keypoint, nam trong phan tu thu 3 cua keypoints).
    """

    keypoints: List[Tuple[float, float, float]]
    bbox: Tuple[float, float, float, float]
    confidence: float

    def get_keypoint(self, name: str) -> Optional[Tuple[float, float, float]]:
        """Lay 1 keypoint theo ten (vi du 'nose', 'left_shoulder',
        'right_hip'...). Tra ve None neu ten khong hop le."""
        try:
            idx = COCO_KEYPOINT_NAMES.index(name)
        except ValueError:
            return None
        return self.keypoints[idx]


class PoseDetectorError(RuntimeError):
    """Nem ra khi khong nap duoc model YOLOv8-pose (thieu thu vien
    ultralytics, thieu file model, hoac model sai dinh dang)."""


class PoseDetector:
    """Boc YOLOv8-pose (Ultralytics) de phat hien khung xuong NHIEU NGUOI
    cung luc trong 1 khung hinh -- khac voi FaceDetector/FaceLandmarker cu
    (huong facial, da ngung dung).

    Cach dung:
        with PoseDetector("models/yolov8n-pose.pt") as detector:
            people = detector.detect(frame.image)  # frame.image: numpy BGR
            for person in people:
                nose = person.get_keypoint("nose")
    """

    def __init__(
        self,
        model_path: str = "models/yolov8n-pose.pt",
        min_confidence: float = 0.5,
        image_size: int = 960,
        iou_threshold: float = 0.5,
        max_detections: int = 100,
        tile_size: Optional[int] = None,
        tile_overlap: float = 0.2,
    ):
        """Tao detector cho canh nhieu nguoi.

        ``image_size`` cao hon mac dinh Ultralytics (640) de giu chi tiet cua
        hoc sinh o xa camera. Khi ``tile_size`` duoc dat, anh CCTV duoc chia
        thanh cac o giao nhau; day la cach de tang kich thuoc nguoi trong input
        ma khong resize ca khung 1080p/4K xuong 640. Cac pose trung nhau o
        vung giao duoc gop lai bang IoU sau khi dua toa do ve anh goc.
        """
        if image_size <= 0 or max_detections <= 0:
            raise ValueError("image_size va max_detections phai lon hon 0.")
        if not 0 < min_confidence <= 1 or not 0 < iou_threshold <= 1:
            raise ValueError("min_confidence va iou_threshold phai nam trong (0, 1].")
        if tile_size is not None and tile_size <= 0:
            raise ValueError("tile_size phai lon hon 0 hoac None.")
        if not 0 <= tile_overlap < 1:
            raise ValueError("tile_overlap phai nam trong [0, 1).")
        self._model_path = model_path
        self._min_confidence = min_confidence
        self._image_size = image_size
        self._iou_threshold = iou_threshold
        self._max_detections = max_detections
        self._tile_size = tile_size
        self._tile_overlap = tile_overlap
        self._model = None
        self._config_lock = threading.RLock()

    def apply_runtime_config(self, *, min_confidence: float, iou_threshold: float, image_size: int, max_detections: int, tile_size: Optional[int], tile_overlap: float) -> None:
        """Ap dung tham so moi giua hai frame, khong nap lai model."""
        if image_size <= 0 or max_detections <= 0 or not 0 < min_confidence <= 1 or not 0 < iou_threshold <= 1 or (tile_size is not None and tile_size <= 0) or not 0 <= tile_overlap < 1:
            raise ValueError("Pose runtime config khong hop le.")
        with self._config_lock:
            self._min_confidence, self._iou_threshold = min_confidence, iou_threshold
            self._image_size, self._max_detections = image_size, max_detections
            self._tile_size, self._tile_overlap = tile_size, tile_overlap

    # ------------------------------------------------------------------
    # Vong doi (lifecycle)
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Nap model YOLOv8-pose.

        Nem PoseDetectorError neu:
        - Chua cai thu vien 'ultralytics' (pip install ultralytics).
        - Model khong nap duoc (file hong/sai dinh dang, hoac loi khong
          xac dinh tu Ultralytics/torch).

        Luu y: neu model_path la ten model chuan cua Ultralytics (vi du
        'yolov8n-pose.pt') va CHUA co san cuc bo, Ultralytics se TU DONG TAI
        VE tu GitHub releases trong lan chay dau tien -- can mang internet o
        lan dau, nhung domain GitHub thuong KHONG bi chan boi cau hinh mang
        truong hoc/doanh nghiep thong thuong (khac voi model MediaPipe phai
        tai thu cong tu storage.googleapis.com, hay bi chan hon).
        """
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise PoseDetectorError(
                "Chua cai thu vien 'ultralytics'. Chay: pip install ultralytics "
                "(se tu dong cai kem torch)."
            ) from e

        try:
            self._model = YOLO(self._model_path)
        except Exception as e:  # Ultralytics/torch co the nem nhieu loai loi khac nhau
            raise PoseDetectorError(
                f"Khong nap duoc model YOLOv8-pose tu '{self._model_path}': {e}"
            ) from e

        logger.info(
            "Da nap YOLOv8-pose tu '%s' (conf=%.2f, imgsz=%d, tile=%s).",
            self._model_path, self._min_confidence, self._image_size,
            self._tile_size if self._tile_size is not None else "tat",
        )

    def close(self) -> None:
        self._model = None

    def __enter__(self) -> "PoseDetector":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Phat hien pose
    # ------------------------------------------------------------------

    def detect(self, image_bgr: "np.ndarray") -> List[PersonPose]:
        """Phat hien tat ca nguoi trong 1 khung hinh, tra ve danh sach
        PersonPose (co the rong neu khong phat hien ai).

        image_bgr: numpy array BGR (dung dinh dang tra ve tu Frame.image cua
                   module capture/ -- Ultralytics tu xu ly chuyen doi mau,
                   khong can tu convert sang RGB nhu voi MediaPipe).
        """
        if self._model is None:
            raise RuntimeError(
                "PoseDetector chua duoc mo. Goi open() truoc, hoac dung 'with'."
            )

        with self._config_lock:
            if self._tile_size is None:
                return self._predict(image_bgr)

            height, width = image_bgr.shape[:2]
        # Khong chia o cho khung nho hon tile: tranh lap lai inference vo ich.
            if width <= self._tile_size and height <= self._tile_size:
                return self._predict(image_bgr)

            people: List[PersonPose] = []
            for x, y, tile in self._iter_tiles(image_bgr):
                for person in self._predict(tile):
                    people.append(self._translate_pose(person, x, y))
            return self._deduplicate(people)

    def _predict(self, image_bgr: "np.ndarray") -> List[PersonPose]:
        results = self._model.predict(
            source=image_bgr,
            conf=self._min_confidence,
            iou=self._iou_threshold,
            imgsz=self._image_size,
            max_det=self._max_detections,
            classes=[0],  # COCO class 0 = person; tranh box cua cac vat the.
            verbose=False,
        )
        return self._parse_results(results)

    def _iter_tiles(self, image_bgr: "np.ndarray"):
        """Tra ve (x, y, tile) phu kin anh, khong bo sot mep phai/duoi."""
        height, width = image_bgr.shape[:2]
        assert self._tile_size is not None
        stride = max(1, int(self._tile_size * (1 - self._tile_overlap)))
        xs = self._tile_starts(width, self._tile_size, stride)
        ys = self._tile_starts(height, self._tile_size, stride)
        for y in ys:
            for x in xs:
                yield (
                    x,
                    y,
                    image_bgr[
                        y:min(y + self._tile_size, height),
                        x:min(x + self._tile_size, width),
                    ],
                )

    @staticmethod
    def _tile_starts(length: int, tile_size: int, stride: int) -> List[int]:
        if length <= tile_size:
            return [0]
        starts = list(range(0, length - tile_size + 1, stride))
        final_start = length - tile_size
        if starts[-1] != final_start:
            starts.append(final_start)
        return starts

    @staticmethod
    def _translate_pose(person: PersonPose, offset_x: int, offset_y: int) -> PersonPose:
        x1, y1, x2, y2 = person.bbox
        return PersonPose(
            keypoints=[(x + offset_x, y + offset_y, confidence) for x, y, confidence in person.keypoints],
            bbox=(x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y),
            confidence=person.confidence,
        )

    def _deduplicate(self, people: List[PersonPose]) -> List[PersonPose]:
        """NMS nhe cho ket qua tu cac tile, giu pose co confidence cao nhat."""
        kept: List[PersonPose] = []
        for person in sorted(people, key=lambda item: item.confidence, reverse=True):
            if all(self._box_iou(person.bbox, existing.bbox) < self._iou_threshold for existing in kept):
                kept.append(person)
        return kept[:self._max_detections]

    @staticmethod
    def _box_iou(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
        left, top = max(a[0], b[0]), max(a[1], b[1])
        right, bottom = min(a[2], b[2]), min(a[3], b[3])
        intersection = max(0.0, right - left) * max(0.0, bottom - top)
        area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
        area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
        union = area_a + area_b - intersection
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _parse_results(results) -> List[PersonPose]:
        """Chuyen doi ket qua tra ve tu Ultralytics (list[Results], 1 phan tu
        ung voi 1 anh dau vao) sang danh sach PersonPose.

        Tach rieng thanh staticmethod thuan de unit test duoc bang doi tuong
        gia lap (khong can model that) -- cung pattern da dung cho
        FaceDetector._parse_result / FaceLandmarker._parse_result.
        """
        people: List[PersonPose] = []
        if not results:
            return people

        result = results[0]  # predict() voi 1 anh dau vao -> list co 1 phan tu

        if result.keypoints is None or result.boxes is None:
            return people

        keypoints_xy = result.keypoints.xy.tolist()  # [[[x,y], ...17 diem], ...moi nguoi]
        keypoints_conf_tensor = result.keypoints.conf
        keypoints_conf = (
            keypoints_conf_tensor.tolist() if keypoints_conf_tensor is not None else None
        )
        boxes_xyxy = result.boxes.xyxy.tolist()
        boxes_conf = result.boxes.conf.tolist()

        for i, kp_xy in enumerate(keypoints_xy):
            kp_conf = keypoints_conf[i] if keypoints_conf is not None else [1.0] * len(kp_xy)

            keypoints = [
                (float(x), float(y), float(c))
                for (x, y), c in zip(kp_xy, kp_conf)
            ]

            people.append(
                PersonPose(
                    keypoints=keypoints,
                    bbox=tuple(float(v) for v in boxes_xyxy[i]),
                    confidence=float(boxes_conf[i]),
                )
            )

        return people
