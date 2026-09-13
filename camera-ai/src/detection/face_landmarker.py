"""
face_landmarker.py -- Module detection/: phat hien landmark chi tiet khuon mat
bang MediaPipe Face Landmarker (Tasks API).

Day la ban nang cap tu FaceDetector (Sprint 2, chi co bounding box + 6 keypoint
co ban) len 478 diem landmark chi tiet + transformation matrix -- dung MediaPipe
Face Landmarker theo dung huong da chot trong tai lieu nghien cuu Sprint 1
(uu tien Tasks API thay vi solutions.face_mesh cu da ngung phat trien).

478 diem landmark nay se la dau vao truc tiep cho module engagement/ o Sprint 4
(tinh head pose tu transformation matrix, tinh eye-aspect-ratio tu landmark
vung mat).

QUAN TRONG -- can tai model thu cong truoc khi dung duoc module nay:
Khac voi FaceDetector (file .tflite don), Face Landmarker dung file .task
(bundle nhieu model con). Xem README.md trong thu muc nay de biet duong dan tai.

QUAN TRONG #2 -- so luong khuon mat toi da:
Mac dinh cua MediaPipe la num_faces=1 (toi uu cho ung dung 1 nguoi). Vi lop
hoc co nhieu hoc sinh, LandmarkerConfig.max_num_faces duoc dat mac dinh 30 --
xem config.py.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

from .config import LandmarkerConfig

logger = logging.getLogger("camera_ai.detection")


@dataclass
class FaceLandmarks:
    """Toan bo landmark cua MOT khuon mat phat hien duoc trong 1 khung hinh.

    points: danh sach (x_pixel, y_pixel, z_relative) cho tung diem landmark
        (478 diem neu dung model mac dinh, da bao gom vung mong mat/iris).
        x, y da quy doi ve pixel tuyet doi; z la do sau TUONG DOI (khong phai
        don vi met/cm that, chi dung de so sanh diem nao gan/xa camera hon).
    transformation_matrix: ma tran 4x4 (numpy array) mo ta phep bien doi tu mo
        hinh khuon mat chuan sang khuon mat trong khung hinh hien tai -- dung
        de suy ra head pose (yaw/pitch/roll) o Sprint 4 ma khong can tu cai
        dat solvePnP thu cong. None neu LandmarkerConfig.output_transformation_matrix=False.
    """

    points: List[Tuple[int, int, float]]
    transformation_matrix: Optional["np.ndarray"] = None


class FaceLandmarkerError(RuntimeError):
    """Nem ra khi khong khoi tao duoc FaceLandmarker (vi du thieu file model,
    hoac file model bi hong/sai dinh dang)."""


class FaceLandmarker:
    """Boc MediaPipe Face Landmarker (Tasks API) o che do VIDEO (dong bo -- phu
    hop voi vong lap 'pull' tu FrameBuffer cua module capture/), cung phong
    cach voi FaceDetector (Sprint 2) de de dung nhat quan trong pipeline.

    Cach dung:
        with FaceLandmarker(LandmarkerConfig.from_env()) as landmarker:
            faces = landmarker.detect(frame.image, frame.timestamp)
            for face in faces:
                print(len(face.points), face.transformation_matrix is not None)
    """

    def __init__(self, config: LandmarkerConfig):
        self._config = config
        self._landmarker: Optional[vision.FaceLandmarker] = None
        self._last_timestamp_ms: Optional[int] = None

    # ------------------------------------------------------------------
    # Vong doi (lifecycle)
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Nap file model va khoi tao MediaPipe FaceLandmarker.

        Nem FaceLandmarkerError neu khong tim thay file model, hoac MediaPipe
        khong nap duoc model (vi du file hong/sai dinh dang/tai thieu).
        """
        if not os.path.exists(self._config.model_path):
            raise FaceLandmarkerError(
                f"Khong tim thay file model tai '{self._config.model_path}'. "
                "MediaPipe Face Landmarker can tai model thu cong -- xem "
                "README.md trong src/detection/ de biet duong dan tai."
            )

        try:
            options = vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self._config.model_path),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=self._config.max_num_faces,
                min_face_detection_confidence=self._config.min_detection_confidence,
                min_face_presence_confidence=self._config.min_presence_confidence,
                min_tracking_confidence=self._config.min_tracking_confidence,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=self._config.output_transformation_matrix,
            )
            self._landmarker = vision.FaceLandmarker.create_from_options(options)
        except FaceLandmarkerError:
            raise
        except Exception as e:  # mediapipe co the nem nhieu loai loi C++ khac nhau
            raise FaceLandmarkerError(
                f"Khong khoi tao duoc MediaPipe FaceLandmarker tu model "
                f"'{self._config.model_path}': {e}"
            ) from e

        self._last_timestamp_ms = None
        logger.info(
            "Da nap Face Landmarker tu '%s' (max_num_faces=%d, output_matrix=%s).",
            self._config.model_path,
            self._config.max_num_faces,
            self._config.output_transformation_matrix,
        )

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __enter__(self) -> "FaceLandmarker":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Phat hien landmark
    # ------------------------------------------------------------------

    def detect(self, image, timestamp: float) -> List[FaceLandmarks]:
        """Phat hien landmark cho tung khuon mat trong 1 khung hinh.

        image: numpy array BGR (dung dinh dang tra ve tu Frame.image cua
               module capture/ -- OpenCV doc anh mac dinh la BGR).
        timestamp: giay (float, tu Frame.timestamp cua capture/).

        Tra ve danh sach FaceLandmarks (co the rong neu khong phat hien khuon
        mat nao), moi phan tu ung voi 1 khuon mat.
        """
        if self._landmarker is None:
            raise RuntimeError(
                "FaceLandmarker chua duoc mo. Goi open() truoc, hoac dung 'with'."
            )

        timestamp_ms = self._to_monotonic_ms(timestamp)

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        height, width = image.shape[:2]
        return self._parse_result(result, width, height)

    def _to_monotonic_ms(self, timestamp: float) -> int:
        """MediaPipe che do VIDEO yeu cau timestamp (ms) TANG DAN NGHIEM NGAT.
        Ham nay bao ve truong hop dong ho he thong lech nho hoac 2 frame den
        trung/lech thu tu (vi du do FrameBuffer drop frame) -- tranh MediaPipe
        nem loi 'timestamp must be monotonically increasing'."""
        timestamp_ms = int(timestamp * 1000)
        if self._last_timestamp_ms is not None and timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms

    @staticmethod
    def _parse_result(result, image_width: int, image_height: int) -> List[FaceLandmarks]:
        """Chuyen FaceLandmarkerResult cua MediaPipe sang danh sach FaceLandmarks.

        Luu y quan trong (giong FaceDetector): landmark tra ve la toa do CHUAN
        HOA (0.0-1.0), phai nhan voi image_width/image_height de doi ve pixel.

        result.facial_transformation_matrixes co the la danh sach RONG (neu
        output_facial_transformation_matrixes=False luc cau hinh) -- khong
        duoc gia dinh no luon co du phan tu tuong ung voi so khuon mat.
        """
        faces: List[FaceLandmarks] = []
        matrices = result.facial_transformation_matrixes or []

        for i, landmarks in enumerate(result.face_landmarks):
            points = [
                (int(lm.x * image_width), int(lm.y * image_height), lm.z)
                for lm in landmarks
            ]
            matrix = matrices[i] if i < len(matrices) else None
            faces.append(FaceLandmarks(points=points, transformation_matrix=matrix))

        return faces