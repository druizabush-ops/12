import React from "react";

// Простая заглушка для ожидания ответа /auth/me.
export const LoadingScreen: React.FC = () => (
  <div className="loading-screen">
    <div className="loading-card">
      <h2>Загрузка</h2>
      <p>Проверяем данные пользователя...</p>
    </div>
  </div>
);
