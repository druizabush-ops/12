import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { HelpPage } from "./pages/HelpPage";
import { LoginPage } from "./pages/LoginPage";
import { RequireAuth } from "./routes/RequireAuth";
import { SmartRedirect } from "./routes/SmartRedirect";
import { getDefaultAppRoute } from "./config/appNavigation";
import { useAuth } from "./contexts/AuthContext";

// Главный набор маршрутов приложения.
export const App: React.FC = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/" element={<SmartRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route
          index
          element={<Navigate to={getDefaultAppRoute(user)} replace />}
        />
        <Route path="help" element={<HelpPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
