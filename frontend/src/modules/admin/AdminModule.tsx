import { useEffect, useMemo, useState } from "react";

import {
  ChangeImpactDto,
  PermissionItem,
  RoleDto,
  UserRolesDto,
  createRole,
  deleteRole,
  fetchAdminModules,
  fetchRoleModulePermissions,
  fetchRoles,
  fetchUsersWithRoles,
  setRoleModuleAccess,
  triggerSessionAction,
  updateRoleModulePermissions,
  updateUserRoles,
} from "../../api/adminAccess";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

type Tab = "roles" | "users";

type AdminModuleItem = {
  id: string;
  title: string;
};

const IMPACT_MESSAGE = "Изменения затрагивают активных пользователей";

const AdminModule = (_: ModuleRuntimeProps) => {
  const { token } = useAuth();

  const [tab, setTab] = useState<Tab>("roles");
  const [roles, setRoles] = useState<RoleDto[]>([]);
  const [modules, setModules] = useState<AdminModuleItem[]>([]);
  const [users, setUsers] = useState<UserRolesDto[]>([]);

  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<PermissionItem[]>([]);

  const [newRoleName, setNewRoleName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [impact, setImpact] = useState<ChangeImpactDto | null>(null);
  const [impactResult, setImpactResult] = useState<string | null>(null);

  const selectedRole = useMemo(
    () => roles.find((role) => role.id === selectedRoleId) ?? null,
    [roles, selectedRoleId]
  );

  useEffect(() => {
    if (!token) {
      return;
    }

    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [rolesData, modulesData, usersData] = await Promise.all([
          fetchRoles(token),
          fetchAdminModules(token),
          fetchUsersWithRoles(token),
        ]);
        setRoles(rolesData);
        setModules(modulesData);
        setUsers(usersData);
        setSelectedRoleId((current) => current ?? rolesData[0]?.id ?? null);
      } catch (e) {
        setError("Не удалось загрузить данные администрирования");
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [token]);

  useEffect(() => {
    if (!token || selectedRoleId == null || !selectedModuleId) {
      setPermissions([]);
      return;
    }

    const loadPermissions = async () => {
      try {
        const data = await fetchRoleModulePermissions(token, selectedRoleId, selectedModuleId);
        setPermissions(data.permissions);
      } catch {
        setPermissions([]);
      }
    };

    void loadPermissions();
  }, [token, selectedRoleId, selectedModuleId]);

  const refreshRoles = async () => {
    if (!token) {
      return;
    }
    const data = await fetchRoles(token);
    setRoles(data);
    if (selectedRoleId && !data.some((item) => item.id === selectedRoleId)) {
      setSelectedRoleId(data[0]?.id ?? null);
      setSelectedModuleId(null);
    }
  };

  const showImpact = (value: ChangeImpactDto) => {
    setImpact({ ...value, message: IMPACT_MESSAGE });
    setImpactResult(null);
  };

  const onCreateRole = async () => {
    if (!token || !newRoleName.trim()) {
      return;
    }
    await createRole(token, newRoleName.trim());
    setNewRoleName("");
    await refreshRoles();
  };

  const onDeleteRole = async (roleId: number) => {
    if (!token) {
      return;
    }
    await deleteRole(token, roleId);
    await refreshRoles();
  };

  const onToggleModuleAccess = async (moduleId: string, hasAccess: boolean) => {
    if (!token || selectedRoleId == null) {
      return;
    }
    const response = await setRoleModuleAccess(token, selectedRoleId, moduleId, hasAccess);
    await refreshRoles();
    showImpact(response);
  };

  const onPermissionChange = (name: string, isAllowed: boolean) => {
    setPermissions((current) =>
      current.map((item) => (item.name === name ? { ...item, is_allowed: isAllowed } : item))
    );
  };

  const onSavePermissions = async () => {
    if (!token || selectedRoleId == null || !selectedModuleId) {
      return;
    }
    const response = await updateRoleModulePermissions(token, selectedRoleId, selectedModuleId, permissions);
    showImpact(response);
  };

  const onToggleUserRole = async (userId: number, roleId: number, enabled: boolean) => {
    if (!token) {
      return;
    }

    const user = users.find((item) => item.id === userId);
    if (!user) {
      return;
    }

    const nextRoles = enabled
      ? Array.from(new Set([...user.role_ids, roleId]))
      : user.role_ids.filter((id) => id !== roleId);

    const response = await updateUserRoles(token, userId, nextRoles);
    setUsers((current) => current.map((item) => (item.id === userId ? { ...item, role_ids: nextRoles } : item)));
    showImpact(response);
  };

  const onSessionAction = async (mode: "now" | "5m") => {
    if (!token || !impact) {
      return;
    }
    const userIds = impact.affected_users.map((item) => item.id);
    const result = await triggerSessionAction(token, userIds, mode);
    setImpactResult(result.message);
    setImpact(null);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Администрирование</h2>
        <p>Управление ролями, доступом к модулям и permissions.</p>
      </div>

      <div className="admin-tabs">
        <button
          type="button"
          className={tab === "roles" ? "primary-button" : "secondary-button"}
          onClick={() => setTab("roles")}
        >
          Roles → Modules → Permissions
        </button>
        <button
          type="button"
          className={tab === "users" ? "primary-button" : "secondary-button"}
          onClick={() => setTab("users")}
        >
          Users → Roles
        </button>
      </div>

      {isLoading ? <div className="page-card">Загрузка…</div> : null}
      {error ? <div className="page-card form-error">{error}</div> : null}

      {!isLoading && !error && tab === "roles" ? (
        <div className="admin-grid">
          <section className="page-card admin-column">
            <h3>Роли</h3>
            <div className="admin-create-role">
              <input
                value={newRoleName}
                onChange={(event) => setNewRoleName(event.target.value)}
                placeholder="Новая роль"
              />
              <button type="button" className="secondary-button" onClick={onCreateRole}>
                Создать
              </button>
            </div>
            <ul className="admin-list">
              {roles.map((role) => (
                <li key={role.id}>
                  <button
                    type="button"
                    className={selectedRoleId === role.id ? "admin-item active" : "admin-item"}
                    onClick={() => {
                      setSelectedRoleId(role.id);
                      setSelectedModuleId(null);
                    }}
                  >
                    {role.name}
                  </button>
                  <button type="button" className="ghost-button" onClick={() => onDeleteRole(role.id)}>
                    Удалить
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="page-card admin-column">
            <h3>Модули</h3>
            <ul className="admin-list">
              {modules.map((moduleItem) => {
                const hasAccess = Boolean(selectedRole?.module_ids.includes(moduleItem.id));
                return (
                  <li key={moduleItem.id}>
                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        checked={hasAccess}
                        onChange={(event) => onToggleModuleAccess(moduleItem.id, event.target.checked)}
                        disabled={!selectedRole}
                      />
                    </label>
                    <button
                      type="button"
                      className={selectedModuleId === moduleItem.id ? "admin-item active" : "admin-item"}
                      onClick={() => setSelectedModuleId(moduleItem.id)}
                      disabled={!selectedRole}
                    >
                      {moduleItem.title}
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="page-card admin-column">
            <h3>Permissions</h3>
            {selectedRole && selectedModuleId ? (
              <>
                <ul className="admin-list permissions-list">
                  {permissions.map((permission) => (
                    <li key={permission.name}>
                      <label className="admin-checkbox-row">
                        <input
                          type="checkbox"
                          checked={permission.is_allowed}
                          onChange={(event) => onPermissionChange(permission.name, event.target.checked)}
                        />
                        <span>{permission.name}</span>
                      </label>
                    </li>
                  ))}
                </ul>
                <button type="button" className="primary-button" onClick={onSavePermissions}>
                  Сохранить permissions
                </button>
              </>
            ) : (
              <p className="muted">Выберите роль и модуль.</p>
            )}
          </section>
        </div>
      ) : null}

      {!isLoading && !error && tab === "users" ? (
        <section className="page-card admin-column">
          <h3>Users → Roles</h3>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Пользователь</th>
                {roles.map((role) => (
                  <th key={role.id}>{role.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  {roles.map((role) => {
                    const checked = user.role_ids.includes(role.id);
                    return (
                      <td key={role.id}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) => onToggleUserRole(user.id, role.id, event.target.checked)}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {impact ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <h3>{IMPACT_MESSAGE}</h3>
            <p>
              Затронуто пользователей: <strong>{impact.affected_users.length}</strong>
            </p>
            <ul>
              {impact.affected_users.map((user) => (
                <li key={user.id}>{user.username}</li>
              ))}
            </ul>
            <div className="admin-modal-actions">
              <button type="button" className="secondary-button" onClick={() => setImpact(null)}>
                Ничего не делать
              </button>
              <button type="button" className="secondary-button" onClick={() => void onSessionAction("5m")}>
                Разлогинить через 5 минут
              </button>
              <button type="button" className="primary-button" onClick={() => void onSessionAction("now")}>
                Разлогинить сейчас
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {impactResult ? <div className="page-card">{impactResult}</div> : null}
    </div>
  );
};

export default AdminModule;
