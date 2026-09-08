import { useState, useEffect } from "react";
import Icon from "../common/Icon";

const AdminProfileModal = ({ admin, idToken, onClose, onSave }) => {
  // Personal Information State
  const [name, setName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  
  // Password Change State
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Loading and Error State
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!admin) return;

    setName(admin.name || "");
    setPhoneNumber(admin.phone_number || "");
  }, [admin]);

  const handlePersonalInfoSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!name.trim()) {
      setError("Vui lòng nhập họ tên.");
      return;
    }

    try {
      setSaving(true);

      const response = await fetch(
        `http://127.0.0.1:5000/api/admin/profile/${admin.uid}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${idToken}`,
          },
          body: JSON.stringify({
            name: name.trim(),
            phone_number: phoneNumber.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Không thể cập nhật thông tin cá nhân");
      }

      setSuccessMessage("Cập nhật thông tin cá nhân thành công");
      
      // Update admin user in localStorage
      const storedUser = JSON.parse(localStorage.getItem("adminUser"));
      const updatedUser = {
        ...storedUser,
        name: name.trim(),
        phone_number: phoneNumber.trim(),
      };
      localStorage.setItem("adminUser", JSON.stringify(updatedUser));

      if (onSave) {
        onSave(updatedUser);
      }

      setTimeout(() => {
        setSuccessMessage("");
      }, 3000);
    } catch (error) {
      console.error("Update admin profile error:", error);
      setError(error.message || "Cập nhật thất bại.");
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("Vui lòng điền đầy đủ thông tin mật khẩu.");
      return;
    }

    if (newPassword.length < 6) {
      setError("Mật khẩu mới phải có ít nhất 6 ký tự.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    if (newPassword === currentPassword) {
      setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
      return;
    }

    try {
      setSaving(true);

      const response = await fetch(
        "http://127.0.0.1:5000/api/admin/change-password",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${idToken}`,
          },
          body: JSON.stringify({
            currentPassword,
            newPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Không thể đổi mật khẩu");
      }

      setSuccessMessage("Đổi mật khẩu thành công");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setShowPasswordForm(false);

      setTimeout(() => {
        setSuccessMessage("");
      }, 3000);
    } catch (error) {
      console.error("Change password error:", error);
      setError(error.message || "Đổi mật khẩu thất bại.");
    } finally {
      setSaving(false);
    }
  };

  if (!admin) {
    return null;
  }

  return (
    <div className="admin-profile-overlay">
      <div className="admin-profile-modal">
        <div className="admin-profile-header">
          <div>
            <h2>Hồ sơ cá nhân</h2>
            <p>Quản lý thông tin tài khoản Admin của bạn.</p>
          </div>

          <button
            type="button"
            className="admin-profile-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Đóng"
          >
            ×
          </button>
        </div>

        <div className="admin-profile-content">
          {/* Error Message */}
          {error && (
            <div className="admin-profile-message error-message">
              <Icon name="alertCircle" size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="admin-profile-message success-message">
              <Icon name="checkCircle" size={16} />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Personal Information Section */}
          <div className="admin-profile-section">
            <div className="admin-profile-section-header">
              <h3>Thông tin cá nhân</h3>
            </div>

            <form className="admin-profile-form" onSubmit={handlePersonalInfoSubmit}>
              <div className="admin-profile-field">
                <label htmlFor="admin-name">Họ và tên</label>
                <input
                  id="admin-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Nhập họ và tên"
                  disabled={saving}
                />
              </div>

              <div className="admin-profile-field">
                <label htmlFor="admin-email">Email</label>
                <input
                  id="admin-email"
                  type="email"
                  value={admin.email || ""}
                  disabled
                />
                <small>Email được liên kết với tài khoản và không thể chỉnh sửa.</small>
              </div>

              <div className="admin-profile-field">
                <label htmlFor="admin-phone">Số điện thoại</label>
                <input
                  id="admin-phone"
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="Nhập số điện thoại"
                  disabled={saving}
                />
              </div>

              <div className="admin-profile-field">
                <label htmlFor="admin-role">Vai trò</label>
                <input
                  id="admin-role"
                  type="text"
                  value={admin.role ? (admin.role === "super_admin" ? "Quản trị viên cấp cao" : "Quản trị viên") : "Admin"}
                  disabled
                />
              </div>

              <button
                type="submit"
                className="admin-profile-button primary"
                disabled={saving}
              >
                {saving ? (
                  "Đang lưu..."
                ) : (
                  <>
                    <Icon name="checkCircle" size={16} />
                    <span>Lưu thay đổi</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Password Change Section */}
          <div className="admin-profile-section">
            <div className="admin-profile-section-header">
              <h3>Bảo mật</h3>
            </div>

            {!showPasswordForm ? (
              <button
                type="button"
                className="admin-profile-button secondary"
                onClick={() => setShowPasswordForm(true)}
                disabled={saving}
              >
                <Icon name="lock" size={16} />
                <span>Đổi mật khẩu</span>
              </button>
            ) : (
              <form className="admin-profile-form" onSubmit={handlePasswordSubmit}>
                <div className="admin-profile-field">
                  <label htmlFor="current-password">Mật khẩu hiện tại</label>
                  <div className="admin-profile-password-input">
                    <input
                      id="current-password"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Nhập mật khẩu hiện tại"
                      disabled={saving}
                    />
                    <button
                      type="button"
                      className="admin-profile-toggle-password"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      disabled={saving}
                      aria-label="Hiển thị/ẩn mật khẩu"
                    >
                      <Icon name={showCurrentPassword ? "eye" : "eyeOff"} size={16} />
                    </button>
                  </div>
                </div>

                <div className="admin-profile-field">
                  <label htmlFor="new-password">Mật khẩu mới</label>
                  <div className="admin-profile-password-input">
                    <input
                      id="new-password"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Nhập mật khẩu mới"
                      disabled={saving}
                    />
                    <button
                      type="button"
                      className="admin-profile-toggle-password"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      disabled={saving}
                      aria-label="Hiển thị/ẩn mật khẩu"
                    >
                      <Icon name={showNewPassword ? "eye" : "eyeOff"} size={16} />
                    </button>
                  </div>
                </div>

                <div className="admin-profile-field">
                  <label htmlFor="confirm-password">Xác nhận mật khẩu</label>
                  <div className="admin-profile-password-input">
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Nhập lại mật khẩu mới"
                      disabled={saving}
                    />
                    <button
                      type="button"
                      className="admin-profile-toggle-password"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={saving}
                      aria-label="Hiển thị/ẩn mật khẩu"
                    >
                      <Icon name={showConfirmPassword ? "eye" : "eyeOff"} size={16} />
                    </button>
                  </div>
                </div>

                <small>Mật khẩu phải có ít nhất 6 ký tự.</small>

                <div className="admin-profile-password-actions">
                  <button
                    type="button"
                    className="admin-profile-button secondary"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setCurrentPassword("");
                      setNewPassword("");
                      setConfirmPassword("");
                    }}
                    disabled={saving}
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    className="admin-profile-button primary"
                    disabled={saving}
                  >
                    {saving ? (
                      "Đang xử lý..."
                    ) : (
                      <>
                        <Icon name="checkCircle" size={16} />
                        <span>Xác nhận</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Additional Information Section */}
          <div className="admin-profile-section">
            <div className="admin-profile-section-header">
              <h3>Thông tin tài khoản</h3>
            </div>

            <div className="admin-profile-info-grid">
              <div className="admin-profile-info-item">
                <span className="admin-profile-info-label">UID</span>
                <span className="admin-profile-info-value">{admin.uid}</span>
              </div>
              <div className="admin-profile-info-item">
                <span className="admin-profile-info-label">Trạng thái</span>
                <span className="admin-profile-info-value">
                  {admin.is_active !== false ? (
                    <span className="admin-profile-status active">Đang hoạt động</span>
                  ) : (
                    <span className="admin-profile-status inactive">Đã vô hiệu hóa</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminProfileModal;
