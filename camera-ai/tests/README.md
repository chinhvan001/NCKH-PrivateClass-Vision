# Automated tests

CI runs all headless `test_*.py` tests, including
`test_end_to_end_pipeline.py`:

```text
simulated MP4 -> CameraCapture -> replayed pose -> SeatGrid/assign_seats
-> posture monitor + engagement score -> anonymized record
```

The test deliberately replaces neural-model inference with a deterministic
`ReplayPoseProvider`. This keeps CI repeatable and does not require GPU,
network access, model weights, webcam, or real student video. Model accuracy
is evaluated separately on an approved, local validation dataset.

`fake_firestore.py` is a helper, not a test. Its `FakeFirestore` replaces the
Firestore client in memory, so `test_firestore_sink.py` needs no credentials,
network access or `firebase_admin` (CI does not install it).

`smoke_test.py` is excluded because it opens a physical webcam. The legacy
facial `test_head_pose.py` is excluded because the privacy-preserving pipeline
does not expose facial-landmark APIs.
