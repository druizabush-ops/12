import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  CounterpartyDto,
  CounterpartyFolderDto,
  RuleDto,
  archiveCounterparty,
  createAutoTaskRule,
  createCounterparty,
  getAutoTaskRules,
  getCounterparties,
  getCounterpartyFolders,
  restoreCounterparty,
  updateAutoTaskRule,
  updateCounterparty,
} from "../../api/counterparties";
import { getUsers } from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const emptyCounterparty: Partial<CounterpartyDto> = {
  folder_id: 0,
  group_id: null,
  is_archived: false,
  status: "active",
  sort_order: 0,
  name: "",
};

const CounterpartiesModule = (_: ModuleRuntimeProps) => {
  const { token } = useAuth();
  const [folders, setFolders] = useState<CounterpartyFolderDto[]>([]);
  const [counterparties, setCounterparties] = useState<CounterpartyDto[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showArchive, setShowArchive] = useState(false);
  const [form, setForm] = useState<Partial<CounterpartyDto>>(emptyCounterparty);
  const [users, setUsers] = useState<{ id: number; username: string }[]>([]);
  const [rules, setRules] = useState<RuleDto[]>([]);
  const [error, setError] = useState("");

  const selected = useMemo(() => counterparties.find((item) => item.id === selectedId) ?? null, [counterparties, selectedId]);

  const visibleCounterparties = useMemo(() => {
    return counterparties.filter((item) => (showArchive ? item.is_archived : !item.is_archived));
  }, [counterparties, showArchive]);

  const loadAll = async () => {
    if (!token) return;
    const [nextFolders, nextCounterparties, nextUsers] = await Promise.all([
      getCounterpartyFolders(token),
      getCounterparties(token, true),
      getUsers(token),
    ]);
    setFolders(nextFolders);
    setCounterparties(nextCounterparties);
    setUsers(nextUsers);
  };

  useEffect(() => {
    void loadAll();
  }, [token]);

  useEffect(() => {
    if (!token || !selectedId) {
      setRules([]);
      return;
    }
    getAutoTaskRules(token, selectedId).then(setRules).catch(() => setRules([]));
  }, [token, selectedId]);

  useEffect(() => {
    if (!selected) {
      setForm(emptyCounterparty);
      return;
    }
    setForm(selected);
  }, [selected]);

  const onSaveCounterparty = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) return;
    setError("");
    try {
      if (selectedId) {
        await updateCounterparty(token, selectedId, form);
      } else {
        const created = await createCounterparty(token, form);
        setSelectedId(created.id);
      }
      await loadAll();
    } catch (e) {
      setError(String(e));
    }
  };

  const onArchiveToggle = async () => {
    if (!token || !selectedId) return;
    if (selected?.is_archived) {
      await restoreCounterparty(token, selectedId);
    } else {
      await archiveCounterparty(token, selectedId);
    }
    await loadAll();
  };

  const onCreateRule = async () => {
    if (!token || !selectedId) return;
    const defaultUser = users[0]?.id;
    if (!defaultUser) return;
    await createAutoTaskRule(token, selectedId, {
      is_enabled: true,
      title: "Запрос заказа",
      kind: "order_request",
      schedule: {
        recurrence_type: "weekly",
        recurrence_interval: 1,
        recurrence_days_of_week: [selected?.order_day_of_week ?? 1],
        recurrence_end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().slice(0, 10),
      },
      primary_task: {
        assignee_user_id: defaultUser,
        text: `Запросить заказ у ${selected?.name ?? "контрагента"}`,
        due_time: selected?.order_deadline_time,
      },
      review_task: { enabled: false, assignee_user_id: null, text: null, due_time: selected?.order_deadline_time ?? null },
    });
    setRules(await getAutoTaskRules(token, selectedId));
  };

  const onRecreateRule = async (rule: RuleDto) => {
    if (!token || !selectedId) return;
    const replace = window.confirm("Удалить существующие серии и пересоздать? OK=удалить+пересоздать, Отмена=оставить и создать новую");
    await updateAutoTaskRule(token, selectedId, rule.id, {
      ...rule,
      update_mode: replace ? "replace_existing" : "keep_existing",
    });
    setRules(await getAutoTaskRules(token, selectedId));
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 16 }}>
      <section className="admin-card" style={{ maxHeight: "80vh", overflow: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>Папки и контрагенты</h3>
          <button type="button" className="ghost-button" onClick={() => setShowArchive((v) => !v)}>{showArchive ? "Активные" : "Архив"}</button>
        </div>
        {folders.map((folder) => (
          <div key={folder.id} style={{ marginBottom: 12 }}>
            <strong>{folder.name}</strong>
            <div style={{ display: "grid", gap: 4, marginTop: 6 }}>
              {visibleCounterparties.filter((c) => c.folder_id === folder.id).map((item) => (
                <button key={item.id} type="button" className="ghost-button" onClick={() => setSelectedId(item.id)}>
                  {item.name} {item.status === "inactive" ? "(не работает)" : ""}
                </button>
              ))}
            </div>
          </div>
        ))}
        <button type="button" className="ghost-button" onClick={() => setSelectedId(null)}>+ Новый контрагент</button>
      </section>

      <section className="admin-card">
        <h3>Карточка контрагента</h3>
        <form onSubmit={onSaveCounterparty} style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(180px, 1fr))", gap: 8 }}>
          <select value={form.folder_id ?? 0} onChange={(e) => setForm((prev) => ({ ...prev, folder_id: Number(e.target.value) }))}>
            <option value={0}>Выберите папку</option>
            {folders.map((folder) => <option key={folder.id} value={folder.id}>{folder.name}</option>)}
          </select>
          <input placeholder="Внутреннее имя" value={form.name ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} />
          <input placeholder="Юр. название" value={form.legal_name ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, legal_name: e.target.value }))} />
          <input placeholder="Город" value={form.city ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value }))} />
          <input placeholder="Телефон" value={form.phone ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))} />
          <input placeholder="Email" value={form.email ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))} />
          <input placeholder="ИНН" value={form.inn ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, inn: e.target.value }))} />
          <input placeholder="КПП" value={form.kpp ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, kpp: e.target.value }))} />
          <button type="submit" className="primary-button">Сохранить</button>
          {selected ? <button type="button" className="ghost-button" onClick={() => void onArchiveToggle()}>{selected.is_archived ? "Восстановить" : "В архив"}</button> : null}
        </form>
        {error ? <p style={{ color: "#f87171" }}>{error}</p> : null}

        <hr style={{ margin: "16px 0" }} />
        <h4>Автозадачи</h4>
        <p>Автозадачи создаются через recurring-механизм Tasks (master + children) без cron.</p>
        <button type="button" className="ghost-button" disabled={!selectedId} onClick={() => void onCreateRule()}>+ Добавить правило</button>
        <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
          {rules.map((rule) => (
            <div key={rule.id} style={{ border: "1px solid #334155", borderRadius: 8, padding: 8 }}>
              <strong>{rule.title}</strong>
              <div>Будет создаваться: {rule.primary_task.text}, повтор: {rule.schedule.recurrence_type} / {rule.schedule.recurrence_interval}</div>
              <div>Источник: counterparty #{rule.counterparty_id}, rule #{rule.id}</div>
              <button type="button" className="ghost-button" onClick={() => void onRecreateRule(rule)}>Изменить расписание</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default CounterpartiesModule;
