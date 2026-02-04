import React from "react";
import { useParams } from "react-router-dom";

import { useModules } from "../hooks/useModules";
import { moduleRegistry } from "../modules/registry";
import { ModuleFallback } from "./ModuleFallback";

export type ModuleContainerProps = {
  moduleId?: string;
};

export const ModuleContainer: React.FC<ModuleContainerProps> = ({ moduleId }) => {
  const { modulePath } = useParams<{ modulePath: string }>();
  console.log("[ModuleContainer] route param modulePath =", modulePath);
  const { modules, isLoading, error } = useModules();
  console.log("[ModuleContainer] available modules =", modules);

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

  console.log("[ModuleContainer] resolve module by path:", resolvedModule?.path);
  const ModuleComponent = moduleRegistry[resolvedModule.path];

  if (!ModuleComponent) {
    return <ModuleFallback state="not_implemented" />;
  }

  console.log("[ModuleContainer] render module component for:", resolvedModule?.path);
  return <ModuleComponent />;
};
