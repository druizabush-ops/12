import { useCallback, useEffect, useState } from "react";
import { fetchModules } from "../api/modules";
import { fetchSidebarSettings, saveSidebarModulesOrder } from "../api/sidebarSettings";
import { useAuth } from "../contexts/AuthContext";
import { PlatformModule } from "../types/module";

type UseModulesState = {
  modules: PlatformModule[];
  isLoading: boolean;
  error: string | null;
  pendingActionId: string | null;
  reload: () => Promise<void>;
  reorder: (orderedIds: string[]) => Promise<void>;
};

const applyModulesOrder = (allModules: PlatformModule[], modulesOrder: string[] | null): PlatformModule[] => {
  if (!modulesOrder || modulesOrder.length === 0) {
    return allModules;
  }

  const modulesById = new Map(allModules.map((module) => [module.id, module]));
  const orderedModules: PlatformModule[] = [];

  modulesOrder.forEach((moduleId) => {
    const module = modulesById.get(moduleId);
    if (module) {
      orderedModules.push(module);
      modulesById.delete(moduleId);
    }
  });

  allModules.forEach((module) => {
    if (modulesById.has(module.id)) {
      orderedModules.push(module);
    }
  });

  return orderedModules;
};

export const useModules = (): UseModulesState => {
  const { token } = useAuth();
  const [modules, setModules] = useState<PlatformModule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [modulesData, modulesOrder] = await Promise.all([
        fetchModules(token),
        fetchSidebarSettings(token),
      ]);
      setModules(applyModulesOrder(modulesData, modulesOrder));
    } catch (err) {
      console.error("Ошибка загрузки модулей", err);
      setError("Не удалось загрузить модули");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!token) {
      setModules([]);
      setError(null);
    }
  }, [token]);

  const reorder = useCallback(
    async (orderedIds: string[]) => {
      if (!token) {
        return;
      }

      const previousModules = modules;
      const optimisticModules = orderedIds
        .map((id) => previousModules.find((module) => module.id === id))
        .filter((module): module is PlatformModule => Boolean(module));
      const remainingModules = previousModules.filter((module) => !orderedIds.includes(module.id));
      setModules([...optimisticModules, ...remainingModules]);

      setPendingActionId("reorder");
      setError(null);

      try {
        await saveSidebarModulesOrder(token, orderedIds);
      } catch (err) {
        console.error("Ошибка сохранения порядка модулей", err);
        setError("Не удалось сохранить порядок модулей");
        setModules(previousModules);
      } finally {
        setPendingActionId(null);
      }
    },
    [modules, token]
  );

  return {
    modules,
    isLoading,
    error,
    pendingActionId,
    reload,
    reorder,
  };
};
