import React from "react";

type ModuleFallbackState = "loading" | "not_found" | "not_implemented" | "error";

type ModuleFallbackProps = {
  state: ModuleFallbackState;
};

const fallbackCopy: Record<ModuleFallbackState, { title: string; description: string }> = {
  loading: {
    title: "Загрузка модуля",
    description: "Подготавливаем модуль. Пожалуйста, подождите.",
  },
  not_found: {
    title: "Модуль не найден",
    description: "Проверьте корректность запроса или обратитесь к администратору.",
  },
  not_implemented: {
    title: "Модуль не подключён",
    description: "UI этого модуля будет добавлен в следующих блоках.",
  },
  error: {
    title: "Ошибка загрузки",
    description: "Не удалось получить данные о модулях. Попробуйте позже.",
  },
};

export const ModuleFallback: React.FC<ModuleFallbackProps> = ({ state }) => {
  if (state === "error") {
    // Ошибки логируем централизованно только здесь.
    console.error("Ошибка состояния модулей: не удалось получить данные о модулях.");
  }

  const copy = fallbackCopy[state];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: "8px",
        padding: "24px",
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        border: "1px solid #e6e6e6",
      }}
    >
      <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600 }}>{copy.title}</h2>
      <p style={{ margin: 0, fontSize: "14px", color: "#5c5c5c" }}>{copy.description}</p>
    </div>
  );
};
