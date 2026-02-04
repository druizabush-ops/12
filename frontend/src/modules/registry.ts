import React from "react";

import HelpModule from "./help";

// BLOCK 14 — подготовительный UI-слой: реальные модули будут подключены позже.
// Реестр намеренно может быть пустым, маршрутизация модулей здесь не выполняется.
export const moduleRegistry: Record<string, React.ComponentType> = {
  help: HelpModule,
};
