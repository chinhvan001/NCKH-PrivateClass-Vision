import { useState } from "react";
import Input from "../common/Input";

const GoogleLoginForm = () => {
  const [email, setEmail] = useState("");

  const handleGoogleLogin = (event) => {
    event.preventDefault();

  };

  return (
    <div className="google-login-container">
      {/* Google Header */}
      <div className="google-header">
        <svg
          className="google-logo"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            fill="#4285F4"
            d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
          />

          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.1 0-5.74-2.09-6.68-4.91H1.26v3.15C3.23 21.3 7.33 24 12 24z"
          />

          <path
            fill="#FBBC05"
            d="M5.32 14.29c-.24-.72-.38-1.49-.38-2.29s.14-1.57.38-2.29V6.56H1.26C.46 8.16 0 9.98 0 12s.46 3.84 1.26 5.44l4.06-3.15z"
          />

          <path
            fill="#EA4335"
            d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.23 2.7 1.26 6.56l4.06 3.15c.94-2.82 3.58-4.96 6.68-4.96z"
          />
        </svg>

        <h2>Đăng nhập</h2>

        <p>để tiếp tục tới PrivateClass Vision</p>
      </div>

      {/* Form */}
      <form onSubmit={handleGoogleLogin} className="google-form">
        <div className="google-field">
          <label htmlFor="google-email">
            Email hoặc số điện thoại
          </label>

          <Input
            id="google-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nguoiquanly@truong.edu.vn"
            autoComplete="email"
            className="google-input"
            icon={
              <svg
                className="input-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                aria-hidden="true"
              >
                <rect x="3" y="5" width="18" height="14" rx="2" />
                <polyline points="3 7 12 13 21 7" />
              </svg>
            }
          />
        </div>

        {/* Action */}
        <div className="google-action-row">
          <button
            type="submit"
            className="google-next-btn"
          >
            <span>Tiếp theo</span>

            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="m13 6 6 6-6 6" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
};

export default GoogleLoginForm;