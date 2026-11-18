"""Gắn tài khoản app cho dữ liệu đã có: giáo viên chưa có uid và học sinh có parent_email chưa có parent_id.

App giáo viên/phụ huynh tìm tài khoản theo teachers/{uid} và parents/{uid} (uid Firebase Auth). Giáo viên tạo
trên web trước bản vá này nằm ở teachers/{id tự sinh}: job chuyển document sang teachers/{uid}, sửa teacher_id
trong classes2 và sessions, rồi xóa document cũ. Mặc định chỉ in ra, --apply mới ghi.

    cd backend; python -m jobs.link_accounts [--apply]
"""

import argparse

from repositories.student_repository import StudentRepository
from routes.test_helpers import account_uid, commit_writes, db


def plan():
    """[(mô tả, hàm ghi)] cho mọi tài khoản cần gắn. Chỉ đọc: tài khoản Firebase Auth chỉ tìm/tạo lúc ghi."""
    changes = []
    for doc in db.collection("teachers").stream():
        teacher = doc.to_dict() or {}
        if teacher.get("uid"):
            continue
        if not teacher.get("email"):
            print(f"teachers/{doc.id}: không có email, bỏ qua")
            continue
        changes.append((f"teachers/{doc.id} -> teachers/{{uid Firebase Auth}} ({teacher['email']})", lambda d=doc: _move_teacher(d)))
    for doc in db.collection("students2").stream():
        student = doc.to_dict() or {}
        if student.get("parent_id") or not student.get("parent_email"):
            continue
        changes.append((
            f"students2/{doc.id}: liên kết phụ huynh {student['parent_email']}",
            lambda d=doc: StudentRepository.update_student(d.id, {"parent_email": (d.to_dict() or {})["parent_email"]}),
        ))
    return changes


def _move_teacher(doc):
    teacher = doc.to_dict() or {}
    uid = account_uid(teacher.get("email"), teacher.get("name", ""))
    if not uid:
        print(f"teachers/{doc.id}: lỗi Firebase Auth, bỏ qua")
        return
    teacher["uid"] = uid
    writes = [(db.collection("teachers").document(uid), teacher)]
    for collection in ("classes2", "sessions"):
        for item in db.collection(collection).where("teacher_id", "==", doc.id).stream():
            writes.append((db.collection(collection).document(item.id), {**(item.to_dict() or {}), "teacher_id": uid}))
    commit_writes(writes)
    if doc.id != uid:
        db.collection("teachers").document(doc.id).delete()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gắn uid Firebase Auth cho giáo viên và phụ huynh đã có.")
    parser.add_argument("--apply", action="store_true", help="ghi thay đổi (mặc định chỉ in ra)")
    args = parser.parse_args(argv)
    changes = plan()
    for description, _ in changes:
        print(description)
    if not args.apply:
        print(f"{len(changes)} thay đổi, chưa ghi (thêm --apply).")
        return
    for _, write in changes:
        write()
    print(f"Đã ghi {len(changes)} thay đổi.")


if __name__ == "__main__":
    main()
