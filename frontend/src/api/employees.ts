import { apiFetch } from "./client";

export type EmployeeUser = {
  id: number;
  full_name: string;
  login: string;
  phone: string | null;
  is_active: boolean;
  is_archived: boolean;
};

export type Organization = { id: number; name: string; code: string; is_active: boolean; is_archived: boolean };
export type EmployeeRole = { id: number; name: string; code: string; description: string | null; is_system: boolean; is_active: boolean; is_archived: boolean };
export type Permission = { id: number; module: string; action: string; code: string; name: string };

export const fetchUsers = (token: string, organizationId?: number) =>
  apiFetch<EmployeeUser[]>(`/users${organizationId ? `?organization_id=${organizationId}` : ""}`, { method: "GET" }, token);

export const fetchOrganizations = (token: string) => apiFetch<Organization[]>("/organizations/my", { method: "GET" }, token);
export const switchOrganization = (token: string, organization_id: number) =>
  apiFetch<{ status: string; organization_id: number }>("/auth/switch-organization", { method: "POST", body: JSON.stringify({ organization_id }) }, token);

export const fetchOrgTree = (token: string, organizationId: number, includeArchived = false) =>
  apiFetch<any[]>(`/org/groups/tree?organization_id=${organizationId}&include_archived=${includeArchived}`, { method: "GET" }, token);

export const fetchRoles = (token: string) => apiFetch<EmployeeRole[]>("/roles", { method: "GET" }, token);
export const fetchPermissions = (token: string) => apiFetch<Permission[]>("/permissions", { method: "GET" }, token);
