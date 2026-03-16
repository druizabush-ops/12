import { apiFetch } from "./client";

export type EmployeeModulePermissions = Record<string, boolean>;

export const listUsers = (token: string | null, params: URLSearchParams) =>
  apiFetch<any[]>(`/users?${params.toString()}`, {}, token);

export const listOrganizations = (token: string | null) =>
  apiFetch<any[]>("/organizations", {}, token);

export const myOrganizations = (token: string | null) =>
  apiFetch<any[]>("/organizations/my", {}, token);

export const switchOrganization = (token: string | null, organizationId: number) =>
  apiFetch<{ organization_id: number }>(
    "/auth/switch-organization",
    { method: "POST", body: JSON.stringify({ organization_id: organizationId }) },
    token
  );

export const getTree = (token: string | null, organizationId: number, showArchived: boolean) =>
  apiFetch<any>(
    `/org/groups/tree?organization_id=${organizationId}&show_archived=${showArchived ? "true" : "false"}`,
    {},
    token
  );

export const listRoles = (token: string | null, showArchived: boolean) =>
  apiFetch<any[]>(`/roles?show_archived=${showArchived ? "true" : "false"}`, {}, token);

export const listPermissions = (token: string | null) => apiFetch<any[]>("/permissions", {}, token);
