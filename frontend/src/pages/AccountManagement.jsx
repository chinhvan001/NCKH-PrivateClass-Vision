import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import AccountManagementPanel from "../components/admin/AccountManagementPanel";

import { clearAdminSession, logoutAdmin } from "../utils/AuthSession";


const AccountManagement = () => {
    const navigate = useNavigate();

    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);


    const fetchUsers = async () => {
        try {
            setLoading(true);

            const idToken = localStorage.getItem("idToken");

            if (!idToken) {
                throw new Error("Không tìm thấy phiên đăng nhập");
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

            // console.log("Admin users:", data);

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "Không thể lấy danh sách tài khoản"
                );
            }

            setUsers(data.users || []);

        } catch (error) {
            console.error("Fetch admin users error:", error);

            if (
                error.message.includes("phiên đăng nhập") ||
                error.message.includes("authorization")
            ) {
                clearAdminSession();
                navigate("/login", { replace: true });
            }

        } finally {
            setLoading(false);
        }
    };


    const handleUpdateUser = async (updatedUser) => {
        try {
            const idToken = localStorage.getItem("idToken");

            if (!idToken) {
                throw new Error("Không tìm thấy phiên đăng nhập");
            }

            const uid = updatedUser.uid || updatedUser.id;

            if (!uid) {
                throw new Error(
                    "Không xác định được UID của giáo viên"
                );
            }

            const response = await fetch(
                `http://127.0.0.1:5000/api/users/${uid}`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${idToken}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        name: updatedUser.name,
                        phone_number: updatedUser.phone_number,
                        subject: updatedUser.subject || [],
                        is_active: updatedUser.is_active,
                    }),
                }
            );

            const data = await response.json();

            console.log("Update user response:", data);

            if (!response.ok) {
                throw new Error(
                    data.message || "Cập nhật tài khoản thất bại"
                );
            }

            setUsers((prevUsers) =>
                prevUsers.map((user) =>
                    user.id === uid || user.uid === uid
                        ? {
                            ...user,
                            name: updatedUser.name,
                            phone_number: updatedUser.phone_number,
                            subject: updatedUser.subject || [],
                            is_active: updatedUser.is_active,
                        }
                        : user
                )
            );

            alert("Cập nhật tài khoản thành công.");

            return data;

        } catch (error) {
            console.error("Update user error:", error);

            alert(
                error.message ||
                "Có lỗi xảy ra khi cập nhật tài khoản."
            );

            throw error;
        }
    };

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };


    useEffect(() => {
        fetchUsers();
    }, []);


    return (
        <main className="admin-page">

            <AdminSidebar
                onLogout={handleLogout}
            />

            <section className="admin-main-content">

                <AdminHeader />

                <AccountManagementPanel
                    users={users}
                    loading={loading}
                    onRefresh={fetchUsers}
                    onUpdateUser={handleUpdateUser}
                />

            </section>

        </main>
    );
};


export default AccountManagement;