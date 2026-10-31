import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import ClassManagementPanel from "../components/admin/class/ClassManagementPanel";
import { logoutAdmin } from "../utils/AuthSession";

const ClassManagement = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">
            <AdminSidebar onLogout={handleLogout} />

            <section className="admin-main-content">
                <AdminHeader />
                <ClassManagementPanel />
            </section>
        </main>
    );
};

export default ClassManagement;