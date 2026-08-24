import { useState } from "react";
import Input from "../common/Input";

const ForgotPasswordForm = ({
  onBackToLogin,
  onContinue,
}) => {
  const [email, setEmail] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    onContinue(email);
  };

  return (
    <div className="forgot-form-wrapper">
      <div className="forgot-card">
        <div className="forgot-heading">
          <h2>Quên mật khẩu</h2>

          <p>
            Nhập email của bạn để bắt đầu quy trình xác minh. Chúng tôi sẽ gửi
            mã gồm 4 chữ số đến email của bạn.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="forgot-form">
          <div className="form-group forgot-form-group">
            <label htmlFor="forgot-email">Nhập email</label>

            <Input
              id="forgot-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              autoComplete="email"
              className="forgot-input"
              icon={
                <svg
                  className="input-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  aria-hidden="true"
                >
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <polyline points="3 7 12 13 21 7" />
                </svg>
              }
            />
          </div>

          <button type="submit" className="forgot-submit-btn">
            <span>TIẾP TỤC</span>

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
        </form>

        <div className="forgot-actions">
          <button
            type="button"
            className="forgot-back-link"
            onClick={onBackToLogin}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              aria-hidden="true"
            >
              <path d="M19 12H5" />
              <path d="m11 6-6 6 6 6" />
            </svg>
            <span>Quay lại Đăng nhập</span>
          </button>

          <a href="#" className="forgot-help-link">
            Liên hệ trợ giúp
          </a>
        </div>

        <div className="forgot-security-message">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path d="M12 3 19 6v5c0 4.5-2.8 8.1-7 10-4.2-1.9-7-5.5-7-10V6l7-3Z" />
            <path d="m9 12 2 2 4-4" />
          </svg>

          <span>Được bảo vệ bởi chính sách bảo mật của trường</span>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;
