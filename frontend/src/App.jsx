import { useState } from "react";
import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import OtpVerification from "./pages/OtpVerification";
import AccountManagement from "./pages/AccountManagement";

function App() {
  const [activePage, setActivePage] = useState("login");
  const [recoveryEmail, setRecoveryEmail] = useState("");

  if (activePage === "account-management") {
    return <AccountManagement />;
  }

  if (activePage === "forgot-password") {
    return (
      <ForgotPassword
        onBackToLogin={() => setActivePage("login")}
        onContinue={(email) => {
          setRecoveryEmail(email);
          setActivePage("otp-verification");
        }}
      />
    );
  }

  if (activePage === "otp-verification") {
    return (
      <OtpVerification
        email={recoveryEmail}
        onBackToLogin={() => setActivePage("login")}
        onChangeEmail={() => setActivePage("forgot-password")}
      />
    );
  }

  return (
    <Login
      onForgotPassword={() => setActivePage("forgot-password")}
      onLogin={() => setActivePage("account-management")}
    />
  );
}

export default App;