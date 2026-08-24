import Icon from "../common/Icon";

const AdminHeader = () => {
  return (
    <header className="admin-header">
      <div>
        <h1>
          Xin chào, Admin <span aria-hidden="true">👋</span>
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
          <i></i>
        </button>
        <div className="admin-avatar">A</div>
        <div className="admin-profile-copy">
          <strong>Admin</strong>
          <span>Super Administrator</span>
        </div>
        <Icon name="chevron" size={15} className="admin-profile-chevron" />
      </div>
    </header>
  );
};

export default AdminHeader;
