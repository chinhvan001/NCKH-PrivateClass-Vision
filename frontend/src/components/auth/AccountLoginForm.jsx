import { useState } from "react";
import Input from "../common/Input";

const AccountLoginForm = ({ onForgotPassword, onLogin }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);

  const handleSubmit = (event) => {
    event.preventDefault();

    onLogin();
  };

  const usernameIcon = (
    <svg
      className="input-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <circle cx="12" cy="8" r="3" />
      <path d="M6.5 20c.5-3.5 2.3-5.5 5.5-5.5s5 2 5.5 5.5" />
    </svg>
  );

  const passwordIcon = (
    <svg
      className="input-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <rect x="5" y="10" width="14" height="10" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );

  const passwordToggle = (
    <button
      type="button"
      className="password-toggle"
      onClick={() => setShowPassword(!showPassword)}
      aria-label={showPassword ? "Ẩn mật khẩu" : "Hiển thị mật khẩu"}
    >
      {showPassword ? (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path d="M3 3l18 18" />
          <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
          <path d="M9.9 4.3A10.7 10.7 0 0 1 12 4c5.5 0 9 5 9 8a8.7 8.7 0 0 1-2.2 4.2" />
          <path d="M6.2 6.2C3.9 7.8 3 10 3 12c0 3 3.5 8 9 8a9.8 9.8 0 0 0 4.1-.9" />
        </svg>
      ) : (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
          <circle cx="12" cy="12" r="2.5" />
        </svg>
      )}
    </button>
  );

  return (
    <form onSubmit={handleSubmit}>
      {/* Username */}
      <div className="form-group">
        <label htmlFor="username">Tên tài khoản</label>

        <Input
          id="username"
          type="text"
          placeholder="VD: jsmith_admin"
          autoComplete="username"
          icon={usernameIcon}
        />

        <small>
          Sử dụng tài khoản do quản trị viên nhà trường cấp.
        </small>
      </div>

      {/* Password */}
      <div className="form-group">
        <label htmlFor="password">Mật khẩu</label>

        <Input
          id="password"
          type={showPassword ? "text" : "password"}
          placeholder="Nhập mật khẩu của bạn"
          autoComplete="current-password"
          icon={passwordIcon}
          rightElement={passwordToggle}
        />
      </div>

      {/* Remember + Forgot */}
      <div className="login-options">
        <label className="remember-option">
          <input
            type="checkbox"
            checked={remember}
            onChange={(event) => setRemember(event.target.checked)}
          />

          <span className="custom-checkbox"></span>

          <span>Ghi nhớ đăng nhập</span>
        </label>

        <button
          type="button"
          className="forgot-password"
          onClick={onForgotPassword}
        >
          Quên mật khẩu?
        </button>
      </div>

      {/* Submit */}
      <button type="submit" className="login-button">
        <span>Đăng nhập</span>

        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M5 12h13" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      </button>
    </form>
  );
};

export default AccountLoginForm;