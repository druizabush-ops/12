// Централизованные настройки приложения и данные, которые могут быть заменены позже.

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const SUPERVISOR_PHONE = "+7 (900) 000-00-00";

// Единая точка определения стартового маршрута внутри /app.
export const getDefaultAppRoute = () => "/app/help";
