import { APP_NAME } from "../../config/appConfig";
import { ModuleRuntimeProps } from "../../types/module";

// BLOCK 18 SDK contract (UI module):
// ✅ Can: render module UI, keep local UI state, receive platform props as pure data.
// ❌ Cannot: fetch API directly, compute RBAC/permissions, navigate, or import container/fallback/router internals.
const AdminModule = ({ permissions }: ModuleRuntimeProps) => {
  console.log("[AdminModule] initialized");

  return (
    <div className="page">
      <div className="page-header">
        <h2>Администрирование</h2>
        <p>Служебный модуль платформы {APP_NAME}.</p>
      </div>
      <div className="page-card">
        <p>Этот экран содержит только UI-оболочку административного модуля.</p>
        <p className="muted">Права доступа и маршрутизация обрабатываются платформой вне UI-модуля.</p>
        {permissions?.delete ? <button type="button">Удалить</button> : null}
      </div>
    </div>
  );
};

export default AdminModule;
