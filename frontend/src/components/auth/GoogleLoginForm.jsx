import { useState } from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebase";
import { saveAdminSession } from "../../utils/AuthSession";
import Input from "../common/Input";

const GoogleLoginForm = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleEmailPasswordLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (!email.trim() || !password.trim()) {
        setError("Vui lòng nhập email và mật khẩu");
        setLoading(false);
        return;
      }

      const response = await fetch(
        "http://127.0.0.1:5000/api/auth/email-password",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password,
          }),
        },
      );

      const data = await response.json();

      // console.log("Backend response: ", data);

      if (response.ok && data.success) {
        console.log("Admin login successful");
        saveAdminSession(data.user, data.idToken);
        onLogin?.(data.user);
        return;
      }

      setError(data.message || "Đăng nhập thất bại");
    } catch (error) {
      console.error("Email/Password Login Error: ", error);
      setError("Có lỗi khi đăng nhập");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      const idToken = await user.getIdToken();

      const response = await fetch("http://127.0.0.1:5000/api/auth/google", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          idToken: idToken,
        }),
      });

      const data = await response.json();
      // console.log("Backend response: ", data);

      if (response.ok && data.success) {
        // console.log("Admin login successful");
        saveAdminSession(data.user, idToken);
        onLogin?.(data.user);
        return;
      }

      alert(data.message);
    } catch (error) {
      console.error("Google Login Error: ", error);
      alert("Đăng nhập google thất bại");
    }
  };

  const emailIcon = (
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
      disabled={loading}
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
    <div className="google-login-container">

      <form onSubmit={handleEmailPasswordLogin} className="email-password-form">

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <Input
            id="email"
            type="email"
            placeholder="Nhập email của bạn"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            icon={emailIcon}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Mật khẩu</label>
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            placeholder="Nhập mật khẩu"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            icon={passwordIcon}
            rightElement={passwordToggle}
            disabled={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          className="email-password-button"
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Đang đăng nhập...
            </>
          ) : (
            "Đăng nhập"
          )}
        </button>
      </form>

      <div className="login-divider">
        <span>Hoặc đăng nhập bằng</span>
      </div>
      
      <button
        type="button"
        className="google-login-button"
        onClick={handleGoogleLogin}
      >
        <svg className="google-logo" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="#4285F4"
            d="M23.49 12.27c0-.79-.07-1.55-.2-2.27H12v4.3h6.44a5.5 5.5 0 0 1-2.39 3.61v3h3.87c2.27-2.09 3.57-5.17 3.57-8.64Z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.96-1.07 7.95-2.9l-3.87-3c-1.07.72-2.45 1.15-4.08 1.15-3.14 0-5.8-2.12-6.75-4.97H1.25v3.09A12 12 0 0 0 12 24Z"
          />
          <path
            fill="#FBBC05"
            d="M5.25 14.28A7.2 7.2 0 0 1 4.87 12c0-.79.14-1.56.38-2.28V6.63H1.25A12 12 0 0 0 0 12c0 1.93.46 3.75 1.25 5.37l4-3.09Z"
          />
          <path
            fill="#EA4335"
            d="M12 4.75c1.76 0 3.34.61 4.59 1.81l3.42-3.42C17.95 1.19 15.24 0 12 0A12 12 0 0 0 1.25 6.63l4 3.09C6.2 6.87 8.86 4.75 12 4.75Z"
          />
        </svg>
        <span>Google</span>
      </button>
    </div>
  );
};

export default GoogleLoginForm;
