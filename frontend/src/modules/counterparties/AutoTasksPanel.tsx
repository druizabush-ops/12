import { useEffect, useMemo, useState } from "react";

import {
  CounterpartyDto,
  createAutoTaskRule,
  getAutoTaskRules,
  getCounterpartySettings,
  pauseAutoTaskRule,
  resumeAutoTaskRule,
  RuleDto,
  stopAutoTaskRule,
  updateAutoTaskRule,
  updateCounterpartySettings,
} from "../../api/counterparties";
import { getUsers, TaskUserDto } from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";

type Props = { counterparty: CounterpartyDto | null };

const weekdayMap: Record<number, string> = { 1: "ПН", 2: "ВТ", 3: "СР", 4: "ЧТ", 5: "ПТ", 6: "СБ", 7: "ВС" };

const defaultTitle = (kind: "MAKE_ORDER" | "SEND_ORDER", name: string) =>
  kind === "MAKE_ORDER" ? `Сделать заявку поставщику ${name}` : `Отправить заявку поставщику ${name}`;

const AutoTasksPanel = ({ counterparty }: Props) => {
  const { token } = useAuth();
  const [rules, setRules] = useState<RuleDto[]>([]);
  const [users, setUsers] = useState<TaskUserDto[]>([]);
  const [creatorUserId, setCreatorUserId] = useState<number | null>(null);
  const [kind, setKind] = useState<"MAKE_ORDER" | "SEND_ORDER">("MAKE_ORDER");
  const [titleTemplate, setTitleTemplate] = useState("");
  const [assignees, setAssignees] = useState<number[]>([]);
  const [weekday, setWeekday] = useState<number>(2);
  const [dueTime, setDueTime] = useState<string>("16:00");

  const usersMap = useMemo(() => new Map(users.map((item) => [item.id, item.username])), [users]);

  const load = async () => {
    if (!token || !counterparty) return;
    const [loadedRules, loadedUsers, settings] = await Promise.all([
      getAutoTaskRules(token, counterparty.id),
      getUsers(token),
      getCounterpartySettings(token),
    ]);
    setRules(loadedRules);
    setUsers(loadedUsers);
    setCreatorUserId(settings.task_creator_user_id);
  };

  useEffect(() => {
    void load();
  }, [token, counterparty?.id]);

  useEffect(() => {
    if (!counterparty) return;
    setTitleTemplate(defaultTitle(kind, counterparty.name));
    setWeekday(counterparty.order_day_of_week ?? 2);
    setDueTime(counterparty.order_deadline_time?.slice(0, 5) ?? "16:00");
  }, [kind, counterparty?.id]);

  if (!counterparty) return <section className="admin-card">Выберите контрагента для автозадач.</section>;

  const submit = async () => {
    if (!token) return;
    await createAutoTaskRule(token, counterparty.id, {
      task_kind: kind,
      title_template: titleTemplate,
      assignee_user_ids: assignees,
      verifier_user_ids: [],
      is_enabled: true,
      schedule_weekday: weekday,
      schedule_due_time: dueTime || null,
      horizon_days: 15,
    });
    await load();
  };

  return (
    <section className="admin-card" style={{ display: "grid", gap: 10, maxHeight: "74vh", overflow: "auto" }}>
      <h3 style={{ margin: 0 }}>Автозадачи</h3>

      <div style={{ display: "grid", gap: 6 }}>
        <strong>Создатель автозадач</strong>
        <input value={creatorUserId ?? ""} onChange={(e) => setCreatorUserId(e.target.value ? Number(e.target.value) : null)} />
        <button type="button" className="ghost-button" onClick={() => token && updateCounterpartySettings(token, { task_creator_user_id: creatorUserId })}>
          Сохранить creator_user_id
        </button>
      </div>

      <div style={{ borderTop: "1px solid var(--border-default)", paddingTop: 8, display: "grid", gap: 6 }}>
        <strong>Создать правило</strong>
        <select value={kind} onChange={(e) => setKind(e.target.value as "MAKE_ORDER" | "SEND_ORDER")}> 
          <option value="MAKE_ORDER">Сделать заявку</option>
          <option value="SEND_ORDER">Отправить заявку</option>
        </select>
        <input value={titleTemplate} onChange={(e) => setTitleTemplate(e.target.value)} placeholder="Title template" />
        <select multiple value={assignees.map(String)} onChange={(e) => setAssignees(Array.from(e.target.selectedOptions).map((item) => Number(item.value)))}>
          {users.map((user) => (
            <option key={user.id} value={user.id}>{user.username}</option>
          ))}
        </select>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <select value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
            {Object.entries(weekdayMap).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <input type="time" value={dueTime} onChange={(e) => setDueTime(e.target.value)} />
        </div>
        <button type="button" className="secondary-button" onClick={() => void submit()}>Создать</button>
      </div>

      {rules.map((rule) => (
        <article key={rule.id} style={{ border: "1px solid var(--border-default)", borderRadius: 8, padding: 8, display: "grid", gap: 6 }}>
          <strong>{rule.task_kind === "MAKE_ORDER" ? "Сделать заявку" : "Отправить заявку"}</strong>
          <div>Каждый {weekdayMap[rule.schedule_weekday]}, до {rule.schedule_due_time?.slice(0, 5) ?? "—"}</div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {rule.assignee_user_ids.map((id) => <span key={id} className="badge">{usersMap.get(id) ?? id}</span>)}
          </div>
          <div>Статус: {rule.state}</div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="ghost-button"
              onClick={() => token && updateAutoTaskRule(token, counterparty.id, rule.id, { is_enabled: !rule.is_enabled })}
            >
              Редактировать
            </button>
            {rule.state === "paused" ? (
              <button type="button" className="ghost-button" onClick={() => token && resumeAutoTaskRule(token, counterparty.id, rule.id)}>Возобновить</button>
            ) : (
              <button type="button" className="ghost-button" onClick={() => token && pauseAutoTaskRule(token, counterparty.id, rule.id)}>Пауза</button>
            )}
            <button type="button" className="secondary-button" onClick={() => token && stopAutoTaskRule(token, counterparty.id, rule.id)}>Остановить</button>
            <button
              type="button"
              className="ghost-button"
              onClick={async () => {
                if (!token) return;
                const action = window.confirm("Оставить старые задачи? OK=keep, Cancel=replace") ? "keep" : "replace";
                await updateAutoTaskRule(token, counterparty.id, rule.id, { schedule_weekday: weekday, schedule_due_time: dueTime || null }, action);
                await load();
              }}
            >
              Изменить расписание
            </button>
          </div>
        </article>
      ))}
    </section>
  );
};

export default AutoTasksPanel;
