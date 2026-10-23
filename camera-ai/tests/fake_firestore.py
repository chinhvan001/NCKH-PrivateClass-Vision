"""Firestore gia trong RAM: test sync va backend web chay khong can credential, mang hay firebase_admin.

Chi mo phong phan API ma ``src.sync``, ``src.config`` va backend web (``backend/tests``) dung:
``document(path)`` voi ``get(field_paths=...)/set/update/delete/collection``,
``collection(path)`` voi ``document()`` (id tu sinh), ``add``, ``where(field, "==", value)``,
``select(fields)``, ``order_by``, ``limit``, ``stream()`` va ``on_snapshot``, ``batch()`` voi
``set/commit``; cung cac rang buoc khien Firestore that tu choi ghi: toi da 500 write/batch,
duong dan document/collection dung so doan, gia tri encode duoc, ``update`` document chua co.
``field_paths``/``select`` chi tra cac field duoc chon, nhu Firestore that. ``SERVER_TIMESTAMP``
thanh gio UTC luc ghi, ``DELETE_FIELD`` xoa field trong ``update``. Listener duoc goi dong bo
ngay khi ghi. Loi commit duoc tiem bang ``fail_next``.
"""

from __future__ import annotations

import copy
import datetime
import uuid

_SCALARS = (type(None), bool, int, float, str, bytes, datetime.datetime)


