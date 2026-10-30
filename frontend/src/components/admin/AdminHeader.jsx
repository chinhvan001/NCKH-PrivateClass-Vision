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
      <header className="admin-header" style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', letterSpacing: '-0.025em', display: 'flex', alignItems: 'center', gap: '8px', margin: '0 0 6px 0' }}>
            Xin chào, {adminName}{" "}
          </h1>

          <p style={{ fontSize: '14px', color: '#64748b', fontWeight: '400', margin: 0, lineHeight: '1.5' }}>
            Quản lý và kiểm soát các tài khoản hệ thống.
          </p>
        </div>

        <div className="admin-profile-area" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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