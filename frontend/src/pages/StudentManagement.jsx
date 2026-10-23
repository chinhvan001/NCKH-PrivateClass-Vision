import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import StudentManagementPanel from "../components/admin/student/StudentManagementPanel";

import { logoutAdmin } from "../utils/AuthSession";

const StudentManagement = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">
            <AdminSidebar onLogout={handleLogout} />

            <section className="admin-main-content">
                <AdminHeader />

                <StudentManagementPanel />
            </section>
        </main>
    );
};

export default StudentManagement;