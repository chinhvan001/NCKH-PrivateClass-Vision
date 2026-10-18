import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import SessionDetailPanel from "../components/admin/session/SessionPanel";

import { logoutAdmin } from "../utils/AuthSession";

const SessionDetail = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">
            <AdminSidebar onLogout={handleLogout} />

            <section className="admin-main-content">
                <AdminHeader />

                <SessionDetailPanel />
            </section>
        </main>
    );
};

export default SessionDetail;