import { NavLink } from "react-router-dom";

import { SUPERVISOR_PHONE } from "../config";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

// Сайдбар содержит информацию о пользователе, навигацию и элементы управления.
export const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside className={isCollapsed ? "sidebar collapsed" : "sidebar"}>
      <div className="sidebar-header">
        <button type="button" className="collapse-button" onClick={onToggle}>
          {isCollapsed ? "→" : "←"}
        </button>
        {!isCollapsed && <span className="brand">Новый Дом</span>}
      </div>

      {!isCollapsed && (
        <div className="sidebar-section">
          <p className="section-title">Пользователь</p>
          <p className="user-name">{user?.username ?? "—"}</p>
          <button type="button" className="secondary-button" onClick={logout}>
            Выйти
          </button>
        </div>
      )}

      {!isCollapsed && (
        <div className="sidebar-section">
          <p className="section-title">Тема</p>
          <button type="button" className="secondary-button" onClick={toggleTheme}>
            Переключить на {theme === "light" ? "тёмную" : "светлую"}
          </button>
        </div>
      )}

      {!isCollapsed && (
        <div className="sidebar-section">
          <p className="section-title">Контакт руководителя</p>
          <p className="muted">{SUPERVISOR_PHONE}</p>
        </div>
      )}

      {!isCollapsed && (
        <div className="sidebar-section">
          <p className="section-title">Модули</p>
          <ul className="module-list">
            <li className="module-item">Скоро появится модуль 1</li>
            <li className="module-item">Скоро появится модуль 2</li>
            <li className="module-item">Скоро появится модуль 3</li>
          </ul>
        </div>
      )}

      {!isCollapsed && (
        <div className="sidebar-section">
          <NavLink to="/app/help" className="help-link">
            Инструкция
          </NavLink>
        </div>
      )}
    </aside>
  );
};
