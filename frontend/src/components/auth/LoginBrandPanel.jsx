import logo from "../../assets/logo.png";

const LoginBrandPanel = () => {
  return (
    <div className="brand-panel">
      <div className="brand-circle brand-circle-top"></div>
      <div className="brand-circle brand-circle-bottom"></div>

      <div className="brand-content">
        <div className="brand-logo">
          <img
            src={logo}
            alt="PrivateClass Vision"
            className="brand-logo-image"
          />

          <div className="brand-logo-text">
            <h1>PrivateClass Vision</h1>
            <span>CỔNG QUẢN TRỊ</span>
          </div>
        </div>

        <div className="brand-intro">
          <h2>
            Truy cập an toàn, đơn giản
            <br />
            vào hệ thống của trường
          </h2>

          <p>
            Quản lý camera, lớp học, giáo viên và học sinh từ một cổng quản trị
            đáng tin cậy
          </p>
        </div>

        <div className="brand-features">
          <div className="brand-feature">
            <div className="feature-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <rect x="3" y="6" width="18" height="13" rx="2" />
                <circle cx="12" cy="12.5" r="3" />
                <path d="M8 6l1.2-2h5.6L16 6" />
              </svg>
            </div>

            <span>Giám sát camera trực tiếp khắp khuôn viên</span>
          </div>

          <div className="brand-feature">
            <div className="feature-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <circle cx="9" cy="8" r="3" />
                <circle cx="17" cy="9" r="2.5" />
                <path d="M3.5 19c.5-3 2.4-5 5.5-5s5 2 5.5 5" />
                <path d="M14 15c2.7-.1 4.8 1.3 5.5 4" />
              </svg>
            </div>

            <span>Quản lý lớp học, giáo viên và học sinh</span>
          </div>

          <div className="brand-feature">
            <div className="feature-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z" />
                <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20" />
                <path d="M12 7v7" />
                <path d="M8.5 10.5h7" />
              </svg>
            </div>

            <span>Lịch học và hồ sơ học tập</span>
          </div>
        </div>

        {/* Khối phía dưới được thay đổi thành thông điệp bảo mật/công nghệ thay vì số liệu thô */}
        <div className="system-status">
          <div className="status-title">
            <span className="status-dot"></span>
            <span>Hệ thống bảo mật và phân tích thông minh</span>
          </div>

          <div className="status-line"></div>

          <div className="status-statistics">
            <div className="status-item">
              <strong>Bảo mật</strong>
              <span>Mã hóa đầu cuối</span>
            </div>

            <div className="status-item">
              <strong>Riêng tư</strong>
              <span>AI phân tích ẩn danh</span>
            </div>

            <div className="status-item">
              <strong>Ổn định</strong>
              <span>Hoạt động 24/7</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginBrandPanel;