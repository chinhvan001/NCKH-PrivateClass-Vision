import { useEffect, useState } from "react";
import Icon from "../common/Icon";
import AdminProfileModal from "./AdminProfileModal";

const AdminHeader = () => {
  const [adminName, setAdminName] = useState("Admin");
  const [adminUser, setAdminUser] = useState(null);
  const [idToken, setIdToken] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("adminUser");
    const storedToken = localStorage.getItem("idToken");

    if (!storedUser) return;

    try {
      const user = JSON.parse(storedUser);

      if (user?.name) {
        setAdminName(user.name);
        setAdminUser(user);
      }

      if (storedToken) {
        setIdToken(storedToken);
      }
    } catch (error) {
      console.error("Không thể đọc thông tin Admin:", error);
    }
  }, []);

  const handleProfileClick = () => {
    setShowProfileModal(true);
  };

  const handleProfileSave = (updatedUser) => {
    setAdminUser(updatedUser);
    setAdminName(updatedUser.name);
  };

  return (
    <>
      <header className="admin-header">
        <div>
          <h1>
            Xin chào, {adminName}{" "}
            <span aria-hidden="true">👋</span>
          </h1>

          <p>Quản lý và kiểm soát các tài khoản hệ thống.</p>
        </div>

        <div className="admin-profile-area">
          <button
            type="button"
            className="admin-icon-button"
            aria-label="Thông báo"
          >
            <Icon name="bell" size={19} />
            <i />
          </button>

          <button
            type="button"
            className="admin-profile-button-area"
            onClick={handleProfileClick}
            aria-label="Xem hồ sơ cá nhân"
          >
            <div className="admin-avatar">
              {adminName.charAt(0).toUpperCase()}
            </div>

            <div className="admin-profile-copy">
              <strong>{adminName}</strong>
              <span>Admin</span>
            </div>

            <Icon
              name="chevron"
              size={15}
              className="admin-profile-chevron"
            />
          </button>
        </div>
      </header>

      {showProfileModal && adminUser && (
        <AdminProfileModal
          admin={adminUser}
          idToken={idToken}
          onClose={() => setShowProfileModal(false)}
          onSave={handleProfileSave}
        />
      )}
    </>
  );
};

export default AdminHeader;