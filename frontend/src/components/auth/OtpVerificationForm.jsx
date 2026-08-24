import { useRef, useState } from "react";

const OTP_LENGTH = 6;

const OtpVerificationForm = ({
  email,
  onBackToLogin,
  onChangeEmail,
}) => {
  const [otpValues, setOtpValues] = useState(
    () => Array(OTP_LENGTH).fill("")
  );
  const inputRefs = useRef([]);

  const handleSubmit = (event) => {
    event.preventDefault();
  };

  const handleOtpChange = (index, value) => {
    const nextValue = value.replace(/\D/g, "").slice(-1);

    setOtpValues((previous) => {
      const updated = [...previous];
      updated[index] = nextValue;
      return updated;
    });

    if (nextValue && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, event) => {
    if (
      event.key === "Backspace" &&
      !otpValues[index] &&
      index > 0
    ) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const displayEmail = email && email.trim()
    ? `[${email.trim()}]`
    : "[email_nguoidung@gmail.com]";

  return (
    <div className="forgot-form-wrapper otp-form-wrapper">
      <div className="forgot-card otp-card">
        <div className="forgot-heading otp-heading">
          <h2>Xác minh tài khoản</h2>

          <p>
            Mã xác minh (OTP) gồm 6 chữ số đã được gửi đến địa chỉ email: {" "}
            <strong>{displayEmail}</strong> (example text). Mã này có hiệu lực
            trong 5 phút.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="forgot-form otp-form">
          <div className="otp-input-row" aria-label="Nhập mã OTP gồm 6 chữ số">
            {otpValues.map((digit, index) => (
              <input
                key={`otp-${index}`}
                ref={(node) => {
                  inputRefs.current[index] = node;
                }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                className="otp-digit-input"
                value={digit}
                onChange={(event) =>
                  handleOtpChange(index, event.target.value)
                }
                onKeyDown={(event) => handleOtpKeyDown(index, event)}
                placeholder="0"
                aria-label={`Số OTP thứ ${index + 1}`}
              />
            ))}
          </div>

          <p className="otp-resend-text">
            Không nhận được mã? Gửi lại mã sau <strong>00:59</strong>
          </p>

          <button type="submit" className="forgot-submit-btn otp-submit-btn">
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

        <div className="forgot-actions otp-actions">
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

          <button
            type="button"
            className="otp-change-email-btn"
            onClick={onChangeEmail}
          >
            Sai email? Nhập lại email.
          </button>
        </div>

        <div className="forgot-security-message otp-security-message">
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

export default OtpVerificationForm;
