// Файл держит запросы модулей отдельно от UI, чтобы Sidebar не содержал сетевую логику.
// Бэкенд остаётся источником истины, мы только нормализуем данные для интерфейса.

import { apiFetch } from "./client";
import { Module, ModuleDto } from "../types/module";

const normalizeModule = (item: ModuleDto, index: number): Module => {
  const id = item.id || item.name || `module-${index}`;
  const name = item.name || item.id || `module-${index}`;
  const title = item.title || item.name || item.id || `Модуль ${index + 1}`;
  const path = item.path || item.name || item.id || id;

  return {
    id,
    name,
    title,
    path,
    icon: item.icon ?? null,
    isPrimary: item.is_primary ?? false,
    order: item.order ?? index,
  };
};

const sortModules = (modules: Module[]) =>
  [...modules].sort((left, right) => left.order - right.order);

export const fetchModules = async (token: string): Promise<Module[]> => {
  const data = await apiFetch<ModuleDto[]>("/modules", { method: "GET" }, token);
  const normalized = data.map((item, index) => normalizeModule(item, index));
  return sortModules(normalized);
};

export const updatePrimaryModule = async (token: string, moduleId: string | null) =>
  apiFetch<void>(
    "/modules/primary",
    {
      method: "PATCH",
      body: JSON.stringify({ module_id: moduleId }),
    },
    token
  );

export const updateModulesOrder = async (token: string, orderedIds: string[]) =>
  apiFetch<void>(
    "/modules/order",
    {
      method: "PATCH",
      body: JSON.stringify({ ordered_ids: orderedIds }),
    },
    token
  );
