import Icon from "../common/Icon";

const DashboardPanel = ({
    users = [],
    loading,
    onRefresh,
    onNavigate,
}) => {
    const totalTeachers = users.length;

    const activeTeachers = users.filter(
        (user) => user.is_active !== false
    ).length;

    const inactiveTeachers = users.filter(
        (user) => user.is_active === false
    ).length;

    // Lấy danh sách môn học thực tế từ tài khoản giáo viên
    const subjects = [
        ...new Set(
            users.flatMap((user) =>
                Array.isArray(user.subject)
                    ? user.subject
                    : []
            )
        ),
    ];

    /*
     * DỮ LIỆU TẠM THỜI
     * Sau này sẽ thay bằng API monitoring thật.
     */
    const monitoringSessions = [
        {
            className: "Lớp 10A1",
            teacher: "Giáo viên 1",
            students: "--",
            status: "Đang hoạt động",
        },
        {
            className: "Lớp 10A2",
            teacher: "--",
            students: "--",
            status: "Chưa bắt đầu",
        },
        {
            className: "Lớp 11A1",
            teacher: "--",
            students: "--",
            status: "Chưa bắt đầu",
        },
    ];

    const alerts = [
        {
            title: "Chưa có cảnh báo mới",
            description: "Hệ thống chưa ghi nhận cảnh báo",
            type: "info",
        },
        {
            title: "Dữ liệu giám sát",
            description: "Tính năng đang được phát triển",
            type: "info",
        },
    ];

    const activities = [
        {
            title: "Đăng nhập hệ thống",
            description: "Quản trị viên đã đăng nhập",
            time: "Vừa xong",
        },
        {
            title: "Đồng bộ tài khoản giáo viên",
            description: `${totalTeachers} tài khoản giáo viên`,
            time: "Hiện tại",
        },
        {
            title: "Kiểm tra hệ thống",
            description: "Hệ thống hoạt động bình thường",
            time: "Hiện tại",
        },
    ];

    return (
        <div className="dashboard-content">

            {/* ================= HEADER ================= */}
            <div className="dashboard-heading">
                <div>
                    <h2>Dashboard</h2>
                    <p>
                        Tổng quan hệ thống PrivateClass Vision.
                    </p>
                </div>

                <button
                    type="button"
                    className="dashboard-refresh-button"
                    onClick={onRefresh}
                >
                    <Icon name="refresh" size={16} />
                    Làm mới
                </button>
            </div>


            {/* ================= STAT CARDS ================= */}
            <section className="dashboard-stat-grid">

                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon blue">
                        <Icon name="book" size={21} />
                    </div>

                    <div>
                        <span>Tổng giáo viên</span>

                        <strong>
                            {loading ? "..." : totalTeachers}
                        </strong>

                        <small>Tài khoản</small>
                    </div>
                </div>


                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon green">
                        <Icon name="check" size={21} />
                    </div>

                    <div>
                        <span>Đang hoạt động</span>

                        <strong>
                            {loading ? "..." : activeTeachers}
                        </strong>

                        <small>Tài khoản</small>
                    </div>
                </div>


                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon red">
                        <Icon name="close" size={21} />
                    </div>

                    <div>
                        <span>Đã vô hiệu hóa</span>

                        <strong>
                            {loading ? "..." : inactiveTeachers}
                        </strong>

                        <small>Tài khoản</small>
                    </div>
                </div>


                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon purple">
                        <Icon name="book" size={21} />
                    </div>

                    <div>
                        <span>Bộ môn</span>

                        <strong>
                            {loading ? "..." : subjects.length}
                        </strong>

                        <small>Môn học</small>
                    </div>
                </div>


                <button
                    type="button"
                    className="dashboard-add-card"
                    onClick={() => onNavigate?.("account-management")}
                >
                    <div className="dashboard-add-icon">
                        <Icon name="plus" size={21} />
                    </div>

                    <div>
                        <strong>Sắp có thêm</strong>
                        <span>
                            Tính năng quản lý cấp nhật
                        </span>
                    </div>
                </button>

            </section>


            {/* ================= MAIN GRID ================= */}
            <section className="dashboard-main-grid">

                {/* ===== ENGAGEMENT ===== */}
                <div className="dashboard-card engagement-card">

                    <div className="dashboard-card-header">
                        <div>
                            <h3>Mức độ tập trung</h3>
                            <p>
                                Tổng quan tình trạng lớp học
                            </p>
                        </div>

                        <span className="dashboard-card-info">
                            Tạm thời
                        </span>
                    </div>


                    <div className="engagement-content">

                        <div className="engagement-circle">
                            <div>
                                <strong>--</strong>
                                <span>
                                    Chưa có dữ liệu
                                </span>
                            </div>
                        </div>


                        <div className="engagement-legend">

                            <div>
                                <span className="legend-dot high"></span>
                                <div>
                                    <strong>Tập trung cao</strong>
                                    <small>--</small>
                                </div>
                            </div>

                            <div>
                                <span className="legend-dot medium"></span>
                                <div>
                                    <strong>Tập trung trung bình</strong>
                                    <small>--</small>
                                </div>
                            </div>

                            <div>
                                <span className="legend-dot low"></span>
                                <div>
                                    <strong>Tập trung thấp</strong>
                                    <small>--</small>
                                </div>
                            </div>

                        </div>

                    </div>

                    <button
                        className="dashboard-link-button"
                        type="button"
                    >
                        Xem báo cáo tập trung
                        <Icon name="arrow-right" size={15} />
                    </button>

                </div>


                {/* ===== MONITORING SESSION ===== */}
                <div className="dashboard-card">

                    <div className="dashboard-card-header">

                        <div>
                            <h3>Phiên giám sát đang hoạt động</h3>
                            <p>
                                Theo dõi các lớp học hiện tại
                            </p>
                        </div>

                        <button
                            type="button"
                            className="dashboard-text-button"
                        >
                            Xem tất cả
                        </button>

                    </div>


                    <div className="dashboard-table-wrapper">

                        <table className="dashboard-table">

                            <thead>
                                <tr>
                                    <th>Lớp</th>
                                    <th>Giáo viên</th>
                                    <th>HS</th>
                                    <th>Trạng thái</th>
                                </tr>
                            </thead>

                            <tbody>

                                {monitoringSessions.map(
                                    (session, index) => (
                                        <tr key={index}>

                                            <td>
                                                <strong>
                                                    {session.className}
                                                </strong>
                                            </td>

                                            <td>
                                                {session.teacher}
                                            </td>

                                            <td>
                                                {session.students}
                                            </td>

                                            <td>
                                                <span
                                                    className={`monitoring-status ${
                                                        session.status ===
                                                        "Đang hoạt động"
                                                            ? "active"
                                                            : "waiting"
                                                    }`}
                                                >
                                                    <i></i>
                                                    {session.status}
                                                </span>
                                            </td>

                                        </tr>
                                    )
                                )}

                            </tbody>

                        </table>

                    </div>

                    <button
                        type="button"
                        className="dashboard-link-button"
                    >
                        Xem tất cả phiên giám sát
                        <Icon name="arrow-right" size={15} />
                    </button>

                </div>

            </section>


            {/* ================= BOTTOM GRID ================= */}
            <section className="dashboard-bottom-grid">

                {/* ===== SYSTEM STATUS ===== */}
                <div className="dashboard-card system-status-card">

                    <div className="dashboard-card-header">

                        <div>
                            <h3>Trạng thái hệ thống</h3>
                            <p>
                                Tình trạng các thành phần
                            </p>
                        </div>

                        <span className="system-status-percent">
                            Hoạt động
                        </span>

                    </div>


                    <div className="system-status-list">

                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon">
                                    <Icon
                                        name="server"
                                        size={17}
                                    />
                                </span>

                                <span>
                                    Backend API
                                </span>
                            </div>

                            <strong className="status-ok">
                                Đang hoạt động
                            </strong>
                        </div>


                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon">
                                    <Icon
                                        name="database"
                                        size={17}
                                    />
                                </span>

                                <span>
                                    Firebase Firestore
                                </span>
                            </div>

                            <strong className="status-ok">
                                Đang hoạt động
                            </strong>
                        </div>


                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon">
                                    <Icon
                                        name="activity"
                                        size={17}
                                    />
                                </span>

                                <span>
                                    Monitoring Service
                                </span>
                            </div>

                            <strong className="status-pending">
                                Đang phát triển
                            </strong>
                        </div>

                    </div>

                </div>


                {/* ===== ALERTS ===== */}
                <div className="dashboard-card">

                    <div className="dashboard-card-header">

                        <div>
                            <h3>Cảnh báo gần đây</h3>
                            <p>
                                Các thông báo từ hệ thống
                            </p>
                        </div>

                        <button
                            type="button"
                            className="dashboard-text-button"
                        >
                            Xem tất cả
                        </button>

                    </div>


                    <div className="dashboard-alert-list">

                        {alerts.map((alert, index) => (

                            <div
                                className="dashboard-alert-item"
                                key={index}
                            >

                                <div className="dashboard-alert-icon">
                                    <Icon
                                        name="info"
                                        size={17}
                                    />
                                </div>

                                <div>
                                    <strong>
                                        {alert.title}
                                    </strong>

                                    <span>
                                        {alert.description}
                                    </span>
                                </div>

                            </div>

                        ))}

                    </div>

                </div>


                {/* ===== ACTIVITIES ===== */}
                <div className="dashboard-card">

                    <div className="dashboard-card-header">

                        <div>
                            <h3>Hoạt động gần đây</h3>
                            <p>
                                Hoạt động quản trị hệ thống
                            </p>
                        </div>

                        <button
                            type="button"
                            className="dashboard-text-button"
                        >
                            Xem tất cả
                        </button>

                    </div>


                    <div className="dashboard-activity-list">

                        {activities.map(
                            (activity, index) => (

                                <div
                                    className="dashboard-activity-item"
                                    key={index}
                                >

                                    <div className="activity-dot">
                                        <Icon
                                            name="check"
                                            size={14}
                                        />
                                    </div>

                                    <div>
                                        <strong>
                                            {activity.title}
                                        </strong>

                                        <span>
                                            {activity.description}
                                        </span>
                                    </div>

                                    <time>
                                        {activity.time}
                                    </time>

                                </div>

                            )
                        )}

                    </div>

                </div>

            </section>

        </div>
    );
};

export default DashboardPanel;