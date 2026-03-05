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

type Toast = { kind: "success" | "error"; text: string };

const weekdayMap: Record<number, string> = { 1: "ПН", 2: "ВТ", 3: "СР", 4: "ЧТ", 5: "ПТ", 6: "СБ", 7: "ВС" };

const defaultTitle = (kind: "MAKE_ORDER" | "SEND_ORDER", name: string) =>
  kind === "MAKE_ORDER" ? `Сделать заявку поставщику ${name}` : `Отправить заявку поставщику ${name}`;

const statusMeta = {
  active: { label: "🟢 Active", className: "task-badge task-badge-success" },
  paused: { label: "🟡 Paused", className: "task-badge" },
  stopped: { label: "⚫ Stopped", className: "task-badge task-badge-danger" },
} as const;

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
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [activeRuleActionId, setActiveRuleActionId] = useState<number | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

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

  const showToast = (kindValue: Toast["kind"], text: string) => {
    setToast({ kind: kindValue, text });
    window.setTimeout(() => setToast(null), 2500);
  };

  const runAction = async (action: () => Promise<unknown>, successText: string, ruleId?: number) => {
    try {
      setIsBusy(true);
      if (ruleId) setActiveRuleActionId(ruleId);
      await action();
      await load();
      showToast("success", successText);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Операция не выполнена";
      showToast("error", message);
    } finally {
      setIsBusy(false);
      setActiveRuleActionId(null);
    }
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

  const startEdit = (rule: RuleDto) => {
    setEditingRuleId(rule.id);
    setKind(rule.task_kind);
    setTitleTemplate(rule.title_template);
    setAssignees(rule.assignee_user_ids);
    setWeekday(rule.schedule_weekday);
    setDueTime(rule.schedule_due_time?.slice(0, 5) ?? "");
  };

  return (
    <section className="admin-card" style={{ display: "grid", gap: 10, maxHeight: "74vh", overflow: "auto" }}>
      <h3 style={{ margin: 0 }}>Автозадачи</h3>
      {toast ? <div className={toast.kind === "success" ? "task-badge task-badge-success" : "task-badge task-badge-danger"}>{toast.text}</div> : null}
      {isBusy ? <div className="task-badge">Загрузка...</div> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 10, padding: 8, borderRight: "2px solid var(--border)" }}>
          <strong>1. Создатель</strong>
          <select value={creatorUserId ?? ""} onChange={(e) => setCreatorUserId(e.target.value ? Number(e.target.value) : null)} disabled={isBusy}>
            <option value="">Не выбран</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.username}</option>
            ))}
          </select>
          <button type="button" className="ghost-button" disabled={isBusy} onClick={() => token && runAction(() => updateCounterpartySettings(token, { task_creator_user_id: creatorUserId }), "Настройки сохранены")}>Сохранить</button>
        </div>

        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 10, padding: 8, borderRight: "2px solid var(--border)" }}>
          <strong>{editingRuleId ? "2. Редактирование" : "2. Новое правило"}</strong>
          <select value={kind} onChange={(e) => setKind(e.target.value as "MAKE_ORDER" | "SEND_ORDER")} disabled={isBusy}>
            <option value="MAKE_ORDER">Сделать заявку</option>
            <option value="SEND_ORDER">Отправить заявку</option>
          </select>
          <input value={titleTemplate} onChange={(e) => setTitleTemplate(e.target.value)} placeholder="Название задачи" disabled={isBusy} />
          <select multiple value={assignees.map(String)} onChange={(e) => setAssignees(Array.from(e.target.selectedOptions).map((item) => Number(item.value)))} disabled={isBusy}>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.username}</option>
            ))}
          </select>
        </div>

        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 10, padding: 8, borderRight: "2px solid var(--border)" }}>
          <strong>3. Расписание</strong>
          <select value={weekday} onChange={(e) => setWeekday(Number(e.target.value))} disabled={isBusy}>
            {Object.entries(weekdayMap).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <input type="time" value={dueTime} onChange={(e) => setDueTime(e.target.value)} disabled={isBusy} />
          <button type="button" className="ghost-button" disabled={isBusy} onClick={() => setDueTime("")}>Очистить время</button>
        </div>

        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 10, padding: 8 }}>
          <strong>4. Действие</strong>
          {editingRuleId ? (
            <>
              <button
                type="button"
                className="secondary-button"
                disabled={isBusy}
                onClick={() =>
                  token &&
                  runAction(
                    () => updateAutoTaskRule(token, counterparty.id, editingRuleId, { task_kind: kind, title_template: titleTemplate, assignee_user_ids: assignees, schedule_weekday: weekday, schedule_due_time: dueTime || null }),
                    "Правило обновлено",
                    editingRuleId,
                  )
                }
              >
                Сохранить
              </button>
              <button type="button" className="ghost-button" disabled={isBusy} onClick={() => setEditingRuleId(null)}>Отменить</button>
            </>
          ) : (
            <button
              type="button"
              className="secondary-button"
              disabled={isBusy}
              onClick={() =>
                token &&
                runAction(
                  () =>
                    createAutoTaskRule(token, counterparty.id, {
                      task_kind: kind,
                      title_template: titleTemplate,
                      assignee_user_ids: assignees,
                      verifier_user_ids: [],
                      is_enabled: true,
                      schedule_weekday: weekday,
                      schedule_due_time: dueTime || null,
                      horizon_days: 15,
                    }),
                  "Правило создано",
                )
              }
            >
              Создать
            </button>
          )}
        </div>
      </div>

      {rules.map((rule) => (
        <article key={rule.id} className="task-item">
          <div className="task-item-main">
            <strong>{rule.task_kind === "MAKE_ORDER" ? "Сделать заявку" : "Отправить заявку"}</strong>
            <div>Каждый {weekdayMap[rule.schedule_weekday]}, до {rule.schedule_due_time?.slice(0, 5) ?? "—"}</div>
            <div className="task-badges">
              <span className={statusMeta[rule.state].className}>{statusMeta[rule.state].label}</span>
            </div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
              {rule.assignee_user_ids.map((id) => <span key={id} className="task-badge">{usersMap.get(id) ?? id}</span>)}
            </div>
          </div>
          <div className="task-actions-inline">
            <button type="button" title="Редактировать" disabled={isBusy && activeRuleActionId === rule.id} onClick={() => startEdit(rule)}>✏️</button>
            {rule.state === "paused" ? (
              <button type="button" title="Возобновить" disabled={isBusy && activeRuleActionId === rule.id} onClick={() => token && runAction(() => resumeAutoTaskRule(token, counterparty.id, rule.id), "Правило возобновлено", rule.id)}>▶️</button>
            ) : (
              <button type="button" title="Пауза" disabled={isBusy && activeRuleActionId === rule.id} onClick={() => token && runAction(() => pauseAutoTaskRule(token, counterparty.id, rule.id), "Правило поставлено на паузу", rule.id)}>⏸️</button>
            )}
            <button type="button" title="Остановить" disabled={isBusy && activeRuleActionId === rule.id} onClick={() => token && runAction(() => stopAutoTaskRule(token, counterparty.id, rule.id), "Правило остановлено", rule.id)}>⏹️</button>
            <button
              type="button"
              title="Удалить"
              disabled={isBusy && activeRuleActionId === rule.id}
              onClick={() =>
                token &&
                window.confirm("Удалить правило автозадачи?") &&
                runAction(() => deleteAutoTaskRule(token, counterparty.id, rule.id), "Правило удалено", rule.id)
              }
            >
              🗑️
            </button>
          </div>
        </article>
      ))}
    </section>
  );
};

export default AutoTasksPanel;
