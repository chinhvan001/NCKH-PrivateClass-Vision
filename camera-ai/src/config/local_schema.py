"""Schema JSON local cho mot pipeline camera an danh.

Schema co chu dich khong co ten hoc sinh, student ID, face model, embedding,
hay URL RTSP. Nguon camera duoc tham chieu bang ten bien moi truong de credential
khong nam trong file config co the bi commit/chia se. Toa do 4 ghe goc (vi tri
ghe tren anh) cung nam o day vi phu thuoc cach lap camera, khong dua len Firestore.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Optional, Union
from zoneinfo import ZoneInfo

from src.capture.config import CaptureConfig
from src.seating import CornerSeats

SCHEMA_VERSION = 2
_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")  # thu tu cua datetime.weekday()
_DAYS = set(_WEEKDAYS)
_CAMERA_ANGLE_TYPES = ("frontal", "top_down")
_CORNER_KEYS = ("first_row_first_column", "first_row_last_column", "last_row_last_column", "last_row_first_column")


class LocalConfigError(ValueError):
    """Config local sai schema, khong day du, hoac vi pham privacy policy."""


def _only_keys(data: dict, allowed: set[str], path: str) -> None:
    extra = set(data) - allowed
    if extra:
        raise LocalConfigError(f"{path} co truong khong duoc phep: {sorted(extra)}")


def _required(data: dict, names: set[str], path: str) -> None:
    missing = names - set(data)
    if missing:
        raise LocalConfigError(f"{path} thieu truong bat buoc: {sorted(missing)}")


def _unit(value: Any, path: str, *, allow_zero: bool = False) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise LocalConfigError(f"{path} phai la so.")
    value = float(value)
    if not (0 <= value <= 1 if allow_zero else 0 < value <= 1):
        raise LocalConfigError(f"{path} phai nam trong {'[0, 1]' if allow_zero else '(0, 1]'}.")
    return value


@dataclass(frozen=True)
class CameraLocalConfig:
    camera_id: str  # vd "Camera 201", ten document edge_nodes/{camera_id}
    class_id: str  # document classes/{class_id}: 1 lop = 1 phong = 1 camera
    source_env: str
    width: Optional[int]
    height: Optional[int]
    angle_type: str  # frontal | top_down; back-turn chi chay voi frontal


@dataclass(frozen=True)
class SeatingConfig:
    corner_seats: CornerSeats


@dataclass(frozen=True)
class SamplingConfig:
    capture_fps: float
    inference_every_n_frames: int


@dataclass(frozen=True)
class ThresholdConfig:
    pose_confidence: float
    iou_threshold: float
    image_size: int
    tile_size: Optional[int]
    tile_overlap: float
    max_detections: int
    conversation_duration_sec: float
    conversation_max_distance_px: float
    back_turn_duration_sec: float
    back_turn_max_face_visibility: float


@dataclass(frozen=True)
class ProcessingWindow:
    days: tuple[str, ...]
    start: str
    end: str


@dataclass(frozen=True)
class ScheduleConfig:
    timezone: str
    windows: tuple[ProcessingWindow, ...]

    def allows(self, moment: datetime) -> bool:
        """``moment`` (co tzinfo) co nam trong 1 cua so xu ly, theo gio dia phuong cua lop."""
        local = moment.astimezone(ZoneInfo(self.timezone))
        day, clock = _WEEKDAYS[local.weekday()], local.time()
        return any(
            day in window.days and time.fromisoformat(window.start) <= clock < time.fromisoformat(window.end)
            for window in self.windows
        )


@dataclass(frozen=True)
class PrivacyConfig:
    frame_buffer_size: int
    allow_persistent_output: bool
    retention_days: int  # expire_at cua document phien edge ghi; Firestore TTL xoa khi het han


@dataclass(frozen=True)
class LocalPipelineConfig:
    """Toan bo config duoc phep luu cuc bo cho mot camera/lop hoc."""

    schema_version: int
    camera: CameraLocalConfig
    seating: SeatingConfig
    sampling: SamplingConfig
    thresholds: ThresholdConfig
    schedule: ScheduleConfig
    privacy: PrivacyConfig

    @classmethod
    def from_json_file(cls, path: Union[str, Path]) -> "LocalPipelineConfig":
        file_path = Path(path)
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise LocalConfigError(f"Khong tim thay config: {file_path}") from error
        except json.JSONDecodeError as error:
            raise LocalConfigError(f"Config JSON khong hop le: {error}") from error
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Any) -> "LocalPipelineConfig":
        if not isinstance(data, dict):
            raise LocalConfigError("Config goc phai la JSON object.")
        sections = {"schema_version", "camera", "seating", "sampling", "thresholds", "schedule", "privacy"}
        _only_keys(data, sections, "root")
        _required(data, sections, "root")
        if data["schema_version"] != SCHEMA_VERSION:
            raise LocalConfigError(f"schema_version phai la {SCHEMA_VERSION}.")
        return cls(
            schema_version=SCHEMA_VERSION,
            camera=_parse_camera(data["camera"]),
            seating=_parse_seating(data["seating"]),
            sampling=_parse_sampling(data["sampling"]),
            thresholds=_parse_thresholds(data["thresholds"]),
            schedule=_parse_schedule(data["schedule"]),
            privacy=_parse_privacy(data["privacy"]),
        )

    def to_capture_config(self) -> CaptureConfig:
        """Chuyen sang config capture, chi doc source tu bien moi truong luc chay."""
        raw_source = os.getenv(self.camera.source_env)
        if not raw_source:
            raise LocalConfigError(
                f"Chua dat bien moi truong {self.camera.source_env!r} cho camera {self.camera.camera_id!r}."
            )
        try:
            source: Union[int, str] = int(raw_source)
        except ValueError:
            source = raw_source
        return CaptureConfig(
            source=source,
            width=self.camera.width,
            height=self.camera.height,
            target_fps=self.sampling.capture_fps,
        )


def _object(value: Any, path: str, keys: set[str]) -> dict:
    if not isinstance(value, dict):
        raise LocalConfigError(f"{path} phai la object.")
    _only_keys(value, keys, path)
    _required(value, keys, path)
    return value


def _parse_camera(value: Any) -> CameraLocalConfig:
    data = _object(value, "camera", {"camera_id", "class_id", "source_env", "width", "height", "angle_type"})
    for key in ("camera_id", "class_id", "source_env"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise LocalConfigError(f"camera.{key} phai la chuoi khong rong.")
    for key in ("camera_id", "class_id"):
        if "/" in data[key]:
            raise LocalConfigError(f"camera.{key} la ten document Firestore, khong duoc chua '/'.")
    if not data["source_env"].isidentifier():
        raise LocalConfigError("camera.source_env phai la ten bien moi truong hop le.")
    width, height = data["width"], data["height"]
    if (width is None) != (height is None):
        raise LocalConfigError("camera.width va camera.height phai cung dat hoac cung null.")
    if width is not None and (not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0):
        raise LocalConfigError("camera.width/height phai la so nguyen duong hoac null.")
    if data["angle_type"] not in _CAMERA_ANGLE_TYPES:
        raise LocalConfigError("camera.angle_type chi duoc la frontal hoac top_down.")
    return CameraLocalConfig(data["camera_id"], data["class_id"], data["source_env"], width, height, data["angle_type"])


def _parse_seating(value: Any) -> SeatingConfig:
    data = _object(value, "seating", {"corner_seats"})
    corners = _object(data["corner_seats"], "seating.corner_seats", set(_CORNER_KEYS))
    points = {}
    for key in _CORNER_KEYS:
        point = corners[key]
        if (
            not isinstance(point, list)
            or len(point) != 2
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in point)
        ):
            raise LocalConfigError(f"seating.corner_seats.{key} phai la [x, y] pixel >= 0.")
        points[key] = (float(point[0]), float(point[1]))
    return SeatingConfig(CornerSeats(**points))


def _parse_sampling(value: Any) -> SamplingConfig:
    data = _object(value, "sampling", {"capture_fps", "inference_every_n_frames"})
    if not isinstance(data["capture_fps"], (int, float)) or data["capture_fps"] <= 0:
        raise LocalConfigError("sampling.capture_fps phai > 0.")
    if not isinstance(data["inference_every_n_frames"], int) or data["inference_every_n_frames"] < 1:
        raise LocalConfigError("sampling.inference_every_n_frames phai la so nguyen >= 1.")
    return SamplingConfig(float(data["capture_fps"]), data["inference_every_n_frames"])


def _parse_thresholds(value: Any) -> ThresholdConfig:
    keys = {
        "pose_confidence",
        "iou_threshold",
        "image_size",
        "tile_size",
        "tile_overlap",
        "max_detections",
        "conversation_duration_sec",
        "conversation_max_distance_px",
        "back_turn_duration_sec",
        "back_turn_max_face_visibility",
    }
    data = _object(value, "thresholds", keys)
    for key in ("image_size", "max_detections"):
        if not isinstance(data[key], int) or data[key] <= 0:
            raise LocalConfigError(f"thresholds.{key} phai la so nguyen duong.")
    if data["tile_size"] is not None and (not isinstance(data["tile_size"], int) or data["tile_size"] <= 0):
        raise LocalConfigError("thresholds.tile_size phai la so nguyen duong hoac null.")
    for key in ("conversation_duration_sec", "conversation_max_distance_px", "back_turn_duration_sec"):
        if not isinstance(data[key], (int, float)) or data[key] <= 0:
            raise LocalConfigError(f"thresholds.{key} phai > 0.")
    return ThresholdConfig(
        _unit(data["pose_confidence"], "thresholds.pose_confidence"),
        _unit(data["iou_threshold"], "thresholds.iou_threshold"),
        data["image_size"],
        data["tile_size"],
        _unit(data["tile_overlap"], "thresholds.tile_overlap", allow_zero=True),
        data["max_detections"],
        float(data["conversation_duration_sec"]),
        float(data["conversation_max_distance_px"]),
        float(data["back_turn_duration_sec"]),
        _unit(data["back_turn_max_face_visibility"], "thresholds.back_turn_max_face_visibility", allow_zero=True),
    )


def _parse_schedule(value: Any) -> ScheduleConfig:
    if not isinstance(value, dict):
        raise LocalConfigError("schedule phai la object.")
    _only_keys(value, {"timezone", "windows"}, "schedule")
    _required(value, {"timezone", "windows"}, "schedule")
    if not isinstance(value["timezone"], str) or not value["timezone"].strip():
        raise LocalConfigError("schedule.timezone phai la chuoi khong rong.")
    try:
        ZoneInfo(value["timezone"])
    except (KeyError, ValueError) as error:  # ZoneInfoNotFoundError la KeyError
        raise LocalConfigError(f"schedule.timezone khong phai ten IANA hop le: {value['timezone']!r}") from error
    if not isinstance(value["windows"], list) or not value["windows"]:
        raise LocalConfigError("schedule.windows phai la danh sach khong rong.")
    windows = []
    for index, item in enumerate(value["windows"]):
        data = _object(item, f"schedule.windows[{index}]", {"days", "start", "end"})
        if not isinstance(data["days"], list) or not data["days"] or set(data["days"]) - _DAYS:
            raise LocalConfigError(f"schedule.windows[{index}].days phai dung mon..sun.")
        try:
            start, end = time.fromisoformat(data["start"]), time.fromisoformat(data["end"])
        except (TypeError, ValueError) as error:
            raise LocalConfigError(f"schedule.windows[{index}] start/end phai dang HH:MM.") from error
        if start >= end:
            raise LocalConfigError("Lich qua dem chua duoc ho tro; end phai sau start.")
        windows.append(ProcessingWindow(tuple(data["days"]), data["start"], data["end"]))
    return ScheduleConfig(value["timezone"], tuple(windows))


def _parse_privacy(value: Any) -> PrivacyConfig:
    data = _object(value, "privacy", {"frame_buffer_size", "allow_persistent_output", "retention_days"})
    if data["frame_buffer_size"] != 1:
        raise LocalConfigError("privacy.frame_buffer_size phai la 1 de chi giu mot frame trong RAM.")
    if data["allow_persistent_output"] is not False:
        raise LocalConfigError("privacy.allow_persistent_output phai la false trong config production.")
    retention = data["retention_days"]
    if not isinstance(retention, int) or isinstance(retention, bool) or retention < 1:
        raise LocalConfigError("privacy.retention_days phai la so nguyen >= 1.")
    return PrivacyConfig(frame_buffer_size=1, allow_persistent_output=False, retention_days=retention)
