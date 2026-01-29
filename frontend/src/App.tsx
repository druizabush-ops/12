import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/Layout/AppLayout";
import { RequireAuth } from "./components/RequireAuth";
import { SmartRedirect } from "./components/SmartRedirect";
import { getDefaultAppRoute } from "./config";
import { HelpPage } from "./pages/HelpPage";
import { LoginPage } from "./pages/LoginPage";

// Маршрутизация верхнего уровня вынесена в отдельный компонент.
export const App = () => (
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
      <Route index element={<Navigate to={getDefaultAppRoute()} replace />} />
      <Route path="help" element={<HelpPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);
