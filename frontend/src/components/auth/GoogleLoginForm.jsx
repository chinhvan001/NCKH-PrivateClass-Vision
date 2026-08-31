import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebase";
import { saveAdminSession } from "../../utils/AuthSession";

const GoogleLoginForm = ({ onLogin }) => {

  const handleGoogleLogin = async () => {
    try {
      const result = await signInWithPopup(
        auth, 
        googleProvider
      );

      const user = result.user;

      const idToken = await user.getIdToken();

      const response = await fetch(
        "http://127.0.0.1:5000/api/auth/google",
        {
          method: "POST",
          headers: {
            // "Authorization": `Bearer ${idToken}`,
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            idToken: idToken,
          }),
        }
      );


      const data = await response.json();

      console.log("Backend response: ", data);

      if (response.ok && data.success) {
        console.log("Admin login successful");

        saveAdminSession(data.user, idToken);

        onLogin(data.user);

        return;
      }

      alert(data.message)

      // console.log("Google Login Success");

      // console.log("UID: ", user.uid);
      // console.log("Email: ", user.email);
      // console.log("Name: ", user.displayName);
      // console.log("Photo: ", user.photoURL);
    } catch (error) {
      console.error("Google Login Error: ", error);

      // console.error("Error code: ", error.code);
      // console.errro("Error message: ", error.message);

      alert("Đăng nhập google thất bại");
    }
  };

  return (
    <div className="google-login-container">
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