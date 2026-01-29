import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";

// Shell-лейаут: боковая панель и область контента, готовая к подключению модулей.
export const AppLayout: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <div className={`app-shell ${isCollapsed ? "app-shell--collapsed" : ""}`}>
      <Sidebar
        isCollapsed={isCollapsed}
        onToggle={() => setIsCollapsed((prev) => !prev)}
      />
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  );
};
