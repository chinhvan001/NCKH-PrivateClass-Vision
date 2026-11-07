"""FakeFirestore (dung cho backend/tests) tu choi nhu Firestore that: duong dan sai, gia tri khong encode
duoc, qua 500 write/batch."""

import numpy as np
import pytest

from fake_firestore import FakeFirestore, FakeFirestoreError


def test_fake_firestore_rejects_what_real_firestore_rejects():
    client = FakeFirestore()
    with pytest.raises(ValueError):
        client.document("classes/class-1/seats")  # collection, khong phai document
    with pytest.raises(ValueError):
        client.collection("classes/class-1")  # document, khong phai collection
    batch = client.batch()
    with pytest.raises(TypeError):
        batch.set(client.document("a/b"), {"count": np.int64(3)})
    for index in range(501):
        batch.set(client.document(f"a/{index}"), {})
    with pytest.raises(FakeFirestoreError) as error:
        batch.commit()
    assert error.value.code == 400
