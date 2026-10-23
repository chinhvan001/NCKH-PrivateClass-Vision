import { useEffect, useState } from "react";
import Icon from "../common/Icon";

const EditTeacherForm = ({ teacher, onClose, onSave }) => {
    const [name, setName] = useState("");
    const [phoneNumber, setPhoneNumber] = useState("");
    const [subject, setSubject] = useState("");
    const [isActive, setIsActive] = useState(true);
    const [saving, setSaving] = useState(false);

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

        setSubject(
            typeof teacher.subject === "string"
                ? teacher.subject
                : ""
        );

        setIsActive(teacher.is_active !== false);
    }, [teacher]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!name.trim()) {
            alert("Vui lòng nhập họ tên giáo viên.");
            return;
        }

        if (!subject) {
            alert("Vui lòng chọn bộ môn.");
            return;
        }

        try {
            setSaving(true);

            await onSave?.({
                uid: teacher.uid || teacher.id,
                name: name.trim(),
                phone_number: phoneNumber.trim(),
                subject: subject,
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

                    <div className="edit-teacher-field">
                        <label htmlFor="teacher-subject">
                            Bộ môn
                        </label>

                        <select
                            id="teacher-subject"
                            value={subject}
                            onChange={(e) =>
                                setSubject(e.target.value)
                            }
                            disabled={saving}
                        >
                            <option value="">
                                Chọn bộ môn
                            </option>

                            {availableSubjects.map((item) => (
                                <option
                                    key={item}
                                    value={item}
                                >
                                    {item}
                                </option>
                            ))}
                        </select>

                        <small>
                            Chọn bộ môn giảng dạy của giáo viên.
                        </small>
                    </div>

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