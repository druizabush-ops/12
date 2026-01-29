import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { LoadingScreen } from "../components/LoadingScreen";

// Защитный компонент для приватных маршрутов /app.
export const RequireAuth: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { token, user, isLoading } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading || !user) {
    return <LoadingScreen />;
  }

  return <>{children}</>;
};
