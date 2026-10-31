import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import { 
    Users, CheckCircle, XCircle, BookOpen, Plus, 
    ArrowRight, RefreshCw, Server, Database, Activity, Info
} from "lucide-react";

import { getAuthHeaders } from "../../utils/AuthSession";

const DashboardPanel = () => {
    const navigate = useNavigate(); // Khởi tạo hook điều hướng
    const [loading, setLoading] = useState(true);
    const [dashboardData, setDashboardData] = useState({
        stats: { total_teachers: 0, active_teachers: 0, inactive_teachers: 0, total_subjects: 0 },
        active_sessions: [],
        concentration: { high: 0, medium: 0, low: 0, avg_score: 0, has_data: false },
        system_status: { backend: "Đang hoạt động", firebase: "Đang hoạt động", monitoring: "--", monitoring_ok: false },
        alerts: [],
        activities: []
    });

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/admin/dashboard-stats", {
                headers: await getAuthHeaders()
            });
            const result = await response.json();
            if (result.success) {
                setDashboardData(result);
            }
        } catch (error) {
            console.error("Lỗi khi tải dữ liệu Dashboard:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const { stats, active_sessions, concentration, system_status, alerts, activities } = dashboardData;

    const highVal = concentration.high || 0;
    const medVal = concentration.medium || 0;
    const lowVal = concentration.low || 0;

    const circumference = 100;
    const highDash = `${highVal} ${circumference - highVal}`;
    const medOffset = -highVal;
    const medDash = `${medVal} ${circumference - medVal}`;
    const lowOffset = -(highVal + medVal);
    const lowDash = `${lowVal} ${circumference - lowVal}`;

    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">
                <div>
                    <h2>Dashboard</h2>
                    <p>Tổng quan hệ thống quản lý lớp học.</p>
                </div>

                <button
                    type="button"
                    className="dashboard-refresh-button"
                    onClick={fetchDashboardData}
                >
                    <RefreshCw size={16} />
                    Làm mới
                </button>
            </div>

            {/* Thẻ thống kê */}
            <section className="dashboard-stat-grid">
                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon blue"><Users size={22} /></div>
                    <div className="dashboard-stat-info">
                        <span>Tổng giáo viên</span>
                        <strong>{loading ? "..." : stats.total_teachers}</strong>
                        <small>Tài khoản</small>
                    </div>
                </div>

                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon green"><CheckCircle size={22} /></div>
                    <div className="dashboard-stat-info">
                        <span>Đang hoạt động</span>
                        <strong>{loading ? "..." : stats.active_teachers}</strong>
                        <small>Tài khoản</small>
                    </div>
                </div>

                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon red"><XCircle size={22} /></div>
                    <div className="dashboard-stat-info">
                        <span>Đã vô hiệu hóa</span>
                        <strong>{loading ? "..." : stats.inactive_teachers}</strong>
                        <small>Tài khoản</small>
                    </div>
                </div>

                <div className="dashboard-stat-card">
                    <div className="dashboard-stat-icon purple"><BookOpen size={22} /></div>
                    <div className="dashboard-stat-info">
                        <span>Bộ môn</span>
                        <strong>{loading ? "..." : stats.total_subjects}</strong>
                        <small>Môn học</small>
                    </div>
                </div>

                <button
                    type="button"
                    className="dashboard-add-card"
                    // onClick={() => navigate("/account-management")}
                >
                    <div className="dashboard-add-icon"><Plus size={22} /></div>
                    <div>
                        <strong>Sắp có thêm</strong>
                        <span>Tính năng quản lý cập nhật</span>
                    </div>
                </button>
            </section>

            {/* Phần biểu đồ và bảng */}
            <section className="dashboard-main-grid">

                {/* BIỂU ĐỒ MỨC ĐỘ TẬP TRUNG */}
                <div className="dashboard-card engagement-card">
                    <div className="dashboard-card-header">
                        <div>
                            <h3>Mức độ tập trung</h3>
                            <p>Tổng quan tình trạng lớp học</p>
                        </div>
                        <span className="dashboard-badge-info">Từ camera AI</span>
                    </div>

                    <div className="engagement-content-wrapper">
                        <div className="engagement-chart-container">
                            <svg viewBox="0 0 36 36" className="engagement-donut-svg">
                                <path
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#edf2f7"
                                    strokeWidth="3.8"
                                />
                                {concentration.has_data && (
                                    <>
                                        <path
                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke="#10b981"
                                            strokeWidth="3.8"
                                            strokeDasharray={highDash}
                                        />
                                        <path
                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke="#f59e0b"
                                            strokeWidth="3.8"
                                            strokeDasharray={medDash}
                                            strokeDashoffset={medOffset}
                                        />
                                        <path
                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke="#ef4444"
                                            strokeWidth="3.8"
                                            strokeDasharray={lowDash}
                                            strokeDashoffset={lowOffset}
                                        />
                                    </>
                                )}
                            </svg>
                            <div className="engagement-chart-center">
                                <strong>{concentration.has_data ? `${concentration.avg_score}%` : "--"}</strong>
                                <span>{concentration.has_data ? "Trung bình" : "Chưa có dữ liệu"}</span>
                            </div>
                        </div>

                        <div className="engagement-progress-list">
                            <div className="progress-item">
                                <div className="progress-info">
                                    <span className="progress-label-wrap">
                                        <span className="dot high"></span>
                                        <strong>Tập trung cao</strong>
                                    </span>
                                    <span className="progress-percent high-text">{highVal}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div className="progress-bar-fill high-fill" style={{ width: `${highVal}%` }}></div>
                                </div>
                            </div>

                            <div className="progress-item">
                                <div className="progress-info">
                                    <span className="progress-label-wrap">
                                        <span className="dot medium"></span>
                                        <strong>Trung bình</strong>
                                    </span>
                                    <span className="progress-percent medium-text">{medVal}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div className="progress-bar-fill medium-fill" style={{ width: `${medVal}%` }}></div>
                                </div>
                            </div>

                            <div className="progress-item">
                                <div className="progress-info">
                                    <span className="progress-label-wrap">
                                        <span className="dot low"></span>
                                        <strong>Tập trung thấp</strong>
                                    </span>
                                    <span className="progress-percent low-text">{lowVal}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div className="progress-bar-fill low-fill" style={{ width: `${lowVal}%` }}></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Điều hướng sang trang Phân tích & Đánh giá */}
                    <button
                        className="dashboard-link-button"
                        type="button"
                        onClick={() => navigate("/evaluation-management")}
                    >
                        Xem báo cáo tập trung chi tiết
                        <ArrowRight size={15} />
                    </button>
                </div>

                {/* Phiên giám sát đang hoạt động */}
                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <div>
                            <h3>Các tiết học đang hoạt động</h3>
                            <p>Theo dõi các lớp học hiện tại</p>
                        </div>
                        <button
                            type="button"
                            className="dashboard-text-button"
                            onClick={() => navigate("/session-management")}
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
                                {active_sessions.length > 0 ? (
                                    active_sessions.map((session, index) => (
                                        <tr key={index}>
                                            <td><strong>{session.class_name}</strong></td>
                                            <td>{session.teacher}</td>
                                            <td>{session.students}</td>
                                            <td>
                                                <span className="monitoring-status active">
                                                    <i></i>
                                                    {session.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="4" className="empty-table-cell">
                                            Hiện tại không có phiên giám sát nào đang diễn ra.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Điều hướng sang trang Quản lý phiên */}
                    <button
                        className="dashboard-link-button"
                        type="button"
                        onClick={() => navigate("/session-management")}
                    >
                        Xem tất cả phiên giám sát
                        <ArrowRight size={15} />
                    </button>
                </div>

            </section>

            {/* Phần dưới: Trạng thái hệ thống & Hoạt động */}
            <section className="dashboard-bottom-grid">
                <div className="dashboard-card system-status-card">
                    <div className="dashboard-card-header">
                        <div>
                            <h3>Trạng thái hệ thống</h3>
                            <p>Tình trạng các thành phần</p>
                        </div>
                        <span className="system-status-percent">Hoạt động</span>
                    </div>

                    <div className="system-status-list">
                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon"><Server size={17} /></span>
                                <span>Backend API</span>
                            </div>
                            <strong className="status-ok">{system_status.backend}</strong>
                        </div>

                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon"><Database size={17} /></span>
                                <span>Firebase Firestore</span>
                            </div>
                            <strong className="status-ok">{system_status.firebase}</strong>
                        </div>

                        <div className="system-status-item">
                            <div>
                                <span className="system-status-icon"><Activity size={17} /></span>
                                <span>Monitoring Service</span>
                            </div>
                            <strong className={system_status.monitoring_ok ? "status-ok" : "status-pending"}>{system_status.monitoring}</strong>
                        </div>
                    </div>
                </div>

                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <div>
                            <h3>Cảnh báo gần đây</h3>
                            <p>Các thông báo từ hệ thống</p>
                        </div>
                        <button type="button" className="dashboard-text-button">Xem tất cả</button>
                    </div>

                    <div className="dashboard-alert-list">
                        {alerts.length > 0 ? alerts.map((alert, index) => (
                            <div className="dashboard-alert-item" key={index}>
                                <div className="dashboard-alert-icon"><Info size={17} /></div>
                                <div>
                                    <strong>{alert.title}{alert.handled ? " (đã xử lý)" : ""}</strong>
                                    <span>{alert.description}</span>
                                </div>
                            </div>
                        )) : (
                            <div className="dashboard-alert-item">
                                <div className="dashboard-alert-icon"><Info size={17} /></div>
                                <div>
                                    <strong>Chưa có cảnh báo mới</strong>
                                    <span>Không có tiết nào đang giám sát có cảnh báo</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="dashboard-card">
                    <div className="dashboard-card-header">
                        <div>
                            <h3>Hoạt động gần đây</h3>
                            <p>Hoạt động quản trị hệ thống</p>
                        </div>
                        <button type="button" className="dashboard-text-button">Xem tất cả</button>
                    </div>

                    <div className="dashboard-activity-list">
                        {activities.map((activity, index) => (
                            <div className="dashboard-activity-item" key={index}>
                                <div className="activity-dot"><CheckCircle size={14} /></div>
                                <div>
                                    <strong>{activity.title}</strong>
                                    <span>{activity.description}</span>
                                </div>
                                <time>{new Date(activity.time).toLocaleString("vi-VN")}</time>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

        </div>
    );
};

export default DashboardPanel;