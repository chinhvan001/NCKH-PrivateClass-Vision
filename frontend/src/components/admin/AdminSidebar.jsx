import logo from "../../assets/logo.png";
import Icon from "../common/Icon";

const navigationItems = [
    {
        label: "Tổng quan",
        icon: "grid",
        page: "dashboard",
        group: "TỔNG QUAN",
        enabled: true,
    },
    {
        label: "Quản lý tài khoản",
        icon: "user",
        page: "account-management",
        group: "QUẢN LÝ HỆ THỐNG",
        enabled: true,
    },
    {
        label: "Nhật ký hoạt động",
        icon: "activity",
        page: "activity-log",
        enabled: false,
    },
    {
        label: "Cài đặt hệ thống",
        icon: "settings",
        page: "settings",
        group: "CÀI ĐẶT",
        enabled: false,
    },
    {
        label: "Trung tâm trợ giúp",
        icon: "help",
        page: "help",
        group: "HỖ TRỢ",
        enabled: false,
    },
];

const AdminSidebar = ({
    activePage,
    onNavigate,
    onLogout,
}) => {
    return (
        <aside className="admin-sidebar">

            {/* =========================
                LOGO
            ========================= */}

            <div className="admin-brand">
                <img
                    src={logo}
                    alt="PrivateClass Vision"
                />

                <div>
                    <strong>PrivateClass Vision</strong>
                    <span>CỔNG QUẢN TRỊ</span>
                </div>
            </div>

            {/* =========================
                NAVIGATION
            ========================= */}

            <nav
                className="admin-navigation"
                aria-label="Điều hướng quản trị"
            >
                {navigationItems.map((item) => (
                    <div
                        key={item.label}
                        className="admin-nav-group"
                    >
                        {item.group && (
                            <span className="admin-nav-group-label">
                                {item.group}
                            </span>
                        )}

                        <button
                            type="button"
                            disabled={!item.enabled}
                            className={`admin-nav-item ${
                                activePage === item.page
                                    ? "active"
                                    : ""
                            } ${
                                !item.enabled
                                    ? "disabled"
                                    : ""
                            }`}
                            onClick={() => {
                                if (item.enabled) {
                                    onNavigate?.(item.page);
                                }
                            }}
                        >
                            <Icon
                                name={item.icon}
                                size={19}
                            />

                            <span>
                                {item.label}
                            </span>
                        </button>
                    </div>
                ))}
            </nav>

            {/* =========================
                SIDEBAR ACTIONS
            ========================= */}

            <div className="admin-sidebar-actions">

                <button
                    type="button"
                    disabled
                >
                    <Icon
                        name="settings"
                        size={18}
                    />

                    <span>Cài đặt</span>
                </button>

                <button
                    type="button"
                    onClick={onLogout}
                >
                    <Icon
                        name="logout"
                        size={18}
                    />

                    <span>Đăng xuất</span>
                </button>

            </div>

            {/* =========================
                FOOTER
            ========================= */}

            <p className="admin-sidebar-footer">
                © 2026 PrivateClass Vision.
                <br />
                Bảo lưu mọi quyền.
            </p>

        </aside>
    );
};

export default AdminSidebar;