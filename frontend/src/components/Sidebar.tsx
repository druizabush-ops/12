// Файл отвечает за боковую панель, чтобы навигация и профиль были всегда под рукой.
// Компонент изолирует логику сайдбара от остального layout.

import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { APP_NAME, MANAGER_PHONE } from "../config/appConfig";
import { useModules } from "../hooks/useModules";

const resolveModulePath = (path: string) => (path.startsWith("/") ? path : `/app/${path}`);

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { modules, isLoading, error, pendingActionId, reload, reorder, setPrimary } = useModules();
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const activeModuleId = useMemo(() => {
    const activeModule = modules.find((module) =>
      location.pathname.startsWith(resolveModulePath(module.path))
    );

    return activeModule?.id ?? null;
  }, [modules, location.pathname]);

  useEffect(() => {
    if (error) {
      console.error("Ошибка загрузки модулей:", error);
    }
  }, [error]);

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
            <div>
              <p className="sidebar-text">Разделы временно недоступны</p>
              <button className="ghost-button" type="button" onClick={reload}>
                <span className="sidebar-text">Повторить</span>
              </button>
            </div>
          ) : modules.length === 0 ? (
            <p className="sidebar-text">Нет доступных модулей</p>
          ) : (
            <ul>
              {modules.map((module, index) => {
                const modulePath = resolveModulePath(module.path);
                const isActive = activeModuleId === module.id;
                const isPrimary = module.isPrimary;
                const isMenuOpen = openMenuId === module.id;
                const isPending = pendingActionId !== null;
                const menuTooltip = isPrimary ? "Снять закрепление" : "Закрепить как основной";

                return (
                  <li key={module.id}>
                    <div
                      tabIndex={0}
                      onBlur={(event) => {
                        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                          setOpenMenuId(null);
                        }
                      }}
                    >
                      <button
                        className="ghost-button"
                        type="button"
                        onClick={() => navigate(modulePath)}
                        data-tooltip={module.title}
                        aria-current={isActive ? "page" : undefined}
                      >
                        <span className="sidebar-icon" aria-hidden="true">
                          {isActive ? "▶" : "•"}
                        </span>
                        <span className="sidebar-text">
                          {module.title} {isPrimary ? "⭐" : ""}
                        </span>
                      </button>
                      <button
                        className="ghost-button"
                        type="button"
                        onClick={() =>
                          setOpenMenuId((current) => (current === module.id ? null : module.id))
                        }
                        aria-haspopup="menu"
                        aria-expanded={isMenuOpen}
                        data-tooltip="Действия"
                      >
                        <span className="sidebar-icon" aria-hidden="true">
                          ⋯
                        </span>
                        <span className="sidebar-text">Действия</span>
                      </button>
                      {isMenuOpen && (
                        <div role="menu">
                          <button
                            className="ghost-button"
                            type="button"
                            disabled={isPending}
                            onClick={async () => {
                              await setPrimary(isPrimary ? null : module.id);
                              setOpenMenuId(null);
                            }}
                            data-tooltip={menuTooltip}
                          >
                            <span className="sidebar-icon" aria-hidden="true">
                              {isPrimary ? "📌" : "📍"}
                            </span>
                            <span className="sidebar-text">
                              {isPrimary ? "Снять закрепление" : "Закрепить как основной"}
                            </span>
                          </button>
                          <button
                            className="ghost-button"
                            type="button"
                            disabled={isPending || index === 0}
                            onClick={async () => {
                              await reorder(module.id, "up");
                              setOpenMenuId(null);
                            }}
                            data-tooltip="Переместить вверх"
                          >
                            <span className="sidebar-icon" aria-hidden="true">
                              ↑
                            </span>
                            <span className="sidebar-text">Переместить вверх</span>
                          </button>
                          <button
                            className="ghost-button"
                            type="button"
                            disabled={isPending || index === modules.length - 1}
                            onClick={async () => {
                              await reorder(module.id, "down");
                              setOpenMenuId(null);
                            }}
                            data-tooltip="Переместить вниз"
                          >
                            <span className="sidebar-icon" aria-hidden="true">
                              ↓
                            </span>
                            <span className="sidebar-text">Переместить вниз</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
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
