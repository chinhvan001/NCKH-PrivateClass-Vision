const LoginMethodSwitcher = ({ activeMethod, onChange }) => {
  return (
    <div className="login-method">
      {/* Ô trắng trượt */}
      <div
        className={`method-slider ${
          activeMethod === "google" ? "slide-right" : ""
        }`}
      />

      <button
        type="button"
        className={`method-item ${
          activeMethod === "account" ? "active" : ""
        }`}
        onClick={() => onChange("account")}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <circle cx="12" cy="8" r="3" />
          <path d="M6.5 20c.5-3.5 2.3-5.5 5.5-5.5s5 2 5.5 5.5" />
        </svg>

        <span>Tài khoản</span>
      </button>

      <button
        type="button"
        className={`method-item ${
          activeMethod === "google" ? "active" : ""
        }`}
        onClick={() => onChange("google")}
      >
        <span>Google</span>

        <svg
          className="google-icon"
          viewBox="0 0 24 24"
        >
          <path
            d="M21.8 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.5c-.2 1.2-.9 2.2-1.9 2.9v2.4h3.1c1.8-1.7 3.1-4.2 3.1-7.1Z"
            fill="#4285F4"
          />
          <path
            d="M12 22c2.8 0 5.1-.9 6.8-2.5l-3.1-2.4c-.9.6-2.1 1-3.7 1-2.8 0-5.2-1.9-6.1-4.5H2.7V16C4.4 19.5 7.9 22 12 22Z"
            fill="#34A853"
          />
          <path
            d="M5.9 13.6c-.2-.6-.3-1.2-.3-1.8s.1-1.2.3-1.8V7.6H2.7C2.1 8.8 1.8 10.4 1.8 12s.3 3.2.9 4.4l3.2-2.8Z"
            fill="#FBBC05"
          />
          <path
            d="M12 5.5c1.6 0 3 .6 4.1 1.7l3-3C17.1 2.5 14.8 1.5 12 1.5c-4.1 0-7.6 2.5-9.3 6.1l3.2 2.4C6.8 7.4 9.2 5.5 12 5.5Z"
            fill="#EA4335"
          />
        </svg>
      </button>
    </div>
  );
};

export default LoginMethodSwitcher;