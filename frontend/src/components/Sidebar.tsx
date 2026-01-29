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
        <div className="brand">
          <span className="brand-logo">🏢</span>
          {!isCollapsed && <span className="brand-name">{APP_NAME}</span>}
        </div>
        <button className="ghost-button" type="button" onClick={onToggle}>
          {isCollapsed ? "→" : "←"}
        </button>
      </div>
      <div className="sidebar-section">
        <div className="user-card">
          <span className="user-label">Пользователь</span>
          <strong>{user ? user.username : "Загрузка..."}</strong>
        </div>
      </div>
      <div className="sidebar-section">
        <button className="secondary-button" type="button" onClick={toggleTheme}>
          {theme === "light" ? "Темная тема" : "Светлая тема"}
        </button>
      </div>
      <div className="sidebar-section">
        <div className="support-card">
          <span className="support-label">Телефон руководителя</span>
          <strong>{MANAGER_PHONE}</strong>
        </div>
      </div>
      <div className="sidebar-section">
        <div className="modules">
          <span className="modules-title">Модули</span>
          <ul>
            <li>Модуль 1 (ожидается)</li>
            <li>Модуль 2 (ожидается)</li>
            <li>Модуль 3 (ожидается)</li>
          </ul>
        </div>
      </div>
      <div className="sidebar-footer">
        <button className="primary-button" type="button" onClick={logout}>
          Выйти
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
