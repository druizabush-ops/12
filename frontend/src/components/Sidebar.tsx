// Файл отвечает за боковую панель, чтобы навигация и профиль были всегда под рукой.
// Компонент изолирует логику сайдбара от остального layout.

import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { APP_NAME, MANAGER_PHONE } from "../config/appConfig";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand" data-tooltip="Новый Дом">
          <span className="brand-logo">🏢</span>
          <span className="brand-name sidebar-text">{APP_NAME}</span>
        </div>
        <button
          className="ghost-button"
          type="button"
          onClick={onToggle}
          data-tooltip={isCollapsed ? "Развернуть" : "Свернуть"}
        >
          <span className="sidebar-icon">{isCollapsed ? "→" : "←"}</span>
          <span className="sidebar-text">{isCollapsed ? "Развернуть" : "Свернуть"}</span>
        </button>
      </div>
      <div className="sidebar-section">
        <div className="user-card" data-tooltip="Пользователь">
          <span className="sidebar-icon" aria-hidden="true">
            👤
          </span>
          <span className="user-label sidebar-text">Пользователь</span>
          <strong className="sidebar-text">{user ? user.username : "Загрузка..."}</strong>
        </div>
      </div>
      <div className="sidebar-section">
        <button
          className="secondary-button"
          type="button"
          onClick={toggleTheme}
          data-tooltip={theme === "light" ? "Темная тема" : "Светлая тема"}
        >
          <span className="sidebar-icon" aria-hidden="true">
            🌓
          </span>
          <span className="sidebar-text">
            {theme === "light" ? "Темная тема" : "Светлая тема"}
          </span>
        </button>
      </div>
      <div className="sidebar-section">
        <div className="support-card" data-tooltip="Телефон руководителя">
          <span className="sidebar-icon" aria-hidden="true">
            📞
          </span>
          <span className="support-label sidebar-text">Телефон руководителя</span>
          <strong className="sidebar-text">{MANAGER_PHONE}</strong>
        </div>
      </div>
      <div className="sidebar-section">
        <div className="modules" data-tooltip="Модули">
          <div className="modules-header">
            <span className="sidebar-icon" aria-hidden="true">
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
        <button className="primary-button" type="button" onClick={logout} data-tooltip="Выйти">
          <span className="sidebar-icon" aria-hidden="true">
            🚪
          </span>
          <span className="sidebar-text">Выйти</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
