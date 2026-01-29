// Файл реализует умный редирект с корня, чтобы направлять пользователя сразу в нужный раздел.
// Логика вынесена в отдельный компонент для ясного разделения маршрутов.

import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const SmartRedirect = () => {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to="/app" replace />;
};

export default SmartRedirect;
