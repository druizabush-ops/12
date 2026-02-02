// Хук разделяет ответственность: он занимается данными и действиями модулей, а Sidebar остаётся только отображением.
// Модульный UI не реализуется, мы готовим лишь список и управление для shell.

import { useCallback, useEffect, useState } from "react";
import { fetchModules, updateModulesOrder, updatePrimaryModule } from "../api/modules";
import { useAuth } from "../contexts/AuthContext";
import { Module } from "../types/module";

const EMPTY_MODULES: Module[] = [];

export const useModules = () => {
  const { token } = useAuth();
  const [modules, setModules] = useState<Module[]>(EMPTY_MODULES);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!token) {
      setModules(EMPTY_MODULES);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchModules(token);
      setModules(data);
    } catch (loadError) {
      setModules(EMPTY_MODULES);
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить модули");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setModules(EMPTY_MODULES);
      setIsLoading(false);
      setError(null);
      return;
    }

    void reload();
  }, [token, reload]);

  const setPrimary = useCallback(
    async (moduleId: string | null) => {
      if (!token) {
        return;
      }

      setPendingActionId(moduleId ?? "primary-reset");
      setError(null);

      try {
        await updatePrimaryModule(token, moduleId);
        await reload();
      } catch (updateError) {
        setError(updateError instanceof Error ? updateError.message : "Не удалось обновить модуль");
      } finally {
        setPendingActionId(null);
      }
    },
    [token, reload]
  );

  const reorder = useCallback(
    async (moduleId: string, direction: "up" | "down") => {
      if (!token) {
        return;
      }

      const currentIndex = modules.findIndex((item) => item.id === moduleId);
      const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;

      if (currentIndex < 0 || targetIndex < 0 || targetIndex >= modules.length) {
        return;
      }

      const previousModules = modules;
      const nextModules = [...modules];
      const [movedModule] = nextModules.splice(currentIndex, 1);
      nextModules.splice(targetIndex, 0, movedModule);

      setPendingActionId(moduleId);
      setError(null);
      setModules(nextModules);

      try {
        await updateModulesOrder(
          token,
          nextModules.map((item) => item.id)
        );
        await reload();
      } catch (updateError) {
        setModules(previousModules);
        setError(updateError instanceof Error ? updateError.message : "Не удалось изменить порядок");
      } finally {
        setPendingActionId(null);
      }
    },
    [modules, token, reload]
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
