import { useEffect, useMemo, useState } from "react";

import { getTree, listOrganizations, listPermissions, listRoles, listUsers, myOrganizations, switchOrganization } from "../../api/employees";
import { ModuleRuntimeProps } from "../../types/module";

type Tab = "users" | "org" | "roles";

type TabDefinition = {
  id: Tab;
  title: string;
};

const TAB_DEFINITIONS: TabDefinition[] = [
  { id: "users", title: "Пользователи" },
  { id: "org", title: "Оргструктура" },
  { id: "roles", title: "Роли" },
];

const EmployeesModule = ({ module, permissions }: ModuleRuntimeProps) => {
  const [tab, setTab] = useState<Tab | null>(TAB_DEFINITIONS[0]?.id ?? null);
  const [metaLoading, setMetaLoading] = useState(false);
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

  const selectedTab = useMemo(
    () => TAB_DEFINITIONS.find((item) => item.id === tab) ?? TAB_DEFINITIONS[0] ?? null,
    [tab]
  );

  useEffect(() => {
    if (!tab && selectedTab) {
      setTab(selectedTab.id);
    }
  }, [tab, selectedTab]);

  useEffect(() => {
    const loadMeta = async () => {
      setMetaLoading(true);
      setError(null);
      try {
        const [allOrgs, accessibleOrgs] = await Promise.all([listOrganizations(token), myOrganizations(token)]);
        setOrganizations(Array.isArray(allOrgs) ? allOrgs : []);
        const safeAccessibleOrgs = Array.isArray(accessibleOrgs) ? accessibleOrgs : [];
        setMyOrgs(safeAccessibleOrgs);
        setSelectedOrgId((current) => current ?? safeAccessibleOrgs[0]?.id ?? null);
      } catch (loadError) {
        console.error(loadError);
        setError("Не удалось загрузить организации");
        setOrganizations([]);
        setMyOrgs([]);
        setSelectedOrgId(null);
      } finally {
        setMetaLoading(false);
      }
    };
    void loadMeta();
  }, [token]);

  useEffect(() => {
    if (!selectedOrgId || !selectedTab) {
      return;
    }

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        if (selectedTab.id === "users") {
          const params = new URLSearchParams();
          params.set("organization_id", String(selectedOrgId));
          params.set("show_archived", String(showArchived));
          if (search) {
            params.set("search", search);
          }
          const loadedUsers = await listUsers(token, params);
          setUsers(Array.isArray(loadedUsers) ? loadedUsers : []);
        }
        if (selectedTab.id === "org") {
          const loadedTree = await getTree(token, selectedOrgId, showArchived);
          setTree({
            groups: Array.isArray(loadedTree?.groups) ? loadedTree.groups : [],
            positions: Array.isArray(loadedTree?.positions) ? loadedTree.positions : [],
          });
        }
        if (selectedTab.id === "roles") {
          const [loadedRoles, loadedPermissions] = await Promise.all([
            listRoles(token, showArchived),
            listPermissions(token),
          ]);
          setRoles(Array.isArray(loadedRoles) ? loadedRoles : []);
          setPermissionCatalog(Array.isArray(loadedPermissions) ? loadedPermissions : []);
        }
      } catch (loadError) {
        console.error(loadError);
        setError("Не удалось загрузить данные вкладки");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [selectedOrgId, showArchived, search, selectedTab, token]);

  const handleSwitchOrganization = async (organizationId: number) => {
    try {
      await switchOrganization(token, organizationId);
      setSelectedOrgId(organizationId);
    } catch (switchError) {
      console.error(switchError);
      setError("Не удалось переключить организацию");
    }
  };

  const moduleTitle = module?.title ?? "Сотрудники";

  return (
    <section style={{ display: "grid", gap: 12 }}>
      <h1>{moduleTitle}</h1>

      {selectedTab ? <h2 style={{ margin: 0 }}>{selectedTab.title}</h2> : null}

      {metaLoading ? <div>Загрузка данных модуля...</div> : null}

      {!metaLoading && myOrgs.length === 0 ? (
        <div>Нет доступных организаций для отображения.</div>
      ) : (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label>
            Организация:
            <select
              value={selectedOrgId ?? ""}
              onChange={(event) => handleSwitchOrganization(Number(event.target.value))}
              disabled={!selectedOrgId}
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
      )}

      <div style={{ display: "flex", gap: 8 }}>
        {TAB_DEFINITIONS.map((tabItem) => (
          <button key={tabItem.id} type="button" onClick={() => setTab(tabItem.id)}>
            {tabItem.title}
          </button>
        ))}
      </div>

      {error ? <div>{error}</div> : null}
      {loading ? <div>Загрузка...</div> : null}

      {!loading && selectedTab?.id === "users" ? (
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
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5}>Пользователи не найдены.</td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.full_name}</td>
                    <td>{user.login}</td>
                    <td>{user.phone ?? "—"}</td>
                    <td>{(user.positions ?? []).join(", ") || "—"}</td>
                    <td>{user.is_archived ? "Архив" : user.is_active ? "Активен" : "Отключён"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : null}

      {!loading && selectedTab?.id === "org" ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <h3>Группы</h3>
            {tree.groups.length === 0 ? (
              <div>Нет групп для отображения.</div>
            ) : (
              <ul>
                {tree.groups.map((group: any) => (
                  <li key={group.id}>
                    {group.name} {group.is_archived ? "(архив)" : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <h3>Должности и сотрудники</h3>
            {tree.positions.length === 0 ? (
              <div>Нет должностей для отображения.</div>
            ) : (
              <ul>
                {tree.positions.map((position: any) => (
                  <li key={position.id}>
                    <strong>{position.name}</strong>
                    <ul>
                      {(position.users ?? []).map((user: any) => (
                        <li key={user.id} style={{ color: user.is_archived ? "#999" : "inherit" }}>
                          {user.full_name}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}

      {!loading && selectedTab?.id === "roles" ? (
        <div style={{ display: "grid", gap: 8 }}>
          <h3>Роли</h3>
          {roles.length === 0 ? (
            <div>Роли не найдены.</div>
          ) : (
            <ul>
              {roles.map((role) => (
                <li key={role.id}>
                  {role.name} ({role.code}) {role.is_archived ? "(архив)" : ""}
                </li>
              ))}
            </ul>
          )}
          <h3>Права</h3>
          {permissionCatalog.length === 0 ? (
            <div>Права не найдены.</div>
          ) : (
            <ul>
              {permissionCatalog.map((permission) => (
                <li key={permission.id}>{permission.name} — {permission.code}</li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <small>Права модуля из backend: {Object.keys(permissions || {}).length}</small>
      <small>Всего организаций в системе: {organizations.length}</small>
    </section>
  );
};

export default EmployeesModule;
