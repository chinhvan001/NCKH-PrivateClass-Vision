import { useEffect, useState } from "react";
import Icon from "../common/Icon";

const AdminHeader = () => {
  const [adminName, setAdminName] = useState("Admin");

  useEffect(() => {
    const storedUser = localStorage.getItem("adminUser");

    if (!storedUser) return;

    try {
      const user = JSON.parse(storedUser);

      if (user?.name) {
        setAdminName(user.name);
      }
    } catch (error) {
      console.error("Không thể đọc thông tin Admin:", error);
    }
  }, []);

  return (
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
      </div>
    </header>
  );
};

export default AdminHeader;