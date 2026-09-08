import { Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/DashBoard";
import AccountManagement from "./pages/AccountManagement";
import SessionManagement from "./pages/SessionManagement";
import SessionDetail from "./pages/SessionDetail";

import { getAdminSession, clearAdminSession } from "./utils/AuthSession";

function ProtectedRoute({ children }) {
  const session = getAdminSession();

  if (!session) {
    clearAdminSession();
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/account-management"
        element={
          <ProtectedRoute>
            <AccountManagement />
          </ProtectedRoute>
        }
      />

      <Route
        path="/session-management"
        element={
          <ProtectedRoute>
            <SessionManagement />
          </ProtectedRoute>
        }
      />

      <Route
        path="/session-management/:sessionId"
        element={
          <ProtectedRoute>
            <SessionDetail />
          </ProtectedRoute>
        }
      />

      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
