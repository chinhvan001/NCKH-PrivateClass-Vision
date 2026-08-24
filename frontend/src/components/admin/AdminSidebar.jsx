import logo from "../../assets/logo.png";
import Icon from "../common/Icon";

const navigationItems = [
  { label: "Tổng quan", icon: "grid", group: "TỔNG QUAN" },
  {
    label: "Quản lý tài khoản",
    icon: "user",
    active: true,
    group: "QUẢN LÝ HỆ THỐNG",
  },
  { label: "Nhật ký hoạt động", icon: "activity" },
  { label: "Cài đặt hệ thống", icon: "settings", group: "CÀI ĐẶT" },
  { label: "Trung tâm trợ giúp", icon: "help", group: "HỖ TRỢ" },
];

const AdminSidebar = () => {
  return (
    <aside className="admin-sidebar">
      <div className="admin-brand">
        <img src={logo} alt="PrivateClass Vision" />
        <div>
          <strong>PrivateClass Vision</strong>
          <span>CỔNG QUẢN TRỊ</span>
        </div>
      </div>

      <nav className="admin-navigation" aria-label="Điều hướng quản trị">
        {navigationItems.map((item) => (
          <div key={item.label} className="admin-nav-group">
            {item.group && (
              <span className="admin-nav-group-label">{item.group}</span>
            )}
            <button
              type="button"
              className={`admin-nav-item ${item.active ? "active" : ""}`}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.label}</span>
            </button>
          </div>
        ))}
      </nav>

      <div className="admin-sidebar-actions">
        <button type="button">
          <Icon name="settings" size={18} />
          <span>Cài đặt</span>
        </button>
        <button type="button">
          <Icon name="logout" size={18} />
          <span>Đăng xuất</span>
        </button>
      </div>

      <p className="admin-sidebar-footer">
        © 2026 PrivateClass Vision.
        <br />
        Bảo lưu mọi quyền.
      </p>
    </aside>
  );
};

export default AdminSidebar;
