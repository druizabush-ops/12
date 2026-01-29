import { UserProfile } from "../types/auth";

// Это единственная точка, где определяется стартовый маршрут внутри /app.
// Сейчас возвращаем справочную страницу, позже можно добавить логику выбора модуля.
export const getDefaultAppRoute = (user: UserProfile | null): string => {
  void user;
  return "/app/help";
};
