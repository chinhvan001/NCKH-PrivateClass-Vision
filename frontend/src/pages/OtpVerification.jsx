import OtpVerificationBrandPanel from "../components/auth/OtpVerificationBrandPanel";
import OtpVerificationForm from "../components/auth/OtpVerificationForm";

const OtpVerification = ({ email, onBackToLogin, onChangeEmail }) => {
  return (
    <main className="login-page forgot-page otp-page">
      <section className="login-left forgot-left otp-left">
        <OtpVerificationBrandPanel />
      </section>

      <section className="login-right forgot-right otp-right">
        <div className="forgot-right-content otp-right-content">
          <div className="forgot-top-action otp-top-action">
            <button
              type="button"
              className="forgot-top-login-btn"
              onClick={onBackToLogin}
            >
              ĐĂNG NHẬP
            </button>
          </div>

          <OtpVerificationForm
            email={email}
            onBackToLogin={onBackToLogin}
            onChangeEmail={onChangeEmail}
          />
        </div>
      </section>
    </main>
  );
};

export default OtpVerification;
