import { apiFetch } from "./client";

export type RoleDto = {
  id: number;
  name: string;
  can_manage_access: boolean;
  module_ids: string[];
};

export type AdminModuleItem = {
  id: string;
  title: string;
};

export type PermissionItem = {
  name: string;
  is_allowed: boolean;
};

export type PermissionsDto = {
  role_id: number;
  module_id: string;
  permissions: PermissionItem[];
};

export type UserRolesDto = {
  id: number;
  username: string;
  role_ids: number[];
};

export type AffectedUser = {
  id: number;
  username: string;
};

export type ChangeImpactDto = {
  message: string;
  affected_users: AffectedUser[];
};

export const fetchRoles = (token: string) =>
  apiFetch<RoleDto[]>("/admin/access/roles", { method: "GET" }, token);

export const createRole = (token: string, name: string) =>
  apiFetch<RoleDto>(
    "/admin/access/roles",
    { method: "POST", body: JSON.stringify({ name }) },
    token
  );

export const deleteRole = (token: string, roleId: number) =>
  apiFetch<unknown>(`/admin/access/roles/${roleId}`, { method: "DELETE" }, token);

export const fetchAdminModules = (token: string) =>
  apiFetch<AdminModuleItem[]>("/admin/access/modules", { method: "GET" }, token);

export const setRoleModuleAccess = (
  token: string,
  roleId: number,
  moduleId: string,
  hasAccess: boolean
) =>
  apiFetch<ChangeImpactDto>(
    `/admin/access/roles/${roleId}/modules/${moduleId}`,
    { method: "PATCH", body: JSON.stringify({ has_access: hasAccess }) },
    token
  );

export const fetchRoleModulePermissions = (token: string, roleId: number, moduleId: string) =>
  apiFetch<PermissionsDto>(
    `/admin/access/roles/${roleId}/modules/${moduleId}/permissions`,
    { method: "GET" },
    token
  );

export const updateRoleModulePermissions = (
  token: string,
  roleId: number,
  moduleId: string,
  permissions: PermissionItem[]
) =>
  apiFetch<ChangeImpactDto>(
    `/admin/access/roles/${roleId}/modules/${moduleId}/permissions`,
    { method: "PUT", body: JSON.stringify({ permissions }) },
    token
  );

export const fetchUsersWithRoles = (token: string) =>
  apiFetch<UserRolesDto[]>("/admin/access/users", { method: "GET" }, token);

export const updateUserRoles = (token: string, userId: number, roleIds: number[]) =>
  apiFetch<ChangeImpactDto>(
    `/admin/access/users/${userId}/roles`,
    { method: "PUT", body: JSON.stringify({ role_ids: roleIds }) },
    token
  );

export const triggerSessionAction = (token: string, userIds: number[], mode: "now" | "5m") =>
  apiFetch<{ status: string; message: string }>(
    "/admin/access/session-actions",
    { method: "POST", body: JSON.stringify({ user_ids: userIds, mode }) },
    token
  );
