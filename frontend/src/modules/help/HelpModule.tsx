import { APP_NAME } from "../../config/appConfig";
import { ModuleRuntimeProps } from "../../types/module";

// BLOCK 18 SDK contract (UI module):
// ✅ Can: render module UI, keep local UI state, receive platform props as pure data.
// ❌ Cannot: fetch API directly, compute RBAC/permissions, navigate, or import container/fallback/router internals.
const HelpModule = (_props: ModuleRuntimeProps) => {
  console.log("[HelpModule] initialized");

  return (
    <div className="page">
      <div className="page-header">
        <h2>Справка</h2>
        <p>Быстрый старт для работы в платформе.</p>
      </div>
      <div className="page-card">
        <h3>Добро пожаловать в {APP_NAME}</h3>
        <p>Выберите доступный модуль в левом меню и следуйте подсказкам на экране.</p>
        <p className="muted">
          Если нужного модуля нет, обратитесь к руководителю или администратору платформы.
        </p>
      </div>
    </div>
  );
};

export default HelpModule;
