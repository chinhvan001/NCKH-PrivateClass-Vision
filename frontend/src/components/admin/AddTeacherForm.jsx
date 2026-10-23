import { useState } from "react";

const AddTeacherForm = ({ onClose, onSave }) => {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [phoneNumber, setPhoneNumber] = useState("");
    const [subject, setSubject] = useState("");
    const [hasChildAtSchool, setHasChildAtSchool] = useState(false);
    const [isActive, setIsActive] = useState(true);

    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const availableSubjects = [
        "Toán",
        "Ngữ văn",
        "Tiếng Anh",
        "Vật lý",
        "Hóa học",
        "Sinh học",
        "Lịch sử",
        "Địa lý",
        "Giáo dục kinh tế và pháp luật",
        "Tin học",
        "Công nghệ",
        "Âm nhạc",
        "Mỹ thuật",
        "Thể dục",
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");

        if (!name.trim()) {
            setError("Họ và tên không được để trống.");
            return;
        }

        if (!email.trim()) {
            setError("Email không được để trống.");
            return;
        }

        if (!subject) {
            setError("Vui lòng chọn bộ môn.");
            return;
        }

        try {
            setSaving(true);

            const newTeacher = {
                name: name.trim(),
                email: email.trim().toLowerCase(),
                phone_number: phoneNumber.trim(),
                subject,
                role: hasChildAtSchool
                    ? ["teacher", "parent"]
                    : ["teacher"],
                is_active: isActive,
            };

            await onSave(newTeacher);

        } catch (error) {
            console.error("Add teacher error:", error);
            setError(
                error.message ||
                "Không thể thêm tài khoản giáo viên."
            );
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="edit-teacher-overlay">
            <div className="edit-teacher-modal">

                <div className="edit-teacher-header">
                    <div>
                        <h2>Thêm giáo viên</h2>
                        <p>
                            Tạo tài khoản giáo viên mới trong hệ thống.
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
                            value={email}
                            onChange={(e) =>
                                setEmail(e.target.value)
                            }
                            placeholder="Nhập Gmail"
                            disabled={saving}
                        />
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
                    </div>

                    <div className="edit-teacher-field">
                        <label htmlFor="teacher-parent-role">
                            Giáo viên có con học tại trường?
                        </label>

                        <select
                            id="teacher-parent-role"
                            value={
                                hasChildAtSchool
                                    ? "yes"
                                    : "no"
                            }
                            onChange={(e) =>
                                setHasChildAtSchool(
                                    e.target.value === "yes"
                                )
                            }
                            disabled={saving}
                        >
                            <option value="no">
                                Không
                            </option>

                            <option value="yes">
                                Có
                            </option>
                        </select>

                        <small>
                            Nếu chọn Có, tài khoản sẽ được cấp thêm quyền phụ huynh.
                        </small>
                    </div>

                    <div className="edit-teacher-field">
                        <label htmlFor="teacher-status">
                            Trạng thái
                        </label>

                        <select
                            id="teacher-status"
                            value={
                                isActive
                                    ? "active"
                                    : "inactive"
                            }
                            onChange={(e) =>
                                setIsActive(
                                    e.target.value === "active"
                                )
                            }
                            disabled={saving}
                        >
                            <option value="active">
                                Đang hoạt động
                            </option>

                            <option value="inactive">
                                Đã vô hiệu hóa
                            </option>
                        </select>
                    </div>

                    {error && (
                        <div className="edit-teacher-error">
                            {error}
                        </div>
                    )}

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
                            {saving
                                ? "Đang thêm..."
                                : "Thêm giáo viên"}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default AddTeacherForm;