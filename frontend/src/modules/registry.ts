import React from "react";

import AdminModule from "./admin";
import HelpModule from "./help";

// BLOCK 14 — подготовительный UI-слой: реальные модули будут подключены позже.
// Реестр намеренно может быть пустым, маршрутизация модулей здесь не выполняется.
export const moduleRegistry: Record<string, React.ComponentType> = {
  admin: AdminModule,
  help: HelpModule,
};
