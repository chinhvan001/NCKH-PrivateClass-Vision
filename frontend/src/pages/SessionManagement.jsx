import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import SessionManagementPanel from "../components/admin/SessionManagementPanel";

import { logoutAdmin } from "../utils/AuthSession";


const SessionManagement = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logoutAdmin(navigate);
    };

    return (
        <main className="admin-page">

            <AdminSidebar
                onLogout={handleLogout}
            />

            <section className="admin-main-content">

                <AdminHeader />

                <SessionManagementPanel />

            </section>

        </main>
    );
};


export default SessionManagement;