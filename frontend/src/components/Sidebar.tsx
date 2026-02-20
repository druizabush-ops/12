// Файл отвечает за боковую панель, чтобы навигация и профиль были всегда под рукой.
// Компонент изолирует логику сайдбара от остального layout.

import { useNavigate } from "react-router-dom";
import { APP_NAME } from "../config/appConfig";
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
        </button>
      </div>
      <div className="sidebar-section">
        <div className="sidebar-user-row" data-tooltip="Пользователь">
          <span className="sidebar-icon" aria-hidden="true">
            👤
          </span>
          <strong className="sidebar-text user-name">{user ? user.username : "Загрузка..."}</strong>
        </div>
      </div>
      <div className="sidebar-section">
        <div className="modules" data-tooltip="Модули">
          <div className="modules-header">
            <span className="sidebar-icon" aria-hidden="true">
              🧩
            </span>
            <span className="modules-title sidebar-text">МОДУЛИ</span>
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
                <li key={moduleItem.id} className="module-row">
                  <button
                    className="ghost-button module-name"
                    type="button"
                    onClick={() => navigate(`/app/modules/${moduleItem.path}`)}
                    data-tooltip={`Перейти: ${moduleItem.title}`}
                  >
                    <span className="sidebar-text">{moduleItem.title}</span>
                    {moduleItem.is_primary ? <span className="sidebar-text">(основной)</span> : null}
                  </button>
                  <div className="module-actions">
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
      <div className="sidebar-section">
        <div className="sidebar-contacts">
          <div className="contacts-title sidebar-text">КОНТАКТЫ</div>

          <div className="contact-item">
            <div className="contact-label sidebar-text">Магазин</div>
            <div className="sidebar-text">8 831 93 51816</div>
          </div>

          <div className="contact-item">
            <div className="contact-label sidebar-text">Бухгалтерия</div>
            <div className="sidebar-text">8 831 93 52558</div>
          </div>

          <div className="contact-item">
            <div className="contact-label sidebar-text">Руководитель отдела</div>
            <div className="sidebar-text">+79087319582 Светлана Зудихина</div>
          </div>

          <div className="contact-item">
            <div className="contact-label sidebar-text">Техподдержка</div>
            <div className="sidebar-text">+79991215130 Николай</div>
          </div>

          <div className="contact-item">
            <a href="https://t.me/ndmaksimov" target="_blank" rel="noreferrer" className="telegram-link">
              <span className="sidebar-text">https://t.me/ndmaksimov</span>
            </a>
          </div>
        </div>
      </div>
      <div className="sidebar-footer">
        <button
          className="theme-icon-only"
          type="button"
          onClick={toggleTheme}
          data-tooltip={theme === "light" ? "Темная тема" : "Светлая тема"}
        >
          <span className="sidebar-icon" aria-hidden="true">
            🌓
          </span>
        </button>
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
