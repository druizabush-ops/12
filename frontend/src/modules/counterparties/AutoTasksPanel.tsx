import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  CounterpartyDto,
  createAutoTaskRule,
  deleteAutoTaskRule,
  getAutoTaskRules,
  getCounterpartySettings,
  RuleDto,
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
  active: { label: "Активна", className: "task-badge task-badge-success" },
  paused: { label: "На паузе", className: "task-badge" },
  stopped: { label: "Остановлена", className: "task-badge task-badge-danger" },
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
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
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

  const resetForm = () => {
    if (!counterparty) return;
    setEditingRuleId(null);
    setKind("MAKE_ORDER");
    setTitleTemplate(defaultTitle("MAKE_ORDER", counterparty.name));
    setAssignees([]);
    setWeekday(counterparty.order_day_of_week ?? 2);
    setDueTime(counterparty.order_deadline_time?.slice(0, 5) ?? "16:00");
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
  }, [kind, counterparty?.id]);

  if (!counterparty) return <section className="admin-card">Выберите контрагента для автозадач.</section>;

  const openCreateModal = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const openEditModal = (rule: RuleDto) => {
    setEditingRuleId(rule.id);
    setKind(rule.task_kind);
    setTitleTemplate(rule.title_template);
    setAssignees(rule.assignee_user_ids);
    setWeekday(rule.schedule_weekday);
    setDueTime(rule.schedule_due_time?.slice(0, 5) ?? "");
    setIsCreateModalOpen(true);
  };

  const submitRule = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) return;

    if (editingRuleId) {
      await runAction(
        () =>
          updateAutoTaskRule(token, counterparty.id, editingRuleId, {
            task_kind: kind,
            title_template: titleTemplate,
            assignee_user_ids: assignees,
            schedule_weekday: weekday,
            schedule_due_time: dueTime || null,
          }),
        "Правило обновлено",
        editingRuleId,
      );
    } else {
      await runAction(
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
      );
    }

    setIsCreateModalOpen(false);
    resetForm();
  };

  return (
    <section style={{ display: "grid", gap: 10 }}>
      {toast ? <div className={toast.kind === "success" ? "task-badge task-badge-success" : "task-badge task-badge-danger"}>{toast.text}</div> : null}
      {isBusy ? <div className="task-badge">Загрузка...</div> : null}

      <section className="admin-card" style={{ display: "grid", gap: 8 }}>
        <strong>Создатель</strong>
        <select value={creatorUserId ?? ""} onChange={(e) => setCreatorUserId(e.target.value ? Number(e.target.value) : null)} disabled={isBusy}>
          <option value="">Не выбран</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>{user.username}</option>
          ))}
        </select>
        <button type="button" className="ghost-button" disabled={isBusy} onClick={() => token && runAction(() => updateCounterpartySettings(token, { task_creator_user_id: creatorUserId }), "Настройки сохранены")}>Сохранить</button>
      </section>

      <button type="button" className="secondary-button" disabled={isBusy} onClick={openCreateModal}>Создать автозадачу</button>

      {rules.map((rule) => (
        <article key={rule.id} className="task-item" style={{ margin: 0 }}>
          <div className="task-item-main">
            <strong>{rule.title_template}</strong>
            <div>Расписание: каждый {weekdayMap[rule.schedule_weekday]}, до {rule.schedule_due_time?.slice(0, 5) ?? "—"}</div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
              <span className={statusMeta[rule.state].className}>{statusMeta[rule.state].label}</span>
              {rule.assignee_user_ids.map((id) => <span key={id} className="task-badge">{usersMap.get(id) ?? id}</span>)}
            </div>
          </div>
          <div className="task-actions-inline">
            <button type="button" title="Редактировать" disabled={isBusy && activeRuleActionId === rule.id} onClick={() => openEditModal(rule)}>✏️</button>
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

      {isCreateModalOpen ? (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={(event) => void submitRule(event)}>
            <h3 style={{ marginTop: 0 }}>{editingRuleId ? "Редактировать автозадачу" : "Создать автозадачу"}</h3>
            <label>
              Тип правила
              <select value={kind} onChange={(e) => setKind(e.target.value as "MAKE_ORDER" | "SEND_ORDER")} disabled={isBusy}>
                <option value="MAKE_ORDER">Сделать заявку</option>
                <option value="SEND_ORDER">Отправить заявку</option>
              </select>
            </label>
            <label>
              Название
              <input value={titleTemplate} onChange={(e) => setTitleTemplate(e.target.value)} placeholder="Название задачи" disabled={isBusy} />
            </label>
            <label>
              Исполнители
              <select multiple value={assignees.map(String)} onChange={(e) => setAssignees(Array.from(e.target.selectedOptions).map((item) => Number(item.value)))} disabled={isBusy}>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>{user.username}</option>
                ))}
              </select>
            </label>
            <label>
              День
              <select value={weekday} onChange={(e) => setWeekday(Number(e.target.value))} disabled={isBusy}>
                {Object.entries(weekdayMap).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label>
              Время
              <input type="time" value={dueTime} onChange={(e) => setDueTime(e.target.value)} disabled={isBusy} />
            </label>
            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" disabled={isBusy} onClick={() => setIsCreateModalOpen(false)}>Отмена</button>
              <button type="submit" className="secondary-button" disabled={isBusy}>Создать</button>
            </div>
          </form>
        </div>
      ) : null}
    </section>
  );
};

export default AutoTasksPanel;
