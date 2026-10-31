import { useNavigate } from "react-router-dom";

import AdminHeader from "../components/admin/AdminHeader";

import AdminSidebar from "../components/admin/AdminSidebar";

import CameraManagementPanel from "../components/admin/camera/CameraManagementPanel";

import { logoutAdmin } from "../utils/AuthSession";

const CameraManagement = () => {
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

                <CameraManagementPanel />
            </section>
        </main>
    );
};

export default CameraManagement;