import { useEffect, useMemo, useState } from "react";

import {
  CounterpartyDto,
  createAutoTaskRule,
  deleteAutoTaskRule,
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

type RuleAction = "pause" | "resume" | "stop" | "edit" | "delete";

const weekdayMap: Record<number, string> = { 1: "ПН", 2: "ВТ", 3: "СР", 4: "ЧТ", 5: "ПТ", 6: "СБ", 7: "ВС" };

const defaultTitle = (kind: "MAKE_ORDER" | "SEND_ORDER", name: string) =>
  kind === "MAKE_ORDER" ? `Сделать заявку поставщику ${name}` : `Отправить заявку поставщику ${name}`;

const statusBadge = (state: RuleDto["state"]) => {
  if (state === "paused") return { icon: "🟡", text: "Paused", className: "task-badge" };
  if (state === "stopped") return { icon: "⚫", text: "Stopped", className: "task-badge" };
  return { icon: "🟢", text: "Active", className: "task-badge task-badge-success" };
};

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
  const [loadingRuleId, setLoadingRuleId] = useState<number | null>(null);
  const [loadingAction, setLoadingAction] = useState<RuleAction | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [toast, setToast] = useState<string>("");

  const usersMap = useMemo(() => new Map(users.map((item) => [item.id, item.username])), [users]);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2400);
  };

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
  const hasToken = Boolean(token);

  const submit = async () => {
    if (!token) return;
    setIsCreating(true);
    try {
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
      showToast("Правило создано");
      await load();
    } finally {
      setIsCreating(false);
    }
  };

  const runRuleAction = async (ruleId: number, action: RuleAction, callback: () => Promise<unknown>, successMessage: string) => {
    setLoadingRuleId(ruleId);
    setLoadingAction(action);
    try {
      await callback();
      await load();
      showToast(successMessage);
    } finally {
      setLoadingRuleId(null);
      setLoadingAction(null);
    }
  };

  return (
    <section className="admin-card" style={{ display: "grid", gap: 10, maxHeight: "74vh", overflow: "auto" }}>
      <h3 style={{ margin: 0 }}>Автозадачи</h3>
      {toast ? <div className="counterparty-toast">{toast}</div> : null}

      <div style={{ display: "grid", gap: 6 }}>
        <strong>Создатель автозадач</strong>
        <input value={creatorUserId ?? ""} onChange={(e) => setCreatorUserId(e.target.value ? Number(e.target.value) : null)} />
        <button type="button" className="ghost-button" onClick={() => token && updateCounterpartySettings(token, { task_creator_user_id: creatorUserId })}>
          Сохранить creator_user_id
        </button>
      </div>

      <div style={{ borderTop: "1px solid var(--border)", paddingTop: 8, display: "grid", gap: 6 }}>
        <strong>Создать правило</strong>
        <select value={kind} onChange={(e) => setKind(e.target.value as "MAKE_ORDER" | "SEND_ORDER")}>
          <option value="MAKE_ORDER">Сделать заявку</option>
          <option value="SEND_ORDER">Отправить заявку</option>
        </select>
        <input value={titleTemplate} onChange={(e) => setTitleTemplate(e.target.value)} placeholder="Название правила" />
        <select multiple value={assignees.map(String)} onChange={(e) => setAssignees(Array.from(e.target.selectedOptions).map((item) => Number(item.value)))}>
          {users.map((user) => (
            <option key={user.id} value={user.id}>{user.username}</option>
          ))}
        </select>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <select value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
            {Object.entries(weekdayMap).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <div style={{ display: "flex", gap: 8 }}>
            <input type="time" value={dueTime} onChange={(e) => setDueTime(e.target.value)} style={{ flex: 1 }} />
            <button type="button" className="ghost-button" onClick={() => setDueTime("")}>Очистить</button>
          </div>
        </div>
        <button type="button" className="secondary-button" onClick={() => void submit()} disabled={isCreating}>{isCreating ? "Создание..." : "Создать"}</button>
      </div>

      {rules.map((rule) => {
        const isLoading = loadingRuleId === rule.id;
        const status = statusBadge(rule.state);
        return (
          <article key={rule.id} className="task-item">
            <div className="task-item-main">
              <strong>{rule.task_kind === "MAKE_ORDER" ? "Сделать заявку" : "Отправить заявку"}</strong>
              <div className="muted">Каждый {weekdayMap[rule.schedule_weekday]}, до {rule.schedule_due_time?.slice(0, 5) ?? "—"}</div>
              <div className="task-chips">
                {rule.assignee_user_ids.map((id) => <span key={id} className="task-chip">{usersMap.get(id) ?? id}</span>)}
              </div>
              <div className="task-badges">
                <span className={status.className}>{status.icon} {status.text}</span>
              </div>
            </div>
            <div className="task-actions-inline">
              <button
                type="button"
                title="Редактировать"
                disabled={isLoading || !hasToken}
                onClick={() => {
                  if (!window.confirm("Применить к правилу текущие день и время из формы?")) return;
                  void runRuleAction(
                    rule.id,
                    "edit",
                    () => updateAutoTaskRule(token as string, counterparty.id, rule.id, { schedule_weekday: weekday, schedule_due_time: dueTime || null }, "keep"),
                    "Правило обновлено",
                  );
                }}
              >✏️</button>
              {rule.state === "paused" ? (
                <button
                  type="button"
                  title="Возобновить"
                  disabled={isLoading || !hasToken}
                  onClick={() => void runRuleAction(rule.id, "resume", () => resumeAutoTaskRule(token as string, counterparty.id, rule.id), "Правило возобновлено")}
                >▶️</button>
              ) : (
                <button
                  type="button"
                  title="Пауза"
                  disabled={isLoading || !hasToken || rule.state === "stopped"}
                  onClick={() => void runRuleAction(rule.id, "pause", () => pauseAutoTaskRule(token as string, counterparty.id, rule.id), "Пауза")}
                >⏸️</button>
              )}
              <button
                type="button"
                title="Остановить"
                disabled={isLoading || !hasToken || rule.state === "stopped"}
                onClick={() => void runRuleAction(rule.id, "stop", () => stopAutoTaskRule(token as string, counterparty.id, rule.id), "Остановлено")}
              >⏹️</button>
              <button
                type="button"
                title="Удалить"
                disabled={isLoading || !hasToken}
                onClick={() => {
                  if (!window.confirm("Удалить правило? Уже созданные задачи сохранятся.")) return;
                  void runRuleAction(rule.id, "delete", () => deleteAutoTaskRule(token as string, counterparty.id, rule.id), "Удалено");
                }}
              >🗑️</button>
            </div>
          </article>
        );
      })}
      {loadingRuleId && loadingAction ? <small style={{ color: "var(--text-secondary)" }}>Выполняется: {loadingAction}...</small> : null}
    </section>
  );
};

export default AutoTasksPanel;
