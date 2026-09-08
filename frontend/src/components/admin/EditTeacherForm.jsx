import { useEffect, useState } from "react";

import Icon from "../common/Icon";

const EditTeacherForm = ({ teacher, onClose, onSave }) => {
  const [name, setName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);

  const [selectedSubject, setSelectedSubject] = useState("");

  const availableSubjects = [
    "Ngữ văn",
    "Toán",
    "Tiếng Anh",
    "Lịch sử",
    "Vật lý",
    "Hóa học",
    "Sinh học",
    "Tin học",
    "Giáo dục kinh tế và pháp luật",
    "Âm nhạc",
    "Mỹ thuật",
  ];

  useEffect(() => {
    if (!teacher) return;

    setName(teacher.name || "");

    setPhoneNumber(teacher.phone_number || "");

    setSubjects(
      Array.isArray(teacher.subject)
        ? teacher.subject
        : []
    );

    setIsActive(teacher.is_active !== false);

    setSelectedSubject("");
  }, [teacher]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name.trim()) {
      alert("Vui lòng nhập họ tên giáo viên.");
      return;
    }

    try {
      setSaving(true);

      await onSave?.({
        uid: teacher.uid || teacher.id,
        name: name.trim(),
        phone_number: phoneNumber.trim(),
        subject: subjects,
        is_active: isActive,
      });
    } catch (error) {
      console.error("Update teacher error:", error);
      alert("Cập nhật tài khoản thất bại.");
    } finally {
      setSaving(false);
    }
  };

  if (!teacher) {
    return null;
  }

  const handleAddSubject = () => {
    if (!selectedSubject) {
      return;
    }

    if (subjects.includes(selectedSubject)) {
      alert("Môn học này đã được thêm.");
      return;
    }

    setSubjects((prev) => [
      ...prev,
      selectedSubject,
    ]);

    setSelectedSubject("");
  };

  const handleRemoveSubject = (subjectToRemove) => {
    setSubjects((prev) =>
      prev.filter(
        (subject) => subject !== subjectToRemove
      )
    );
  };

  return (
    <div className="edit-teacher-overlay">
      <div className="edit-teacher-modal">

        <div className="edit-teacher-header">
          <div>
            <h2>Chỉnh sửa tài khoản</h2>
            <p>
              Cập nhật thông tin tài khoản giáo viên.
            </p>
          </div>

          <button
            type="button"
            className="edit-teacher-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Đóng"
          >
            ×
          </button>
        </div>

        <form
          className="edit-teacher-form"
          onSubmit={handleSubmit}
        >

          {/* Họ và tên */}
          <div className="edit-teacher-field">
            <label htmlFor="teacher-name">
              Họ và tên
            </label>

            <input
              id="teacher-name"
              type="text"
              value={name}
              onChange={(e) =>
                setName(e.target.value)
              }
              placeholder="Nhập họ và tên"
              disabled={saving}
            />
          </div>

          {/* Gmail */}
          <div className="edit-teacher-field">
            <label htmlFor="teacher-email">
              Gmail
            </label>

            <input
              id="teacher-email"
              type="email"
              value={teacher.email || ""}
              disabled
            />

            <small>
              Gmail được liên kết với tài khoản và
              không thể chỉnh sửa tại đây.
            </small>
          </div>

          {/* Số điện thoại */}
          <div className="edit-teacher-field">
            <label htmlFor="teacher-phone">
              Số điện thoại
            </label>

            <input
              id="teacher-phone"
              type="tel"
              value={phoneNumber}
              onChange={(e) =>
                setPhoneNumber(e.target.value)
              }
              placeholder="Nhập số điện thoại"
              disabled={saving}
            />
          </div>

          {/* Bộ môn */}
          <div className="edit-teacher-field">
            <label>Bộ môn</label>

            <div className="edit-teacher-subjects">
              {subjects.length > 0 ? (
                subjects.map((subject) => (
                  <div
                    key={subject}
                    className="edit-teacher-subject-tag"
                  >
                    <span>{subject}</span>

                    <button
                      type="button"
                      onClick={() =>
                        handleRemoveSubject(subject)
                      }
                      disabled={saving}
                      aria-label={`Xóa môn ${subject}`}
                    >
                      ×
                    </button>
                  </div>
                ))
              ) : (
                <span className="edit-teacher-no-subject">
                  Chưa có môn học
                </span>
              )}
            </div>

            <div className="edit-teacher-add-subject">
              <select
                value={selectedSubject}
                onChange={(e) =>
                  setSelectedSubject(
                    e.target.value
                  )
                }
                disabled={saving}
              >
                <option value="">
                  Chọn môn học
                </option>

                {availableSubjects
                  .filter(
                    (subject) =>
                      !subjects.includes(subject)
                  )
                  .map((subject) => (
                    <option
                      key={subject}
                      value={subject}
                    >
                      {subject}
                    </option>
                  ))}
              </select>

              <button
                type="button"
                onClick={handleAddSubject}
                disabled={
                  saving || !selectedSubject
                }
                className="edit-teacher-add-subject-button"
              >
                <Icon name="plus" size={16} />

                <span>Thêm môn</span>
              </button>
            </div>

            <small>
              Có thể thêm nhiều môn học cho giáo viên.
            </small>
          </div>

          {/* Trạng thái */}
          <div className="edit-teacher-field">
            <label>Trạng thái tài khoản</label>

            <label className="edit-teacher-status">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) =>
                  setIsActive(
                    e.target.checked
                  )
                }
                disabled={saving}
              />

              <span>
                {isActive
                  ? "Đang hoạt động"
                  : "Đã vô hiệu hóa"}
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="edit-teacher-actions">
            <button
              type="button"
              className="edit-teacher-cancel"
              onClick={onClose}
              disabled={saving}
            >
              Hủy
            </button>

            <button
              type="submit"
              className="edit-teacher-save"
              disabled={saving}
            >
              {saving ? (
                "Đang lưu..."
              ) : (
                <>
                  <Icon
                    name="checkCircle"
                    size={17}
                  />

                  <span>
                    Lưu thay đổi
                  </span>
                </>
              )}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};

export default EditTeacherForm;