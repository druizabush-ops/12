// API для платформенного реестра модулей BLOCK 13.
// Нормализация ответа выполняется здесь, потому что backend — источник истины.

import { apiFetch } from "./client";
import { PlatformModule } from "../types/module";

type ModuleDto = {
  id: string;
  name: string;
  title: string;
  path: string;
  order: number;
  is_primary: boolean;
  has_access: boolean;
  permissions?: Record<string, boolean>;
};

const normalizeModule = (module: ModuleDto): PlatformModule => ({
  id: module.id,
  name: module.name,
  title: module.title,
  path: module.path,
  order: module.order,
  is_primary: module.is_primary,
  has_access: module.has_access,
  permissions: module.permissions ?? {},
});

export const fetchModules = async (token: string): Promise<PlatformModule[]> => {
  const data = await apiFetch<ModuleDto[]>("/modules", { method: "GET" }, token);
  return data.map(normalizeModule);
};

export const updatePrimaryModule = async (
  token: string,
  moduleId: string | null
): Promise<PlatformModule[]> => {
  const data = await apiFetch<ModuleDto[]>(
    "/modules/primary",
    {
      method: "PATCH",
      body: JSON.stringify({ module_id: moduleId }),
    },
    token
  );
  return data.map(normalizeModule);
};

export const updateModulesOrder = async (
  token: string,
  orderedIds: string[]
): Promise<PlatformModule[]> => {
  const data = await apiFetch<ModuleDto[]>(
    "/modules/order",
    {
      method: "PATCH",
      body: JSON.stringify({ ordered_ids: orderedIds }),
    },
    token
  );
  return data.map(normalizeModule);
};
