import { DndContext, PointerSensor, closestCenter, useSensor, useSensors } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { APP_NAME } from "../config/appConfig";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { useModules } from "../hooks/useModules";
import { PlatformModule } from "../types/module";

type SidebarProps = {
  isCollapsed: boolean;
  onToggle: () => void;
};

type SortableModuleRowProps = {
  moduleItem: PlatformModule;
  isPinned: boolean;
  isEditingModules: boolean;
  onNavigate: (modulePath: string) => void;
};

const SortableModuleRow = ({
  moduleItem,
  isPinned,
  isEditingModules,
  onNavigate,
}: SortableModuleRowProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: moduleItem.id,
    disabled: !isEditingModules,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`module-row ${isPinned ? "pinned" : ""} ${isEditingModules ? "editing" : ""} ${
        isDragging ? "dragging" : ""
      }`}
    >
      {isEditingModules ? (
        <button className="module-handle" type="button" aria-label="Переместить модуль" {...attributes} {...listeners}>
          ≡
        </button>
      ) : null}
      <button
        className="ghost-button module-name"
        type="button"
        onClick={() => {
          if (!isEditingModules) {
            onNavigate(moduleItem.path);
          }
        }}
        data-tooltip={isEditingModules ? undefined : `Перейти: ${moduleItem.title}`}
      >
        <span className="sidebar-text">{moduleItem.title}</span>
      </button>
    </li>
  );
};

const Sidebar = ({ isCollapsed, onToggle }: SidebarProps) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const { modules, isLoading, error, pendingActionId, reload, reorder } = useModules();
  const [isEditingModules, setIsEditingModules] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));
  const visibleModules = useMemo(() => modules.filter((moduleItem) => moduleItem.has_access), [modules]);

  const handleDragEnd = async ({ active, over }: { active: { id: string | number }; over: { id: string | number } | null }) => {
    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = visibleModules.findIndex((moduleItem) => moduleItem.id === active.id);
    const newIndex = visibleModules.findIndex((moduleItem) => moduleItem.id === over.id);
    if (oldIndex < 0 || newIndex < 0) {
      return;
    }

    const nextOrder = arrayMove(visibleModules, oldIndex, newIndex).map((moduleItem) => moduleItem.id);
    await reorder(nextOrder);
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
            <button
              className="ghost-button"
              type="button"
              onClick={() => setIsEditingModules((prev) => !prev)}
              disabled={pendingActionId === "reorder"}
              data-tooltip={isEditingModules ? "Завершить редактирование" : "Редактировать порядок"}
            >
              <span className="sidebar-icon" aria-hidden="true">
                ✎
              </span>
            </button>
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
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={visibleModules.map((moduleItem) => moduleItem.id)} strategy={verticalListSortingStrategy}>
                <ul className="sidebar-text module-list">
                  {visibleModules.map((moduleItem, index) => (
                    <SortableModuleRow
                      key={moduleItem.id}
                      moduleItem={moduleItem}
                      isPinned={index === 0}
                      isEditingModules={isEditingModules}
                      onNavigate={(modulePath) => navigate(`/app/modules/${modulePath}`)}
                    />
                  ))}
                </ul>
              </SortableContext>
            </DndContext>
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
