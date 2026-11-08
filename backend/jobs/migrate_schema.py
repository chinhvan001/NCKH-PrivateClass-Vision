"""Đưa dữ liệu Firestore về sơ đồ đã chốt (camera-ai/docs/backend_scoring_and_schema_proposal.md, phần 2).
Chạy từ thư mục backend/:

    python -m jobs.migrate_schema           # chỉ in các thay đổi sẽ làm (mặc định)
    python -m jobs.migrate_schema --apply   # ghi thật; sao lưu trước: gcloud firestore export gs://<bucket>/<ngày>

Chạy lại bao nhiêu lần cũng được: dữ liệu đã đúng thì không còn thay đổi nào. Không xóa collection cũ (app
Flutter vẫn đọc classes, students, enrollments, monitoring_sessions, classrooms) và không tự xóa dữ liệu cá nhân:
những mục cần nhóm quyết định chỉ được liệt kê. Kết quả in ra chỉ có ID document và tên field, không có giá trị.
"""

import argparse
from datetime import datetime

from firebase_admin import firestore
from firebase_config import db
from services.monitoring_service import MONITORED_STUDENTS, SCHOOL_TZ

DELETE = firestore.DELETE_FIELD
LEGACY_SESSION_FIELDS = ("aggregated_evaluation", "class_attention_score", "day_of_week")
MONITORED_FIELDS = ("student_id", "row", "column", "is_attention", "is_present", "attention_score", "note")
LEGACY_COLLECTIONS = ("classes", "students", "enrollments", "class_members", "monitoring_sessions", "classrooms")


def documents(collection):
    return {doc.id: doc.to_dict() or {} for doc in db.collection(collection).stream()}


