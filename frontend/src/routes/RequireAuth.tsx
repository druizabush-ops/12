// Файл защищает приватные маршруты, чтобы пользователь без токена не видел приложение.
// Проверка вынесена отдельно, чтобы не дублировать логику в каждом маршруте.

import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import LoadingPage from "../pages/LoadingPage";

const RequireAuth = ({ children }: { children: React.ReactNode }) => {
  const { token, user, isLoading } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading || !user) {
    return <LoadingPage />;
  }

  return <>{children}</>;
};

export default RequireAuth;
