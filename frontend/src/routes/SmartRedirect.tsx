import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

// Умная точка входа: отправляет на /login без токена и на /app при наличии токена.
export const SmartRedirect: React.FC = () => {
  const { token } = useAuth();

  return <Navigate to={token ? "/app" : "/login"} replace />;
};
