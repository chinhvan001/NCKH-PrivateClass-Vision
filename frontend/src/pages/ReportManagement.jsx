import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import ReportManagementPanel from "../components/admin/report/ReportManagementPanel";

import { logoutAdmin } from "../utils/AuthSession";

const ReportManagement = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">
            <AdminSidebar onLogout={handleLogout} />

            <section className="admin-main-content">
                <AdminHeader />

                <ReportManagementPanel />
            </section>
        </main>
    );
};

export default ReportManagement;