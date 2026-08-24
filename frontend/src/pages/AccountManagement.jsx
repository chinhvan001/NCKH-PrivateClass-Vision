import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";
import AccountManagementPanel from "../components/admin/AccountManagementPanel";

const AccountManagement = () => {
  return (
    <main className="admin-page">
      <AdminSidebar />
      <section className="admin-main-content">
        <AdminHeader />
        <AccountManagementPanel />
      </section>
    </main>
  );
};

export default AccountManagement;
