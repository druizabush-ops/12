import { apiFetch } from "./client";

type SidebarSettingsDto = {
  modules_order: string[] | null;
};

export const fetchSidebarSettings = async (token: string): Promise<string[] | null> => {
  const data = await apiFetch<SidebarSettingsDto>("/user/sidebar-settings", { method: "GET" }, token);
  return data.modules_order;
};

export const saveSidebarModulesOrder = async (
  token: string,
  modulesOrder: string[]
): Promise<string[] | null> => {
  const data = await apiFetch<SidebarSettingsDto>(
    "/user/sidebar-settings/modules-order",
    {
      method: "PUT",
      body: JSON.stringify({ modules_order: modulesOrder }),
    },
    token
  );
  return data.modules_order;
};
