"""
seat_grid.py -- Module seating/: dinh nghia luoi cho ngoi (seat grid) va co
che calibration, phuc vu Pseudonymous Spatial Seating Mapping.

Day la thanh phan HOAN TOAN MOI trong kien truc pivot skeleton/pose-based
(xem Algorithm-Pivot-Proposal.docx, 04/09/2026) -- thay the vai tro "nhan
dien" ma truoc day du dinh dung facial landmark dam nhiem mot phan: thay vi
nhan dien DANH TINH hoc sinh, he thong chi nhan dien VI TRI CHO NGOI, dung
seat_id lam dinh danh (khong gan voi ca nhan cu the).

Vi tri ghe co 3 nguon: file calibration JSON cuc bo (demo), 4 ghe goc trong
config edge (seat_layout.py), hoac o chu nhat admin ve tren trang Quan ly
camera cua web (Firestore seat_regions/{camera_id}, config/class_layout.py).
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union


@dataclass
class Seat:
    """Mot vi tri cho ngoi da hieu chinh (calibrate) trong khung hinh camera.

    seat_id: dinh danh ghe, VI DU "A1", "row2_col3" -- khong gan voi hoc sinh
        cu the nao, chi la toa do vat ly trong phong hoc (dung tinh than
        Pseudonymous Spatial Tracking cua Proposal chinh thuc).
    center_x, center_y: toa do TRUNG TAM cua ghe trong khung hinh camera,
        don vi pixel (theo dung he toa do cua anh dau vao pipeline capture/).
    region: o (x1, y1, x2, y2) pixel cua ghe; co o thi chi nguoi co trung diem
        vai nam trong o moi duoc gan vao ghe. None: chi dung tam ghe.
    """

    seat_id: str
    center_x: float
    center_y: float
    region: Optional[Tuple[float, float, float, float]] = None

    def contains(self, x: float, y: float) -> bool:
        if self.region is None:
            return True
        x1, y1, x2, y2 = self.region
        return x1 <= x <= x2 and y1 <= y <= y2


class SeatGridError(ValueError):
    """Nem ra khi file calibration seat grid khong hop le (thieu truong,
    trung seat_id, sai dinh dang JSON...)."""


@dataclass
class SeatGrid:
    """Toan bo luoi cho ngoi cua MOT lop hoc/MOT goc camera cu the.

    Luu y quan trong: SeatGrid gan voi MOT cach lap dat camera cu the (goc
    quay, vi tri) -- neu camera bi dich chuyen hoac lap lai o goc khac, can
    calibrate lai tu dau (tao SeatGrid moi), khong the dung chung.

    image_size: (rong, cao) cua anh dung de ve toa do (o ve tren anh chup tu
        camera); None: toa do da theo dung khung hinh pipeline.
    """

    seats: List[Seat]
    image_size: Optional[Tuple[int, int]] = None

    def __post_init__(self):
        seat_ids = [s.seat_id for s in self.seats]
        if len(seat_ids) != len(set(seat_ids)):
            duplicates = {sid for sid in seat_ids if seat_ids.count(sid) > 1}
            raise SeatGridError(f"seat_id bi trung lap trong SeatGrid: {duplicates}")

    @classmethod
    def from_json_file(cls, path: Union[str, Path]) -> "SeatGrid":
        """Doc file calibration JSON cuc bo, dinh dang:

            {
              "seats": [
                {"seat_id": "A1", "center_x": 120, "center_y": 340},
                {"seat_id": "A2", "center_x": 260, "center_y": 340}
              ]
            }

        Nem SeatGridError neu file khong ton tai, sai dinh dang JSON, thieu
        truong bat buoc, hoac co seat_id trung lap.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise SeatGridError(
                f"Khong tim thay file calibration seat grid tai '{file_path}'. "
                "Can chay buoc calibration truoc (xac dinh vi tri tung ghe "
                "trong khung hinh camera) va luu thanh file JSON dung dinh dang."
            )

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SeatGridError(f"File '{file_path}' khong phai JSON hop le: {e}") from e

        return cls.from_dict(raw, source=f"File '{file_path}'")

    @classmethod
    def from_dict(cls, raw: object, *, source: str = "SeatGrid") -> "SeatGrid":
        """Tao grid tu payload da duoc nap trong RAM (vi du Firestore)."""
        if not isinstance(raw, dict) or "seats" not in raw or not isinstance(raw["seats"], list):
            raise SeatGridError(f"{source} thieu truong 'seats' (danh sach).")

        seats = []
        for i, item in enumerate(raw["seats"]):
            missing = {"seat_id", "center_x", "center_y"} - set(item.keys())
            if missing:
                raise SeatGridError(f"Phan tu thu {i} trong 'seats' thieu truong bat buoc: {missing}")
            seats.append(
                Seat(
                    seat_id=str(item["seat_id"]),
                    center_x=float(item["center_x"]),
                    center_y=float(item["center_y"]),
                )
            )

        return cls(seats=seats)

    def to_json_file(self, path: Union[str, Path]) -> None:
        """Ghi SeatGrid hien tai ra file JSON (huu ich khi tao calibration
        bang code/script rieng thay vi viet tay file JSON)."""
        data = {"seats": [{"seat_id": s.seat_id, "center_x": s.center_x, "center_y": s.center_y} for s in self.seats]}
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def find_nearest_seat(self, x: float, y: float) -> Optional[Seat]:
        """Tim seat co trung tam GAN NHAT voi toa do (x, y) cho truoc, theo
        khoang cach Euclid, trong cac seat co o chua diem do. Tra ve None neu
        SeatGrid rong (chua calibrate) hoac diem nam ngoai moi o."""
        seats = [s for s in self.seats if s.contains(x, y)]
        if not seats:
            return None
        return min(seats, key=lambda s: _distance(s.center_x, s.center_y, x, y))

    def fit_to(self, width: int, height: int) -> None:
        """Doi toa do ve khung hinh (width, height) khi anh dung de ve co do phan
        giai khac (cung goc camera). Khong lam gi neu da khop hoac khong co image_size."""
        if self.image_size is None or self.image_size == (width, height):
            return
        sx, sy = width / self.image_size[0], height / self.image_size[1]
        self.seats = [
            Seat(
                s.seat_id,
                s.center_x * sx,
                s.center_y * sy,
                None if s.region is None else (s.region[0] * sx, s.region[1] * sy, s.region[2] * sx, s.region[3] * sy),
            )
            for s in self.seats
        ]
        self.image_size = (width, height)

    def get_seat(self, seat_id: str) -> Optional[Seat]:
        """Tim seat theo seat_id. Tra ve None neu khong ton tai."""
        return next((s for s in self.seats if s.seat_id == seat_id), None)

    def distance_to(self, seat: Seat, x: float, y: float) -> float:
        return _distance(seat.center_x, seat.center_y, x, y)


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x1 - x2, y1 - y2)
