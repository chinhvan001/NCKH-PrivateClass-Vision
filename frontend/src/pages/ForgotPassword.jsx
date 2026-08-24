import ForgotPasswordBrandPanel from "../components/auth/ForgotPasswordBrandPanel";
import ForgotPasswordForm from "../components/auth/ForgotPasswordForm";

const ForgotPassword = ({
  onBackToLogin,
  onContinue,
}) => {
  return (
    <main className="login-page forgot-page">
      <section className="login-left forgot-left">
        <ForgotPasswordBrandPanel />
      </section>

      <section className="login-right forgot-right">
        <div className="forgot-right-content">
          <div className="forgot-top-action">
            <button
              type="button"
              className="forgot-top-login-btn"
              onClick={onBackToLogin}
            >
              ĐĂNG NHẬP
            </button>
          </div>

          <ForgotPasswordForm
            onBackToLogin={onBackToLogin}
            onContinue={onContinue}
          />
        </div>
      </section>
    </main>
  );
};

export default ForgotPassword;
