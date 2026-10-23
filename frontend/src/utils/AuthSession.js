import { signOut } from "firebase/auth";

import { auth } from "../firebase";

const SESSION_DURATION = 30 * 60 * 1000; // 30 phút

export const saveAdminSession = (user, idToken) => {
  const expiresAt = Date.now() + SESSION_DURATION;

  localStorage.setItem("adminUser", JSON.stringify(user));
  localStorage.setItem("idToken", idToken);
  localStorage.setItem("sessionExpiresAt", expiresAt.toString());
};

export const getAdminSession = () => {
  const storedUser = localStorage.getItem("adminUser");
  const idToken = localStorage.getItem("idToken");
  const expiresAt = localStorage.getItem("sessionExpiresAt");

  if (!storedUser || !idToken || !expiresAt) {
    return null;
  }

  const now = Date.now();

  if (now >= Number(expiresAt)) {
    clearAdminSession();
    return null;
  }

  try {
    const user = JSON.parse(storedUser);

    return {
      user,
      idToken,
      expiresAt: Number(expiresAt),
    };
  } catch (error) {
    console.error("Không thể đọc admin session:", error);
    clearAdminSession();
    return null;
  }
};

export const clearAdminSession = () => {
  localStorage.removeItem("adminUser");
  localStorage.removeItem("idToken");
  localStorage.removeItem("sessionExpiresAt");
};

export const logoutAdmin = async (navigate) => {
  try {
    if (auth) {
      await signOut(auth);
    }
  } catch (error) {
    console.error("Firebase logout error:", error);
  }

  clearAdminSession();

  if (navigate) {
    navigate("/login", { replace: true });
  }

  return true;
};