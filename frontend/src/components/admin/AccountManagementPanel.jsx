import Icon from "../common/Icon";

const accounts = [
  {
    email: "admin@privateclass.vn",
    name: "Super Administrator",
    school: "Hệ thống",
    role: "Super Admin",
    roleType: "purple",
    status: "Đang hoạt động",
    statusType: "active",
    date: "20/05/2025",
    time: "09:15 AM",
  },
  {
    email: "admin.hanoischool@privateclass.vn",
    name: "Admin Trường Hà Nội",
    school: "Trường THPT Hà Nội",
    role: "Admin",
    roleType: "blue",
    status: "Đang hoạt động",
    statusType: "active",
    date: "19/05/2025",
    time: "02:30 PM",
  },
  {
    email: "admin.saigonschool@privateclass.vn",
    name: "Admin Trường Sài Gòn",
    school: "Trường THPT Sài Gòn",
    role: "Admin",
    roleType: "blue",
    status: "Đang hoạt động",
    statusType: "active",
    date: "18/05/2025",
    time: "10:45 AM",
  },
  {
    email: "admin.danangschool@privateclass.vn",
    name: "Admin Trường Đà Nẵng",
    school: "Trường THPT Đà Nẵng",
    role: "Admin",
    roleType: "blue",
    status: "Đang hoạt động",
    statusType: "active",
    date: "17/05/2025",
    time: "04:20 PM",
  },
  {
    email: "admin.canthoschool@privateclass.vn",
    name: "Admin Trường Cần Thơ",
    school: "Trường THPT Cần Thơ",
    role: "Admin",
    roleType: "blue",
    status: "Đã vô hiệu hóa",
    statusType: "inactive",
    date: "--",
    time: "",
  },
];

const accountStats = [
  { label: "Super Admin", value: "1", icon: "user", tone: "purple" },
  { label: "Admin trường", value: "12", icon: "user", tone: "blue" },
  { label: "Tổng tài khoản", value: "13", icon: "user", tone: "green" },
  { label: "Đang hoạt động", value: "12", icon: "checkCircle", tone: "orange" },
  { label: "Đã vô hiệu hóa", value: "1", icon: "xCircle", tone: "red" },
];

const AccountManagementPanel = () => {
  return (
    <>
      <section className="account-stats-section">
        <h2>Tài khoản hệ thống</h2>
        <div className="account-stats-grid">
          {accountStats.map((stat) => (
            <article
              key={stat.label}
              className={`account-stat-card ${stat.tone}`}
            >
              <div className="account-stat-icon">
                <Icon name={stat.icon} size={21} />
              </div>
              <div>
                <span>{stat.label}</span>
                <strong>{stat.value}</strong>
                <small>Tài khoản</small>
              </div>
            </article>
          ))}
          <article className="account-stat-card add-stat-card">
            <div className="account-stat-icon">
              <Icon name="plus" size={22} />
            </div>
            <div>
              <strong>Sắp có thêm</strong>
              <small>Tính năng sắp cập nhật</small>
            </div>
          </article>
        </div>
      </section>

      <section className="account-panel">
        <div className="account-panel-heading">
          <div>
            <h2>Quản lý tài khoản</h2>
            <p>
              Danh sách tài khoản Super Admin và Admin của các trường trong hệ
              thống.
            </p>
          </div>
          <button type="button" className="add-account-button">
            <Icon name="plus" size={17} />
            <span>Thêm tài khoản</span>
          </button>
        </div>

        <div className="account-filters">
          <label className="account-search">
            <input placeholder="Tìm kiếm theo tên, email..." />
            <Icon name="search" size={19} />
          </label>
          <label className="account-select">
            <span>Vai trò</span>
            <button type="button">
              Tất cả vai trò <Icon name="chevron" size={16} />
            </button>
          </label>
          <label className="account-select">
            <span>Tên trường</span>
            <button type="button">
              Tất cả trường <Icon name="chevron" size={16} />
            </button>
          </label>
          <label className="account-select">
            <span>Trạng thái</span>
            <button type="button">
              Tất cả trạng thái <Icon name="chevron" size={16} />
            </button>
          </label>
          <button type="button" className="refresh-button">
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        <div className="account-table-wrap">
          <table className="account-table">
            <thead>
              <tr>
                <th>Tài khoản</th>
                <th>Tên trường</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Đăng nhập cuối</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.email}>
                  <td>
                    <div className="account-cell">
                      <div className="table-avatar">
                        <Icon name="user" size={19} />
                      </div>
                      <div>
                        <strong>{account.email}</strong>
                        <span>{account.name}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="account-school">{account.school}</span>
                  </td>
                  <td>
                    <span className={`role-badge ${account.roleType}`}>
                      {account.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${account.statusType}`}>
                      <i></i>
                      {account.status}
                    </span>
                  </td>
                  <td>
                    <span className="last-login">
                      {account.date}
                      <br />
                      {account.time}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button
                        type="button"
                        aria-label={`Chỉnh sửa ${account.email}`}
                      >
                        <Icon name="edit" size={17} />
                      </button>
                      <button
                        type="button"
                        aria-label={`Thêm thao tác cho ${account.email}`}
                      >
                        <Icon name="more" size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="account-pagination">
          <span>Hiển thị 1 đến 5 của 13 tài khoản</span>
          <div>
            <button type="button" className="page-size">
              10 / trang <Icon name="chevron" size={14} />
            </button>
            <button type="button" disabled>
              <Icon name="first" size={15} />
            </button>
            <button type="button" disabled>
              <Icon name="arrowLeft" size={15} />
            </button>
            <button type="button" className="current-page">
              1
            </button>
            <button type="button">2</button>
            <button type="button">
              <Icon name="arrowRight" size={15} />
            </button>
            <button type="button">
              <Icon name="last" size={15} />
            </button>
          </div>
        </div>
      </section>
    </>
  );
};

export default AccountManagementPanel;
