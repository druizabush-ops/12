import React from "react";

import { useModules } from "../hooks/useModules";
import { moduleRegistry } from "../modules/registry";
import { ModuleFallback } from "./ModuleFallback";

export type ModuleContainerProps = {
  moduleId?: string;
  modulePath?: string;
};

export const ModuleContainer: React.FC<ModuleContainerProps> = ({ moduleId, modulePath }) => {
  const { modules, isLoading, error } = useModules();

  // BLOCK 14 — подготовительный UI-слой: контейнер ничего не знает о маршрутизации.
  const resolvedModule = React.useMemo(() => {
    if (!modules || modules.length === 0) {
      return undefined;
    }

    if (moduleId) {
      return modules.find((moduleItem) => moduleItem.id === moduleId);
    }

    if (modulePath) {
      return modules.find((moduleItem) => moduleItem.path === modulePath);
    }

    return undefined;
  }, [modules, moduleId, modulePath]);

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

  return <ModuleComponent />;
};
