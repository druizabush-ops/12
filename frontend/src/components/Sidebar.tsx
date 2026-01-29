import React from "react";
import { APP_BRAND, MANAGER_PHONE } from "../config/appConfig";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

// Боковая панель платформы: бренд, профиль, быстрые настройки и список модулей.
export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const { user, signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside className={`sidebar ${isCollapsed ? "sidebar--collapsed" : ""}`}>
      <div className="sidebar__header">
        <div>
          <p className="sidebar__brand">{APP_BRAND}</p>
          <p className="sidebar__subtitle">Платформа управления</p>
        </div>
        <button
          className="sidebar__collapse"
          type="button"
          onClick={onToggle}
          aria-label={isCollapsed ? "Развернуть меню" : "Свернуть меню"}
        >
          {isCollapsed ? "»" : "«"}
        </button>
      </div>

      <div className="sidebar__section">
        <p className="sidebar__label">Пользователь</p>
        <p className="sidebar__value">{user?.username ?? "—"}</p>
        <button className="sidebar__link" type="button" onClick={signOut}>
          Выйти
        </button>
      </div>

      <div className="sidebar__section">
        <p className="sidebar__label">Тема интерфейса</p>
        <button className="sidebar__toggle" type="button" onClick={toggleTheme}>
          Сейчас: {theme === "light" ? "Светлая" : "Тёмная"}
        </button>
      </div>

      <div className="sidebar__section">
        <p className="sidebar__label">Телефон руководителя</p>
        <p className="sidebar__value">{MANAGER_PHONE}</p>
      </div>

      <div className="sidebar__section">
        <p className="sidebar__label">Модули</p>
        <ul className="sidebar__modules">
          <li>Основной модуль (ожидает подключения)</li>
          <li>Отчёты (placeholder)</li>
          <li>Заявки (placeholder)</li>
        </ul>
      </div>
    </aside>
  );
};
