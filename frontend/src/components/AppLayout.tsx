// Файл определяет каркас приложения с сайдбаром и зоной контента.
// Отделение layout помогает переиспользовать структуру для всех приватных страниц.

import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

const AppLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className={`app-shell ${isCollapsed ? "collapsed" : ""}`}>
      <Sidebar isCollapsed={isCollapsed} onToggle={() => setIsCollapsed((prev) => !prev)} />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
