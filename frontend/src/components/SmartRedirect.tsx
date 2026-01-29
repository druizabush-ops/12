import { Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

// Умный редирект с корня: отправляем на /login или /app в зависимости от токена.
export const SmartRedirect = () => {
  const { token } = useAuth();

  return <Navigate to={token ? "/app" : "/login"} replace />;
};
