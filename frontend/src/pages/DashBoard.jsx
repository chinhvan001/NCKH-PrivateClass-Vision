import { useEffect, useState } from "react";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import DashboardPanel from "../components/admin/DashboardPanel";

const Dashboard = ({ onLogout, onNavigate }) => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchUsers = async () => {
        try {
            setLoading(true);

            const idToken = localStorage.getItem("idToken");

            if (!idToken) {
                return;
            }

            const response = await fetch(
                "http://127.0.0.1:5000/api/admin/users",
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${idToken}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            const data = await response.json();

            console.log("Dashboard users:", data);

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "Không thể lấy dữ liệu Dashboard"
                );
            }

            setUsers(data.users || []);
        } catch (error) {
            console.error("Fetch dashboard users error:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    return (
        <main className="admin-page">
            <AdminSidebar
                onLogout={onLogout}
                activePage="dashboard"
                onNavigate={onNavigate}
            />

            <section className="admin-main-content">
                <AdminHeader />

                <DashboardPanel
                    users={users}
                    loading={loading}
                    onRefresh={fetchUsers}
                    onNavigate={onNavigate}
                />
            </section>
        </main>
    );
};

export default Dashboard;