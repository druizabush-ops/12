// Файл отвечает за боковую панель, чтобы навигация и профиль были всегда под рукой.
// Компонент изолирует логику сайдбара от остального layout.

import { NavLink } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { APP_NAME, MANAGER_PHONE } from "../config/appConfig";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

const navigationItems = [
  { to: "/app", label: "Главная", icon: "🏠" },
  { to: "/app/help", label: "Помощь", icon: "❓" },
];

const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const collapseLabel = isCollapsed ? "Развернуть" : "Свернуть";
  const themeLabel = theme === "light" ? "Темная тема" : "Светлая тема";

  // UX-логика: при сворачивании показываем только иконки с подсказками,
  // чтобы контент не ломался и ширина сайдбара оставалась фиксированной.
  // Это чистое UI-изменение: архитектура shell, маршрутизация и auth (BLOCK 11) не затрагиваются.
  return (
    <aside className={`sidebar ${isCollapsed ? "is-collapsed" : ""}`}>
      <div className="sidebar-header">
        <div className="brand sidebar-item" data-tooltip={APP_NAME}>
          <span className="brand-logo" aria-hidden>
            🏢
          </span>
          <span className="brand-name sidebar-text">{APP_NAME}</span>
        </div>
        <button
          className="ghost-button sidebar-button sidebar-item"
          type="button"
          onClick={onToggle}
          data-tooltip={collapseLabel}
        >
          <span className="sidebar-icon" aria-hidden>
            {isCollapsed ? "→" : "←"}
          </span>
          <span className="sidebar-text">{collapseLabel}</span>
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Основные разделы">
        {navigationItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar-nav-link sidebar-item ${isActive ? "is-active" : ""}`
            }
            data-tooltip={item.label}
          >
            <span className="sidebar-icon" aria-hidden>
              {item.icon}
            </span>
            <span className="sidebar-text">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-section">
        <div
          className="user-card sidebar-item"
          data-tooltip={`Пользователь: ${user ? user.username : "Загрузка..."}`}
        >
          <span className="sidebar-icon" aria-hidden>
            👤
          </span>
          <div className="sidebar-text">
            <span className="user-label">Пользователь</span>
            <strong>{user ? user.username : "Загрузка..."}</strong>
          </div>
        </div>
      </div>

      <div className="sidebar-section">
        <button
          className="secondary-button sidebar-button sidebar-item"
          type="button"
          onClick={toggleTheme}
          data-tooltip={themeLabel}
        >
          <span className="sidebar-icon" aria-hidden>
            {theme === "light" ? "🌙" : "☀️"}
          </span>
          <span className="sidebar-text">{themeLabel}</span>
        </button>
      </div>

      <div className="sidebar-section">
        <div
          className="support-card sidebar-item"
          data-tooltip={`Телефон руководителя: ${MANAGER_PHONE}`}
        >
          <span className="sidebar-icon" aria-hidden>
            ☎️
          </span>
          <div className="sidebar-text">
            <span className="support-label">Телефон руководителя</span>
            <strong>{MANAGER_PHONE}</strong>
          </div>
        </div>
      </div>

      <div className="sidebar-section">
        <div className="modules sidebar-item" data-tooltip="Модули (ожидается)">
          <div className="modules-header">
            <span className="sidebar-icon" aria-hidden>
              🧩
            </span>
            <span className="modules-title sidebar-text">Модули</span>
          </div>
          <ul className="sidebar-text">
            <li>Модуль 1 (ожидается)</li>
            <li>Модуль 2 (ожидается)</li>
            <li>Модуль 3 (ожидается)</li>
          </ul>
        </div>
      </div>

      <div className="sidebar-footer">
        <button
          className="primary-button sidebar-button sidebar-item"
          type="button"
          onClick={logout}
          data-tooltip="Выйти"
        >
          <span className="sidebar-icon" aria-hidden>
            🚪
          </span>
          <span className="sidebar-text">Выйти</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
