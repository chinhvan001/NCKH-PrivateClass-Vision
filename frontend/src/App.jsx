import { useEffect, useState } from "react";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AccountManagement from "./pages/AccountManagement";

import {
  getAdminSession,
  clearAdminSession,
} from "./utils/AuthSession";

function App() {
  const [activePage, setActivePage] = useState("login");

  // const [recoveryEmail, setRecoveryEmail] = useState("");

  // =========================
  // KIỂM TRA ADMIN SESSION
  // =========================

  useEffect(() => {
    const session = getAdminSession();

    if (session) {
      // Session vẫn còn hạn
      setActivePage("dashboard");
    } else {
      // Session hết hạn hoặc chưa đăng nhập
      clearAdminSession();
      setActivePage("login");
    }
  }, []);

  // =========================
  // ĐĂNG XUẤT
  // =========================

  const handleLogout = () => {
    clearAdminSession();
    setActivePage("login");
  };

  // =========================
  // ĐIỀU HƯỚNG
  // =========================

  const handleNavigate = (page) => {
    setActivePage(page);
  };

  // =========================
  // DASHBOARD
  // =========================

  if (activePage === "dashboard") {
    return (
      <Dashboard
        onLogout={handleLogout}
        onNavigate={handleNavigate}
      />
    );
  }

  // =========================
  // ACCOUNT MANAGEMENT
  // =========================

  if (activePage === "account-management") {
    return (
      <AccountManagement
        onLogout={handleLogout}
        onNavigate={handleNavigate}
      />
    );
  }

  // =========================
  // FORGOT PASSWORD
  // =========================

  // if (activePage === "forgot-password") {
  //   return (
  //     <ForgotPassword
  //       onBackToLogin={() => setActivePage("login")}
  //       onContinue={(email) => {
  //         setRecoveryEmail(email);
  //         setActivePage("otp-verification");
  //       }}
  //     />
  //   );
  // }

  // =========================
  // OTP VERIFICATION
  // =========================

  // if (activePage === "otp-verification") {
  //   return (
  //     <OtpVerification
  //       email={recoveryEmail}
  //       onBackToLogin={() => setActivePage("login")}
  //       onChangeEmail={() => setActivePage("forgot-password")}
  //     />
  //   );
  // }

  // =========================
  // LOGIN
  // =========================

  return (
    <Login
      // onForgotPassword={() => setActivePage("forgot-password")}

      onLogin={() => setActivePage("dashboard")}
    />
  );
}

export default App;