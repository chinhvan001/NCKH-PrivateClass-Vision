import LoginBrandPanel from "../components/auth/LoginBrandPanel";
import LoginForm from "../components/auth/LoginForm";

const Login = ({ onForgotPassword, onLogin }) => {
  return (
    <main className="login-page">
      <section className="login-left">
        <LoginBrandPanel />
      </section>

      <section className="login-right">
        <LoginForm onForgotPassword={onForgotPassword} onLogin={onLogin} />

        <footer className="login-footer">
          <div className="footer-links">
            <a href="#">Chính sách bảo mật</a>
            <span>•</span>
            <a href="#">Trung tâm trợ giúp</a>
            <span>•</span>
            <a href="#">Điều khoản sử dụng</a>
          </div>

          <p>2026 PrivateClass Vision. Bảo lưu mọi quyền.</p>
        </footer>
      </section>
    </main>
  );
};

export default Login;
