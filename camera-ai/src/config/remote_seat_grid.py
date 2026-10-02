"""Nguon SeatGrid tu Firestore, chi giu config vo danh trong RAM."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import threading
import time

from src.seating import SeatGrid, SeatGridError

CAMERA_ANGLE_TYPES = frozenset({"frontal", "top_down"})


class RemoteSeatGridError(RuntimeError):
    pass


@dataclass(frozen=True)
class RemoteSeatGrid:
    camera_id: str
    classroom_id: str
    camera_angle_type: str
    config_version: int
    grid: SeatGrid
    pose: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: Any, *, expected_camera_id: str, expected_classroom_id: str) -> "RemoteSeatGrid":
        if not isinstance(payload, dict):
            raise RemoteSeatGridError("Firestore document phai la object.")
        required = {"schema_version", "config_version", "camera_id", "classroom_id", "camera_angle_type", "seats"}
        missing = required - set(payload)
        if missing:
            raise RemoteSeatGridError(f"Document thieu truong: {sorted(missing)}")
        if payload["schema_version"] != 1:
            raise RemoteSeatGridError("seat-grid schema_version phai la 1.")
        if payload["camera_id"] != expected_camera_id or payload["classroom_id"] != expected_classroom_id:
            raise RemoteSeatGridError("camera_id/classroom_id khong khop cau hinh local.")
        if payload["camera_angle_type"] not in CAMERA_ANGLE_TYPES:
            raise RemoteSeatGridError("camera_angle_type chi duoc la frontal hoac top_down.")
        if not isinstance(payload["config_version"], int) or payload["config_version"] < 1:
            raise RemoteSeatGridError("config_version phai la so nguyen >= 1.")
        try:
            grid = SeatGrid.from_dict({"seats": payload["seats"]}, source="Firestore seat grid")
        except SeatGridError as error:
            raise RemoteSeatGridError(str(error)) from error
        pose = payload.get("pose")
        if pose is not None and (
            not isinstance(pose, dict)
            or set(pose)
            != {"min_confidence", "iou_threshold", "image_size", "max_detections", "tile_size", "tile_overlap"}
        ):
            raise RemoteSeatGridError("pose phai co day du tham so runtime hop le.")
        return cls(
            expected_camera_id,
            expected_classroom_id,
            payload["camera_angle_type"],
            payload["config_version"],
            grid,
            pose,
        )


class DocumentReader(Protocol):
    def get(self, path: str) -> dict[str, Any] | None: ...


class FirestoreSeatGridSource:
    """Doc document Firestore; SDK duoc import muon de CI khong can credential."""

    def __init__(self, reader: DocumentReader | None = None) -> None:
        self._reader = reader

    def fetch(self, camera_id: str, classroom_id: str) -> RemoteSeatGrid:
        path = f"classrooms/{classroom_id}/camera_configs/{camera_id}"
        payload = self._reader.get(path) if self._reader else self._firebase_get(path)
        if payload is None:
            raise RemoteSeatGridError(f"Khong co document Firestore {path}.")
        return RemoteSeatGrid.from_dict(payload, expected_camera_id=camera_id, expected_classroom_id=classroom_id)

    @staticmethod
    def _firebase_get(path: str) -> dict[str, Any] | None:
        try:
            import firebase_admin
            from firebase_admin import firestore

            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            snapshot = firestore.client().document(path).get()
            return snapshot.to_dict() if snapshot.exists else None
        except Exception as error:
            raise RemoteSeatGridError(f"Khong doc duoc Firestore: {error}") from error


class SeatGridResolver:
    """Chi thay config neu version moi hon; khong ghi cache xuong dia."""

    def __init__(
        self,
        source: FirestoreSeatGridSource,
        camera_id: str,
        classroom_id: str,
        fallback_path: str | Path | None = None,
    ) -> None:
        self.source, self.camera_id, self.classroom_id = source, camera_id, classroom_id
        self.fallback_path = Path(fallback_path) if fallback_path else None
        self.current: RemoteSeatGrid | None = None

    def refresh(self) -> RemoteSeatGrid:
        try:
            incoming = self.source.fetch(self.camera_id, self.classroom_id)
            if self.current is None or incoming.config_version > self.current.config_version:
                self.current = incoming
            return self.current
        except RemoteSeatGridError:
            if self.current is not None:
                return self.current
            if self.fallback_path:
                return RemoteSeatGrid(
                    self.camera_id, self.classroom_id, "frontal", 0, SeatGrid.from_json_file(self.fallback_path)
                )
            raise


class RuntimeConfigPoller:
    """Polling Firestore va ap dung config moi an toan giua cac frame."""

    def __init__(self, resolver: SeatGridResolver, pose_detector: Any, interval_sec: float = 30.0) -> None:
        if interval_sec <= 0:
            raise ValueError("interval_sec phai > 0.")
        self.resolver, self.pose_detector, self.interval_sec = resolver, pose_detector, interval_sec
        self._lock, self._stop = threading.RLock(), threading.Event()
        self._thread: threading.Thread | None = None
        self._current: RemoteSeatGrid | None = None

    def refresh_once(self) -> RemoteSeatGrid:
        incoming = self.resolver.refresh()
        with self._lock:
            if self._current is None or incoming.config_version > self._current.config_version:
                if incoming.pose is not None:
                    self.pose_detector.apply_runtime_config(**incoming.pose)
                self._current = incoming
            return self._current

    def snapshot(self) -> RemoteSeatGrid:
        with self._lock:
            if self._current is None:
                return self.refresh_once()
            return self._current

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.refresh_once()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="seat-grid-poller", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.wait(self.interval_sec):
            try:
                self.refresh_once()
            except RemoteSeatGridError:
                pass  # resolver giu config cu; logging do host pipeline thuc hien
