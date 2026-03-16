import { useEffect, useMemo, useState } from "react";

import { getTree, listOrganizations, listPermissions, listRoles, listUsers, myOrganizations, switchOrganization } from "../../api/employees";
import { ModuleRuntimeProps } from "../../types/module";

type Tab = "users" | "org" | "roles";

const EmployeesModule = ({ module, permissions }: ModuleRuntimeProps) => {
  const [tab, setTab] = useState<Tab>("users");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [myOrgs, setMyOrgs] = useState<any[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<number | null>(null);
  const [tree, setTree] = useState<any>({ groups: [], positions: [] });
  const [roles, setRoles] = useState<any[]>([]);
  const [permissionCatalog, setPermissionCatalog] = useState<any[]>([]);

  const token = useMemo(() => localStorage.getItem("token"), []);

  useEffect(() => {
    const loadMeta = async () => {
      try {
        const [allOrgs, accessibleOrgs] = await Promise.all([listOrganizations(token), myOrganizations(token)]);
        setOrganizations(allOrgs);
        setMyOrgs(accessibleOrgs);
        if (accessibleOrgs.length > 0) {
          setSelectedOrgId(accessibleOrgs[0].id);
        }
      } catch (loadError) {
        console.error(loadError);
        setError("Не удалось загрузить организации");
      }
    };
    loadMeta();
  }, [token]);

  useEffect(() => {
    if (!selectedOrgId) {
      return;
    }

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        if (tab === "users") {
          const params = new URLSearchParams();
          params.set("organization_id", String(selectedOrgId));
          params.set("show_archived", String(showArchived));
          if (search) {
            params.set("search", search);
          }
          setUsers(await listUsers(token, params));
        }
        if (tab === "org") {
          setTree(await getTree(token, selectedOrgId, showArchived));
        }
        if (tab === "roles") {
          const [loadedRoles, loadedPermissions] = await Promise.all([
            listRoles(token, showArchived),
            listPermissions(token),
          ]);
          setRoles(loadedRoles);
          setPermissionCatalog(loadedPermissions);
        }
      } catch (loadError) {
        console.error(loadError);
        setError("Не удалось загрузить данные вкладки");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [selectedOrgId, showArchived, search, tab, token]);

  const handleSwitchOrganization = async (organizationId: number) => {
    try {
      await switchOrganization(token, organizationId);
      setSelectedOrgId(organizationId);
    } catch (switchError) {
      console.error(switchError);
      setError("Не удалось переключить организацию");
    }
  };

  return (
    <section style={{ display: "grid", gap: 12 }}>
      <h1>{module.title}</h1>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <label>
          Организация:
          <select
            value={selectedOrgId ?? ""}
            onChange={(event) => handleSwitchOrganization(Number(event.target.value))}
          >
            {myOrgs.map((organization) => (
              <option key={organization.id} value={organization.id}>
                {organization.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Показать архивные
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(event) => setShowArchived(event.target.checked)}
          />
        </label>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button type="button" onClick={() => setTab("users")}>Пользователи</button>
        <button type="button" onClick={() => setTab("org")}>Оргструктура</button>
        <button type="button" onClick={() => setTab("roles")}>Роли</button>
      </div>

      {error ? <div>{error}</div> : null}
      {loading ? <div>Загрузка...</div> : null}

      {tab === "users" ? (
        <div style={{ display: "grid", gap: 8 }}>
          <input value={search} placeholder="Поиск по ФИО" onChange={(event) => setSearch(event.target.value)} />
          <table>
            <thead>
              <tr>
                <th>ФИО</th>
                <th>Логин</th>
                <th>Телефон</th>
                <th>Должности</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.full_name}</td>
                  <td>{user.login}</td>
                  <td>{user.phone ?? "—"}</td>
                  <td>{(user.positions ?? []).join(", ") || "—"}</td>
                  <td>{user.is_archived ? "Архив" : user.is_active ? "Активен" : "Отключён"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "org" ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <h3>Группы</h3>
            <ul>
              {tree.groups.map((group: any) => (
                <li key={group.id}>
                  {group.name} {group.is_archived ? "(архив)" : ""}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Должности и сотрудники</h3>
            <ul>
              {tree.positions.map((position: any) => (
                <li key={position.id}>
                  <strong>{position.name}</strong>
                  <ul>
                    {position.users.map((user: any) => (
                      <li key={user.id} style={{ color: user.is_archived ? "#999" : "inherit" }}>
                        {user.full_name}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}

      {tab === "roles" ? (
        <div style={{ display: "grid", gap: 8 }}>
          <h3>Роли</h3>
          <ul>
            {roles.map((role) => (
              <li key={role.id}>
                {role.name} ({role.code}) {role.is_archived ? "(архив)" : ""}
              </li>
            ))}
          </ul>
          <h3>Права</h3>
          <ul>
            {permissionCatalog.map((permission) => (
              <li key={permission.id}>{permission.name} — {permission.code}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <small>Права модуля из backend: {Object.keys(permissions || {}).length}</small>
      <small>Всего организаций в системе: {organizations.length}</small>
    </section>
  );
};

export default EmployeesModule;
