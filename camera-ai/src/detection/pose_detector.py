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

    def __init__(self, model_path: str = "models/yolov8n-pose.pt", min_confidence: float = 0.5):
        self._model_path = model_path
        self._min_confidence = min_confidence
        self._model = None

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
            "Da nap YOLOv8-pose tu '%s' (min_confidence=%.2f).",
            self._model_path, self._min_confidence,
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

        results = self._model.predict(
            source=image_bgr, conf=self._min_confidence, verbose=False
        )
        return self._parse_results(results)

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