import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

type ModuleFallbackState = "loading" | "not_found" | "not_implemented" | "error" | "no_access";

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
  no_access: {
    title: "Нет доступа",
    description: "Вы не можете открыть этот модуль.",
  },
  error: {
    title: "Ошибка загрузки",
    description: "Не удалось получить данные о модулях. Попробуйте позже.",
  },
};

export const ModuleFallback: React.FC<ModuleFallbackProps> = ({ state }) => {
  const navigate = useNavigate();

  if (state === "error") {
    // Ошибки логируем централизованно только здесь.
    console.error("Ошибка состояния модулей: не удалось получить данные о модулях.");
  }

  useEffect(() => {
    if (state !== "no_access") {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      navigate("/app", { replace: true });
    }, 2000);

    return () => window.clearTimeout(timeoutId);
  }, [navigate, state]);

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
      <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600 }}>
        {state === "no_access" ? <span aria-hidden="true">🔒 </span> : null}
        {copy.title}
      </h2>
      <p style={{ margin: 0, fontSize: "14px", color: "#5c5c5c" }}>{copy.description}</p>
    </div>
  );
};
