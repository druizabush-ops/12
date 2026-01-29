import React from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { LoadingPage } from "../pages/LoadingPage";

// Защищает маршруты /app и обрабатывает состояние загрузки пользователя.
export const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, user, isLoading } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading || !user) {
    return <LoadingPage />;
  }

  return <>{children}</>;
};
