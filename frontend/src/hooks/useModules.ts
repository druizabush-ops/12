// Хук хранит состояние реестра модулей BLOCK 13 как платформенный слой.
// UI модулей не реализуется, backend остаётся источником истины, поэтому запросы централизованы.
// Логика вынесена сюда, чтобы Sidebar оставался тонким UI-слоем без сетевых деталей.

import { useCallback, useEffect, useState } from "react";
import { fetchModules, updateModulesOrder, updatePrimaryModule } from "../api/modules";
import { useAuth } from "../contexts/AuthContext";
import { PlatformModule } from "../types/module";

type UseModulesState = {
  modules: PlatformModule[];
  isLoading: boolean;
  error: string | null;
  pendingActionId: string | null;
  reload: () => Promise<void>;
  setPrimary: (moduleId: string | null) => Promise<void>;
  reorder: (orderedIds: string[]) => Promise<void>;
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
      const data = await fetchModules(token);
      setModules(data);
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

  const setPrimary = useCallback(
    async (moduleId: string | null) => {
      if (!token) {
        return;
      }

      setPendingActionId(moduleId ?? "primary-reset");
      setError(null);

      try {
        const data = await updatePrimaryModule(token, moduleId);
        setModules(data);
      } catch (err) {
        console.error("Ошибка обновления основного модуля", err);
        setError("Не удалось обновить основной модуль");
      } finally {
        setPendingActionId(null);
      }
    },
    [token]
  );

  const reorder = useCallback(
    async (orderedIds: string[]) => {
      if (!token) {
        return;
      }

      const previousModules = modules;
      const optimisticModules = orderedIds
        .map((id) => previousModules.find((module) => module.id === id))
        .filter((module): module is PlatformModule => Boolean(module));

      if (optimisticModules.length === previousModules.length) {
        setModules(optimisticModules);
      }

      setPendingActionId("reorder");
      setError(null);

      try {
        const data = await updateModulesOrder(token, orderedIds);
        setModules(data);
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
    setPrimary,
    reorder,
  };
};
