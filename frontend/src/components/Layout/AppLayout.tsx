import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "../Sidebar";

// Shell-раскладка приложения с сайдбаром и основной областью контента.
export const AppLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar isCollapsed={isCollapsed} onToggle={() => setIsCollapsed((prev) => !prev)} />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
};
