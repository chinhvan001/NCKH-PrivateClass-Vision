// import { useState } from "react";

// import LoginMethodSwitcher from "./LoginMethodSwitcher";
// import AccountLoginForm from "./AccountLoginForm";
import GoogleLoginForm from "./GoogleLoginForm";

const LoginForm = ({ onForgotPassword, onLogin }) => {
  // const [activeMethod, setActiveMethod] = useState("account");

  return (
    <div className="login-form-wrapper">
      <div className="login-card">
        {/* Heading */}
        <div className="login-heading">
          <h2>Chào mừng trở lại</h2>
          <p>Đăng nhập vào cổng quản trị PrivateClass Vision</p>
        </div>

        {/* Login method switcher */}
        {/* <LoginMethodSwitcher
          activeMethod={activeMethod}
          onChange={setActiveMethod}
        /> */}

        {/* Login form */}
        {/* {activeMethod === "account" && (
          <AccountLoginForm
            onForgotPassword={onForgotPassword}
            onLogin={onLogin}
          />
        )}

        {activeMethod === "google" && <GoogleLoginForm />} */}

        <GoogleLoginForm onLogin={onLogin}/>

        {/* Security */}
        <div className="security-message">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
          >
            <path d="M12 3 19 6v5c0 4.5-2.8 8.1-7 10-4.2-1.9-7-5.5-7-10V6l7-3Z" />
            <path d="m9 12 2 2 4-4" />
          </svg>

          <span>
            Được bảo vệ bởi chính sách bảo mật của trường
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;