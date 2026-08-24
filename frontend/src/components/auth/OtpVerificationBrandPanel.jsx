import logo from "../../assets/logo.png";

const OtpVerificationBrandPanel = () => {
  return (
    <div className="brand-panel forgot-brand-panel otp-brand-panel">
      <div className="brand-circle brand-circle-top"></div>
      <div className="brand-circle brand-circle-bottom"></div>

      <div className="brand-content forgot-brand-content otp-brand-content">
        <div className="brand-logo">
          <img
            src={logo}
            alt="PrivateClass Vision"
            className="brand-logo-image"
          />

          <div className="brand-logo-text forgot-logo-text">
            <h1>PrivateClass Vision</h1>
            <span>CỔNG QUẢN TRỊ</span>
          </div>
        </div>

        <div className="otp-brand-intro">
          <h2>
            Hỗ trợ khôi phục tài
            <br />
            khoản
          </h2>

          <p>
            Mã xác minh đã được gửi đến email. Vui lòng nhập mã OTP để tiếp tục
            quy trình.
          </p>
        </div>

        <div className="forgot-brand-status otp-brand-status">
          <span className="status-dot"></span>
          <span>Hệ thống bảo mật đang hoạt động</span>
        </div>
      </div>
    </div>
  );
};

export default OtpVerificationBrandPanel;
