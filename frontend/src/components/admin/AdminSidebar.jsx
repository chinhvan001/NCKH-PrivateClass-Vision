import { useLocation, useNavigate } from "react-router-dom";

import logo from "../../assets/logo.png";
import Icon from "../common/Icon";


const navigationItems = [
    {
        label: "Tổng quan",
        icon: "grid",
        path: "/dashboard",
        group: "TỔNG QUAN",
        enabled: true,
    },
    {
        label: "Quản lý giáo viên",
        icon: "user",
        path: "/account-management",
        group: "QUẢN LÝ HỆ THỐNG",
        enabled: true,
    },
    {
        label: "Quản lý phiên",
        icon: "school",
        path: "/session-management",
        enabled: true,
    },
    {
        label: "Nhật ký hoạt động",
        icon: "activity",
        path: "/activity-log",
        group: "Hệ thống",
        enabled: false,
    },
    {
        label: "Trung tâm trợ giúp",
        icon: "help",
        path: "/help",
        group: "HỖ TRỢ",
        enabled: false,
    },
];


const AdminSidebar = ({ onLogout }) => {
    const navigate = useNavigate();
    const location = useLocation();


    const handleNavigation = (path, enabled) => {
        if (!enabled) {
            return;
        }

        navigate(path);
    };


    return (
        <aside className="admin-sidebar">

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
                                location.pathname === item.path
                                    ? "active"
                                    : ""
                            } ${
                                !item.enabled
                                    ? "disabled"
                                    : ""
                            }`}
                            onClick={() =>
                                handleNavigation(
                                    item.path,
                                    item.enabled
                                )
                            }
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

            <p className="admin-sidebar-footer">
                © 2026 PrivateClass Vision.
                <br />
                Bảo lưu mọi quyền.
            </p>

        </aside>
    );
};


export default AdminSidebar;