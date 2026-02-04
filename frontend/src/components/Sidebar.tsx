// Файл отвечает за боковую панель, чтобы навигация и профиль были всегда под рукой.
// Компонент изолирует логику сайдбара от остального layout.

import { useNavigate } from "react-router-dom";
import { APP_NAME, MANAGER_PHONE } from "../config/appConfig";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { useModules } from "../hooks/useModules";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const { modules, isLoading, error, pendingActionId, reload, setPrimary, reorder } = useModules();

  const isPending = pendingActionId !== null;
  const visibleModules = modules.filter((moduleItem) => moduleItem.has_access);
  const canReorder = modules.length === visibleModules.length;

  const handleMove = (moduleId: string, direction: "up" | "down") => {
    if (!canReorder) {
      return;
    }

    const currentIndex = visibleModules.findIndex((moduleItem) => moduleItem.id === moduleId);
    if (currentIndex === -1) {
      return;
    }

    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= visibleModules.length) {
      return;
    }

    const nextOrder = [...visibleModules];
    [nextOrder[currentIndex], nextOrder[targetIndex]] = [
      nextOrder[targetIndex],
      nextOrder[currentIndex],
    ];
    void reorder(nextOrder.map((moduleItem) => moduleItem.id));
  };

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
          {isLoading ? (
            <p className="sidebar-text">Загрузка модулей...</p>
          ) : error ? (
            <div className="sidebar-text">
              <p>{error}</p>
              <button className="ghost-button" type="button" onClick={reload}>
                Повторить
              </button>
            </div>
          ) : visibleModules.length === 0 ? (
            <p className="sidebar-text">Нет доступных модулей</p>
          ) : (
            <ul className="sidebar-text">
              {visibleModules.map((moduleItem, index) => (
                <li key={moduleItem.id}>
                  <div>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => navigate(`/app/modules/${moduleItem.path}`)}
                      data-tooltip={`Перейти: ${moduleItem.title}`}
                    >
                      <span className="sidebar-text">{moduleItem.title}</span>
                    </button>
                    {moduleItem.is_primary ? (
                      <span className="sidebar-text"> (основной)</span>
                    ) : null}
                  </div>
                  <div>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => setPrimary(moduleItem.is_primary ? null : moduleItem.id)}
                      disabled={isPending}
                      data-tooltip={
                        moduleItem.is_primary ? "Снять основной модуль" : "Сделать основным"
                      }
                    >
                      <span className="sidebar-icon" aria-hidden="true">
                        ⭐
                      </span>
                    </button>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => handleMove(moduleItem.id, "up")}
                      disabled={isPending || !canReorder || index === 0}
                      data-tooltip="Поднять выше"
                    >
                      <span className="sidebar-icon" aria-hidden="true">
                        ↑
                      </span>
                    </button>
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => handleMove(moduleItem.id, "down")}
                      disabled={isPending || !canReorder || index === visibleModules.length - 1}
                      data-tooltip="Опустить ниже"
                    >
                      <span className="sidebar-icon" aria-hidden="true">
                        ↓
                      </span>
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
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
