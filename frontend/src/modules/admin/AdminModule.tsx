import { APP_NAME } from "../../config/appConfig";

// BLOCK 18 SDK contract (UI module):
// ✅ Can: render module UI, keep local UI state, receive future platform props.
// ❌ Cannot: fetch API directly, implement RBAC/permissions, navigate, or import container/fallback/router internals.
const AdminModule = () => {
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
      </div>
    </div>
  );
};

export default AdminModule;
