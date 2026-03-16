import { useEffect, useMemo, useState } from "react";

import { fetchOrganizations, fetchOrgTree, fetchPermissions, fetchRoles, fetchUsers, Organization, switchOrganization } from "../../api/employees";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

type Tab = "users" | "org" | "roles";

const EmployeesModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [tab, setTab] = useState<Tab>("users");
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState<number | null>(user?.last_organization_id ?? null);
  const [users, setUsers] = useState<any[]>([]);
  const [tree, setTree] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    const load = async () => {
      setIsLoading(true);
      try {
        const [orgs, rolesData, permsData] = await Promise.all([
          fetchOrganizations(token),
          fetchRoles(token),
          fetchPermissions(token),
        ]);
        setOrganizations(orgs);
        setRoles(rolesData);
        setPermissions(permsData);
        const nextOrgId = organizationId ?? orgs[0]?.id ?? null;
        setOrganizationId(nextOrgId);
      } finally {
        setIsLoading(false);
      }
    };
    void load();
  }, [token]);

  useEffect(() => {
    if (!token || !organizationId) {
      return;
    }
    const load = async () => {
      const [usersData, treeData] = await Promise.all([
        fetchUsers(token, organizationId),
        fetchOrgTree(token, organizationId),
      ]);
      setUsers(usersData);
      setTree(treeData);
    };
    void load();
  }, [token, organizationId]);

  const permissionGroups = useMemo(() => {
    const grouped = new Map<string, any[]>();
    permissions.forEach((item) => {
      grouped.set(item.module, [...(grouped.get(item.module) ?? []), item]);
    });
    return Array.from(grouped.entries());
  }, [permissions]);

  const onSwitchOrganization = async (nextId: number) => {
    if (!token) {
      return;
    }
    await switchOrganization(token, nextId);
    setOrganizationId(nextId);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Сотрудники</h2>
        <p>Пользователи, оргструктура и роли в контексте выбранной организации.</p>
      </div>

      <div className="admin-section" style={{ marginBottom: 16 }}>
        <label>
          Организация:&nbsp;
          <select value={organizationId ?? ""} onChange={(e) => void onSwitchOrganization(Number(e.target.value))}>
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="admin-tabs">
        <button type="button" className={tab === "users" ? "primary-button" : "secondary-button"} onClick={() => setTab("users")}>Пользователи</button>
        <button type="button" className={tab === "org" ? "primary-button" : "secondary-button"} onClick={() => setTab("org")}>Оргструктура</button>
        <button type="button" className={tab === "roles" ? "primary-button" : "secondary-button"} onClick={() => setTab("roles")}>Роли</button>
      </div>

      {isLoading ? <div className="empty-state">Загрузка...</div> : null}

      {tab === "users" ? (
        <div className="admin-section">
          <h3>Пользователи</h3>
          <table className="admin-table">
            <thead><tr><th>ФИО</th><th>Логин</th><th>Телефон</th><th>Статус</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}><td>{u.full_name}</td><td>{u.login}</td><td>{u.phone ?? "—"}</td><td>{u.is_archived ? "Архив" : "Активен"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "org" ? (
        <div className="admin-section">
          <h3>Оргструктура</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(tree, null, 2)}</pre>
        </div>
      ) : null}

      {tab === "roles" ? (
        <div className="admin-section">
          <h3>Роли</h3>
          <ul>{roles.map((role) => <li key={role.id}>{role.name} ({role.code})</li>)}</ul>
          <h4>Permissions</h4>
          {permissionGroups.map(([module, list]) => (
            <div key={module}><strong>{module}</strong>: {list.map((item) => item.code).join(", ")}</div>
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default EmployeesModule;
