import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import EvaluationManagementPanel from "../components/admin/evaluation/EvaluationManagementPanel";

import { logoutAdmin } from "../utils/AuthSession";

const EvaluationManagement = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">
            <AdminSidebar onLogout={handleLogout} />

            <section className="admin-main-content">
                <AdminHeader />

                <EvaluationManagementPanel />
            </section>
        </main>
    );
};

export default EvaluationManagement;