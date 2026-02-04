import React from "react";
import { useParams } from "react-router-dom";

import { useModules } from "../hooks/useModules";
import { moduleRegistry } from "../modules/registry";
import { ModuleFallback } from "./ModuleFallback";

export const ModuleContainer: React.FC = () => {
  const { modulePath } = useParams<{ modulePath: string }>();
  const { modules, isLoading, error } = useModules();

  console.log("[ModuleContainer] route param modulePath =", modulePath);
  console.log("[ModuleContainer] available modules =", modules);

  // BLOCK 14 — подготовительный UI-слой: контейнер ничего не знает о маршрутизации.
  const resolvedModule = React.useMemo(() => {
    if (!modules || modules.length === 0) {
      return undefined;
    }

    if (modulePath) {
      return modules.find((moduleItem) => moduleItem.path === modulePath);
    }

    return undefined;
  }, [modules, modulePath]);

  console.log("[ModuleContainer] resolved module =", resolvedModule);

  if (isLoading) {
    return <ModuleFallback state="loading" />;
  }

  if (error) {
    return <ModuleFallback state="error" />;
  }

  if (!resolvedModule) {
    return <ModuleFallback state="not_found" />;
  }

  if (!resolvedModule.has_access) {
    return <ModuleFallback state="no_access" />;
  }

  const ModuleComponent = moduleRegistry[resolvedModule.path];

  if (!ModuleComponent) {
    return <ModuleFallback state="not_implemented" />;
  }

  console.log("[ModuleContainer] render module component for =", resolvedModule?.path);

  return <ModuleComponent />;
};