class _Sentinel:
    """Giong ``firestore.SERVER_TIMESTAMP``/``DELETE_FIELD``: gia tri dac biet server thay khi ghi."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __deepcopy__(self, memo) -> "_Sentinel":
        return self  # van so sanh duoc bang ``is`` sau khi copy


SERVER_TIMESTAMP = _Sentinel("SERVER_TIMESTAMP")
DELETE_FIELD = _Sentinel("DELETE_FIELD")


class FakeFirestoreError(Exception):
    """Co ``code`` HTTP giong google.api_core.exceptions: 503 mang/server loi, 400 du lieu bi tu choi."""

    def __init__(self, code: int = 503, message: str = "fake firestore error") -> None:
        super().__init__(message)
        self.code = code


class FakeFirestore:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}
        self.commits: list[list[str]] = []  # duong dan document cua moi commit da ghi
        self.reads: list[dict] = []  # du lieu client nhan duoc qua get()/stream(), sau projection
        self._failures: list[tuple[Exception, bool]] = []
        self._listeners: list[tuple[FakeCollection, object, FakeWatch]] = []

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
        for query, callback, watch in list(self._listeners):
            if query.path in changed and watch.is_active:
                callback(query._snapshots(), [], None)

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

    def get(self, field_paths=None, retry=None, timeout=None) -> FakeSnapshot:
        data = _project(self._client.docs.get(self.path), field_paths)
        if data is not None:
            self._client.reads.append(copy.deepcopy(data))
        return FakeSnapshot(self.id, data)

    def set(self, data: dict) -> None:
        self._client._write([(self.path, _stored(data))])

    def update(self, data: dict) -> None:
        """Chi doi field top-level duoc gui; document chua co -> loi 404 nhu Firestore that."""
        current = self._client.docs.get(self.path)
        if current is None:
            raise FakeFirestoreError(404, f"No document to update: {self.path}")
        if any("." in key for key in data):
            raise NotImplementedError("FakeFirestore khong ho tro field path co dau cham.")
        merged = {**current, **data}
        self._client._write([(self.path, _stored({k: v for k, v in merged.items() if v is not DELETE_FIELD}))])

    def delete(self) -> None:
        self._client._write([(self.path, None)])

    def collection(self, name: str) -> "FakeCollection":
        return self._client.collection(f"{self.path}/{name}")


class FakeWatch:
    """Giong ``Watch`` that: ``is_active`` False khi listener da dung."""

    def __init__(self) -> None:
        self.is_active = True

    def unsubscribe(self) -> None:
        self.is_active = False


class FakeCollection:
    """Collection, hoac query tren no (giong ``Query`` that, moi ham loc tra ve ban moi)."""

    def __init__(self, client: FakeFirestore, path: str) -> None:
        self._client = client
        self.path = path
        self._filters: tuple = ()
        self._fields = None
        self._order: tuple[str, bool] | None = None  # (field, giam dan)
        self._limit: int | None = None

    def _with(self, **changes) -> "FakeCollection":
        query = copy.copy(self)
        query.__dict__.update(changes)
        return query

    def document(self, doc_id: str | None = None) -> FakeDocument:
        """Khong co ``doc_id``: id ngau nhien 20 ky tu nhu Firestore."""
        return self._client.document(f"{self.path}/{doc_id or uuid.uuid4().hex[:20]}")

    def add(self, data: dict) -> tuple[None, FakeDocument]:
        reference = self.document()
        reference.set(data)
        return None, reference

    def where(self, field: str, op: str, value) -> "FakeCollection":
        if op != "==":
            raise NotImplementedError(f"FakeFirestore chi ho tro '==', khong ho tro {op!r}.")
        return self._with(_filters=self._filters + ((field, value),))

    def select(self, field_paths) -> "FakeCollection":
        return self._with(_fields=list(field_paths))

    def order_by(self, field: str, direction: str = "ASCENDING") -> "FakeCollection":
        return self._with(_order=(field, direction == "DESCENDING"))

    def limit(self, count: int) -> "FakeCollection":
        return self._with(_limit=count)

    def stream(self, retry=None, timeout=None):
        snapshots = self._snapshots()
        self._client.reads += [snapshot.to_dict() for snapshot in snapshots]
        return iter(snapshots)

    def on_snapshot(self, callback) -> FakeWatch:
        """Nhu Firestore: goi ``callback(docs, changes, read_time)`` ngay voi snapshot dau tien."""
        watch = FakeWatch()
        self._client._listeners.append((self, callback, watch))
        callback(self._snapshots(), [], None)
        return watch

    def _snapshots(self) -> list[FakeSnapshot]:
        matches = [
            snapshot
            for snapshot in self._client._snapshots(self.path)
            if all(snapshot._data.get(field) == value for field, value in self._filters)
        ]
        if self._order is not None:  # nhu Firestore: document thieu field sap xep bi bo
            field, descending = self._order
            matches = sorted(
                (snapshot for snapshot in matches if field in snapshot._data),
                key=lambda snapshot: snapshot._data[field],
                reverse=descending,
            )
        return [FakeSnapshot(item.id, _project(item._data, self._fields)) for item in matches[: self._limit]]


class FakeWriteBatch:
    def __init__(self, client: FakeFirestore) -> None:
        self._client = client
        self._writes: list[tuple[str, dict]] = []

    def set(self, reference: FakeDocument, data: dict) -> None:
        self._writes.append((reference.path, _stored(data)))

    def commit(self, retry=None, timeout=None) -> None:
        if len(self._writes) > 500:
            raise FakeFirestoreError(400, "maximum 500 writes allowed per request")
        error, after_write = self._client._failures.pop(0) if self._client._failures else (None, False)
        if error is None or after_write:
            self._client._write(self._writes)
            self._client.commits.append([path for path, _ in self._writes])
        if error is not None:
            raise error


def _stored(data: dict) -> dict:
    """Ban server luu: copy, ``SERVER_TIMESTAMP`` -> gio UTC luc ghi, roi kiem tra encode duoc."""
    now = datetime.datetime.now(datetime.timezone.utc)

    def resolve(value):
        if value is SERVER_TIMESTAMP:
            return now
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [resolve(item) for item in value]
        return value

    data = resolve(copy.deepcopy(data))
    _check_value(data)
    return data


def _project(data: dict | None, field_paths) -> dict | None:
    """Chi giu cac field top-level duoc chon (``None``: lay het), nhu projection cua Firestore."""
    if data is None or field_paths is None:
        return data
    wanted = set(field_paths)
    return {key: value for key, value in data.items() if key in wanted}


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
