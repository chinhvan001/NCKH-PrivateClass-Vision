"""Firestore gia trong RAM: test sync chay khong can credential, mang hay firebase_admin.

Chi mo phong phan API ma ``src.sync`` dung (``document(path)`` voi ``get/set/delete``,
``collection(path).on_snapshot``, ``batch()`` voi ``set/commit``) cung cac rang
buoc khien Firestore that tu choi ghi: toi da 500 write/batch, duong dan
document/collection dung so doan, gia tri encode duoc. Listener duoc goi dong bo
ngay khi ghi. Loi commit duoc tiem bang ``fail_next``.
"""

from __future__ import annotations

import copy
import datetime

_SCALARS = (type(None), bool, int, float, str, bytes, datetime.datetime)


class FakeFirestoreError(Exception):
    """Co ``code`` HTTP giong google.api_core.exceptions: 503 mang/server loi, 400 du lieu bi tu choi."""

    def __init__(self, code: int = 503, message: str = "fake firestore error") -> None:
        super().__init__(message)
        self.code = code


class FakeFirestore:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}
        self.commits: list[list[str]] = []  # duong dan document cua moi commit da ghi
        self._failures: list[tuple[Exception, bool]] = []
        self._listeners: list[tuple[str, object, FakeWatch]] = []

    def fail_next(self, error: Exception, *, after_write: bool = False) -> None:
        """Lan commit ke tiep nem ``error``; ``after_write=True``: server DA ghi
        nhung client van nhan loi (vd timeout sau khi commit thanh cong)."""
        self._failures.append((error, after_write))

    def document(self, path: str) -> "FakeDocument":
        _check_path(path, document=True)
        return FakeDocument(self, path)

    def collection(self, path: str) -> "FakeCollection":
        _check_path(path, document=False)
        return FakeCollection(self, path)

    def batch(self) -> "FakeWriteBatch":
        return FakeWriteBatch(self)

    def _write(self, writes: list[tuple[str, dict | None]]) -> None:
        """Ghi (data=None la xoa) roi bao cho listener cua collection bi anh huong."""
        for path, data in writes:
            if data is None:
                self.docs.pop(path, None)
            else:
                self.docs[path] = data
        changed = {path.rsplit("/", 1)[0] for path, _ in writes}
        for collection, callback, watch in list(self._listeners):
            if collection in changed and watch.is_active:
                callback(self._snapshots(collection), [], None)

    def _snapshots(self, collection: str) -> list["FakeSnapshot"]:
        return [
            FakeSnapshot(path.rsplit("/", 1)[1], data)
            for path, data in sorted(self.docs.items())
            if path.rsplit("/", 1)[0] == collection
        ]


class FakeSnapshot:
    def __init__(self, doc_id: str, data: dict | None) -> None:
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return copy.deepcopy(self._data)


class FakeDocument:
    def __init__(self, client: FakeFirestore, path: str) -> None:
        self._client = client
        self.path = path
        self.id = path.rsplit("/", 1)[1]

    def get(self, retry=None, timeout=None) -> FakeSnapshot:
        return FakeSnapshot(self.id, self._client.docs.get(self.path))

    def set(self, data: dict) -> None:
        _check_value(data)
        self._client._write([(self.path, copy.deepcopy(data))])

    def delete(self) -> None:
        self._client._write([(self.path, None)])


class FakeWatch:
    """Giong ``Watch`` that: ``is_active`` False khi listener da dung."""

    def __init__(self) -> None:
        self.is_active = True

    def unsubscribe(self) -> None:
        self.is_active = False


class FakeCollection:
    def __init__(self, client: FakeFirestore, path: str) -> None:
        self._client = client
        self.path = path

    def on_snapshot(self, callback) -> FakeWatch:
        """Nhu Firestore: goi ``callback(docs, changes, read_time)`` ngay voi snapshot dau tien."""
        watch = FakeWatch()
        self._client._listeners.append((self.path, callback, watch))
        callback(self._client._snapshots(self.path), [], None)
        return watch


class FakeWriteBatch:
    def __init__(self, client: FakeFirestore) -> None:
        self._client = client
        self._writes: list[tuple[str, dict]] = []

    def set(self, reference: FakeDocument, data: dict) -> None:
        _check_value(data)
        self._writes.append((reference.path, copy.deepcopy(data)))

    def commit(self, retry=None, timeout=None) -> None:
        if len(self._writes) > 500:
            raise FakeFirestoreError(400, "maximum 500 writes allowed per request")
        error, after_write = self._client._failures.pop(0) if self._client._failures else (None, False)
        if error is None or after_write:
            self._client._write(self._writes)
            self._client.commits.append([path for path, _ in self._writes])
        if error is not None:
            raise error


def _check_path(path: str, *, document: bool) -> None:
    """Document co so doan chan (collection/doc), collection co so doan le."""
    parts = path.split("/")
    if not all(parts) or (len(parts) % 2 == 0) != document:
        raise ValueError(f"Khong phai duong dan {'document' if document else 'collection'}: {path!r}")


def _check_value(value) -> None:
    """Nhu ``encode_value`` cua google-cloud-firestore: kieu la (vd numpy.int64) -> TypeError."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"Ten field phai la str: {key!r}")
            _check_value(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_value(item)
    elif not isinstance(value, _SCALARS):
        raise TypeError(f"Cannot convert to a Firestore Value: {type(value).__name__}")