def plan():
    """(thay đổi, cần xem xét): thay đổi là [(mô tả, hàm ghi)] theo đúng thứ tự phải ghi."""
    changes, review = [], []

    def change(description, write):
        changes.append((description, write))

    # Camera: trang camera cũ ghi classrooms, sơ đồ đã chốt dùng cameras/{camera_id}
    cameras = documents("cameras")
    for room_id, room in documents("classrooms").items():
        camera_id = str(room.get("camera_name") or "").strip()
        if camera_id and "/" not in camera_id and camera_id not in cameras:
            camera = {
                "camera_name": camera_id,
                "room_name": room.get("classroom_name", ""),
                "ip_address": room.get("ip_address", ""),
                "rtsp_port": str(room.get("rtsp_port") or ""),
            }
            cameras[camera_id] = camera
            change(f"cameras/{camera_id}: tạo từ classrooms/{room_id}", lambda c=camera_id, d=camera: _set("cameras", c, d))
    for camera_id, camera in cameras.items():
        fix = {"rtsp_url": DELETE} if "rtsp_url" in camera else {}  # URL kèm mật khẩu: chỉ ở camera_configs
        name = camera.get("camera_name")
        if isinstance(name, str) and name != name.strip():
            fix["camera_name"] = name.strip()
        if fix:
            change(f"cameras/{camera_id}: {', '.join(sorted(fix))}", lambda c=camera_id, f=fix: _update("cameras", c, f))

    # Lớp của camera: camera_configs/{camera}.class_id -> classes2/{lớp}.camera_id
    classes = documents("classes2")
    for camera_id, config in documents("camera_configs").items():
        class_id = config.get("class_id")
        if class_id is None:
            continue
        linked = classes.get(class_id, {}).get("camera_id")
        if class_id not in classes or linked not in (None, "", camera_id):
            review.append(f"camera_configs/{camera_id}.class_id: lớp {class_id} không tồn tại hoặc đã gắn camera khác")
            continue
        if linked != camera_id:
            classes[class_id]["camera_id"] = camera_id
            change(
                f"classes2/{class_id}.camera_id = {camera_id}",
                lambda c=class_id, v=camera_id: _update("classes2", c, {"camera_id": v}),
            )
        change(f"camera_configs/{camera_id}: bỏ class_id", lambda c=camera_id: _update("camera_configs", c, {"class_id": DELETE}))

    for class_id, data in classes.items():
        if "seatmap" in data:  # field rác cạnh seat_map
            change(f"classes2/{class_id}: bỏ seatmap", lambda c=class_id: _update("classes2", c, {"seatmap": DELETE}))
        if not data.get("class_name") or not (data.get("row_count") and data.get("column_count")):
            review.append(f"classes2/{class_id}: thiếu class_name hoặc row_count/column_count (sửa hoặc xóa lớp)")

    # Tiết: bỏ field cũ, ngày giờ dạng chuỗi như web ghi, monitored_students thành subcollection
    sessions = documents("sessions")
    for session_id, session in sessions.items():
        fix = {name: DELETE for name in LEGACY_SESSION_FIELDS if name in session}
        for name, pattern in (("session_date", "%Y-%m-%d"), ("start_time", "%H:%M"), ("end_time", "%H:%M")):
            if isinstance(session.get(name), datetime):
                fix[name] = session[name].astimezone(SCHOOL_TZ).strftime(pattern)
        roster = session.get("monitored_students")
        if isinstance(roster, dict):
            fix["monitored_students"] = DELETE
            for seat, info in roster.items():
                if isinstance(info, dict) and "/" not in seat:
                    data = {key: info[key] for key in MONITORED_FIELDS if key in info}
                    change(
                        f"sessions/{session_id}/{MONITORED_STUDENTS}/{seat}: từ map trong tiết",
                        lambda s=session_id, k=seat, d=data: _set(f"sessions/{s}/{MONITORED_STUDENTS}", k, d),
                    )
        if fix:
            change(f"sessions/{session_id}: {', '.join(sorted(fix))}", lambda s=session_id, f=fix: _update("sessions", s, f))

    # Bản chốt ghế kiểu cũ: session_rosters/{s} -> sessions/{s}/monitored_students/{ghế}
    for session_id, frozen in documents("session_rosters").items():
        seat_map = classes.get(frozen.get("class_id"), {}).get("seat_map") or {}
        for seat, student_id in (frozen.get("seats") or {}).items():
            place = seat_map.get(seat) or {}
            data = {"student_id": student_id, "row": place.get("row"), "column": place.get("column")}
            change(
                f"sessions/{session_id}/{MONITORED_STUDENTS}/{seat}: từ session_rosters",
                lambda s=session_id, k=seat, d=data: _set(f"sessions/{s}/{MONITORED_STUDENTS}", k, d),
            )
        marker = {key: frozen[key] for key in ("reports_at", "report_count") if key in frozen}
        if marker and session_id in sessions:
            change(f"sessions/{session_id}: {', '.join(sorted(marker))} từ session_rosters",
                   lambda s=session_id, m=marker: _update("sessions", s, m))
        change(f"session_rosters/{session_id}: xóa (đã chuyển)", lambda s=session_id: _delete("session_rosters", s))

    # Field rác: tên field là email (teachers), e-mail trùng email (parents). Ghi lại cả document vì tên
    # field có ký tự đặc biệt không cập nhật riêng được bằng update().
    for teacher_id, teacher in documents("teachers").items():
        junk = [key for key in teacher if "@" in key]
        if junk:
            clean = {key: value for key, value in teacher.items() if key not in junk}
            change(f"teachers/{teacher_id}: bỏ {len(junk)} field đặt tên bằng email",
                   lambda t=teacher_id, d=clean: _set("teachers", t, d))
    for parent_id, parent in documents("parents").items():
        if "e-mail" in parent:
            clean = {key: value for key, value in parent.items() if key != "e-mail"}
            clean["email"] = parent.get("email") or parent["e-mail"]
            change(f"parents/{parent_id}: gộp e-mail vào email", lambda p=parent_id, d=clean: _set("parents", p, d))
        if "birthday" in parent:
            review.append(f"parents/{parent_id}: có birthday, không có trong sơ đồ (nhóm quyết định xóa)")

    for student_id, student in documents("students2").items():
        active = student.get("is_active")
        if isinstance(active, str):
            if active.strip().lower() in ("true", "false"):
                value = active.strip().lower() == "true"
                change(f"students2/{student_id}: is_active chuỗi -> bool",
                       lambda s=student_id, v=value: _update("students2", s, {"is_active": v}))
            else:
                review.append(f"students2/{student_id}: is_active là chuỗi không rõ nghĩa")
        if isinstance(student.get("birthday"), str):
            review.append(f"students2/{student_id}: birthday dạng chuỗi (chọn một kiểu cho cả web và app)")
    with_gender = sum("gender" in student for student in documents("students2").values())
    if with_gender:
        review.append(f"students2: {with_gender} học sinh có gender, sơ đồ không có (checklist §3.13)")

    for name in LEGACY_COLLECTIONS:
        count = len(list(db.collection(name).select([]).stream()))
        if count:
            review.append(f"{name}: {count} document cũ, giữ đến khi app Flutter thôi đọc")
    return changes, review


def _set(collection, doc_id, data):
    db.collection(collection).document(doc_id).set(data)


def _update(collection, doc_id, data):
    db.collection(collection).document(doc_id).update(data)


def _delete(collection, doc_id):
    db.collection(collection).document(doc_id).delete()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Đưa dữ liệu Firestore về sơ đồ đã chốt.")
    parser.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ in kế hoạch)")
    args = parser.parse_args(argv)

    changes, review = plan()
    print(f"{len(changes)} thay đổi{'' if args.apply else ' (chưa ghi)'}:")
    for description, write in changes:
        print(f"  - {description}")
        if args.apply:
            write()
    print(f"{len(review)} mục cần nhóm quyết định (không tự sửa):")
    for item in review:
        print(f"  - {item}")
    if changes and not args.apply:
        print("Chạy lại với --apply để ghi. Sao lưu trước: gcloud firestore export gs://<bucket>/<ngày>.")


if __name__ == "__main__":
    main()
