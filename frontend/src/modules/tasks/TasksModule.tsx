import { FormEvent, useEffect, useMemo, useState } from "react";

import { getUsers } from "../../api/auth";
import {
  TaskDto,
  TaskFolderDto,
  completeTask,
  createFolder,
  createTask,
  getAttentionTasks,
  getCalendar,
  getFolders,
  getTasksByDate,
  recurrenceAction,
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const toDateKey = (value: Date) => value.toISOString().slice(0, 10);
const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);
const SYSTEM_ATTENTION_ID = "system-attention";

const normalizeDateInput = (input: string): string | null => {
  const digits = input.replace(/[^\d]/g, " ").trim().split(/\s+/).filter(Boolean);
  if (digits.length !== 3) return null;
  let [d, m, y] = digits.map(Number);
  if (y < 100) y += 2000;
  if (!d || !m || !y) return null;
  const value = new Date(y, m - 1, d);
  if (value.getFullYear() !== y || value.getMonth() !== m - 1 || value.getDate() !== d) return null;
  return toDateKey(value);
};

const formatDisplayDate = (apiDate: string) => {
  const [y, m, d] = apiDate.split("-");
  return `${d}.${m}.${y}`;
};

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [calendarCounts, setCalendarCounts] = useState<Record<string, number>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [attentionTasks, setAttentionTasks] = useState<TaskDto[]>([]);
  const [folders, setFolders] = useState<TaskFolderDto[]>([]);
  const [activeFolderId, setActiveFolderId] = useState<string | null>(null);
  const [users, setUsers] = useState<{ id: number; full_name: string }[]>([]);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskDto | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDateRaw, setDueDateRaw] = useState(formatDisplayDate(selectedDate));
  const [dueTime, setDueTime] = useState("");
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "very_urgent">("normal");
  const [requiresVerification, setRequiresVerification] = useState(false);
  const [verifierIdInput, setVerifierIdInput] = useState<number | "">("");
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrenceType, setRecurrenceType] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
  const [recurrenceInterval, setRecurrenceInterval] = useState(1);
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [newFolderName, setNewFolderName] = useState("");

  const monthDays = useMemo(() => {
    const first = startOfMonth(monthDate);
    const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    return Array.from({ length: daysInMonth }, (_, index) => {
      const day = new Date(first.getFullYear(), first.getMonth(), index + 1);
      return toDateKey(day);
    });
  }, [monthDate]);

  const loadCalendar = async () => {
    if (!token) return;
    const from = toDateKey(startOfMonth(monthDate));
    const to = toDateKey(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0));
    const data = await getCalendar(token, from, to);
    setCalendarCounts(Object.fromEntries(data.map((item) => [item.date, item.count])));
  };

  const loadTasks = async () => {
    if (!token) return;
    const folderId = activeFolderId && activeFolderId !== SYSTEM_ATTENTION_ID ? activeFolderId : undefined;
    const [dayTasks, attention] = await Promise.all([
      getTasksByDate(token, selectedDate, { folderId }),
      getAttentionTasks(token),
    ]);
    setTasks(dayTasks);
    setAttentionTasks(attention);
  };

  const loadFolders = async () => {
    if (!token) return;
    setFolders(await getFolders(token));
  };

  useEffect(() => {
    if (!token) return;
    void Promise.all([loadCalendar(), loadFolders(), loadTasks(), getUsers(token).then(setUsers)]);
  }, [token]);

  useEffect(() => {
    void loadCalendar();
  }, [monthDate]);

  useEffect(() => {
    void loadTasks();
  }, [selectedDate, activeFolderId]);

  const visibleTasks = activeFolderId === SYSTEM_ATTENTION_ID ? attentionTasks : tasks;
  const today = toDateKey(new Date());
  const grouped = {
    actual: visibleTasks.filter((task) => task.due_date === selectedDate && task.status !== "done"),
    overdue: visibleTasks.filter((task) => !!task.due_date && task.due_date < today && task.status !== "done"),
    done: visibleTasks.filter((task) => task.status === "done"),
  };

  const onCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !title.trim()) return;
    const normalizedDueDate = normalizeDateInput(dueDateRaw);
    await createTask(token, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: normalizedDueDate,
      due_time: dueTime || null,
      urgency,
      requires_verification: requiresVerification,
      verifier_user_id: verifierIdInput || null,
      assignee_user_ids: assigneeIds,
      is_recurring: isRecurring,
      recurrence_type: isRecurring ? recurrenceType : null,
      recurrence_interval: isRecurring ? recurrenceInterval : null,
      recurrence_end_date: isRecurring && recurrenceEndDate ? recurrenceEndDate : null,
    });
    setTitle("");
    setDescription("");
    setDueTime("");
    setUrgency("normal");
    setRequiresVerification(false);
    setVerifierIdInput("");
    setAssigneeIds([]);
    setIsRecurring(false);
    setRecurrenceType("daily");
    setRecurrenceInterval(1);
    setRecurrenceEndDate("");
    setIsCreateOpen(false);
    await Promise.all([loadTasks(), loadCalendar()]);
  };

  const renderTask = (task: TaskDto) => {
    const canVerify = task.requires_verification && (task.verifier_user_id ?? task.created_by_user_id) === user?.id;
    const urgencyLabel = task.urgency === "urgent" ? "🔥" : task.urgency === "very_urgent" ? "🔥🔥🔥" : "";
    return (
      <li key={task.id} className={`${task.status === "done" ? "task-item done" : "task-item"}${task.is_overdue ? " overdue" : ""}`}>
        <div>
          <strong>{task.title}</strong> <span>{urgencyLabel}</span>
          <div className="muted">Дедлайн: {task.due_date ? formatDisplayDate(task.due_date) : "без срока"} {task.due_time ?? ""}</div>
          <div className="task-badges">
            <span className="task-badge">{task.status}</span>
            {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
            {task.status === "done" ? <span className="task-badge">Выполнено</span> : null}
          </div>
        </div>
        <div className="task-actions">
          {task.status !== "done" ? <button className="secondary-button" onClick={() => token && completeTask(token, task.id).then(loadTasks)}>Выполнить</button> : null}
          {canVerify && !task.verified_at ? <button className="ghost-button" onClick={() => token && verifyTask(token, task.id).then(loadTasks)}>Проверить</button> : null}
          <button className="ghost-button" onClick={() => { setSelectedTask(task); setIsDetailsOpen(true); }}>Подробнее</button>
        </div>
      </li>
    );
  };

  return (
    <div className="page tasks-page">
      <div className="page-header"><h2>Задачи</h2></div>
      <div className="tasks-layout">
        <section className="page-card tasks-calendar">
          <div className="tasks-calendar-header">
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() - 1, 1))}>←</button>
            <strong>{monthDate.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}</strong>
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 1))}>→</button>
          </div>
          <button className="secondary-button" onClick={() => { const d = new Date(); setMonthDate(startOfMonth(d)); setSelectedDate(toDateKey(d)); }}>Сегодня</button>
          <div className="tasks-calendar-grid">{monthDays.map((dayKey) => {
            const weekday = new Date(dayKey).getDay();
            return (
              <button key={dayKey} type="button" className={`${dayKey === selectedDate ? "tasks-day active" : "tasks-day"}${weekday === 0 || weekday === 6 ? " weekend" : ""}`} onClick={() => setSelectedDate(dayKey)}>
                <span>{new Date(dayKey).getDate()}</span><small>{calendarCounts[dayKey] ?? 0}</small>
              </button>
            );
          })}</div>
        </section>
        <section className="page-card tasks-list-wrap">
          <div className="tasks-folders-bar">
            <div className="tasks-folders-tabs">
              <button className={activeFolderId === null ? "active" : ""} onClick={() => setActiveFolderId(null)}>Все</button>
              {folders.map((f) => <button key={f.id} className={activeFolderId === f.id ? "active" : ""} onClick={() => setActiveFolderId(f.id)}>{f.name}</button>)}
              <button className={activeFolderId === SYSTEM_ATTENTION_ID ? "active" : ""} onClick={() => setActiveFolderId(SYSTEM_ATTENTION_ID)}>На углубленную проверку</button>
            </div>
            <div>
              <input value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} placeholder="Новая папка" />
              <button className="primary-button" onClick={async () => { if (!token || !newFolderName.trim()) return; await createFolder(token, { name: newFolderName.trim(), filter_json: {} }); setNewFolderName(""); await loadFolders(); }}>+ Папка</button>
            </div>
          </div>
          <div className="tasks-list-header">
            <button className="primary-button" type="button" onClick={() => setIsCreateOpen(true)}>Новая задача</button>
            <h3>{selectedDate}</h3>
          </div>
          <h4>Актуальные</h4><ul className="tasks-list">{grouped.actual.map(renderTask)}</ul>
          <h4>Просроченные</h4><ul className="tasks-list">{grouped.overdue.map(renderTask)}</ul>
          <h4>Выполненные</h4><ul className="tasks-list">{grouped.done.map(renderTask)}</ul>
        </section>
      </div>

      {isCreateOpen ? <div className="admin-modal-backdrop"><form className="admin-modal" onSubmit={onCreateTask}>
        <h3>Новая задача</h3>
        <input style={{ fontSize: 22, fontWeight: 700 }} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название" required />
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание" />
        <input value={dueDateRaw} onChange={(event) => setDueDateRaw(event.target.value)} placeholder="дд.мм.гггг" />
        <input type="time" value={dueTime} onChange={(event) => setDueTime(event.target.value)} />
        <select value={urgency} onChange={(event) => setUrgency(event.target.value as typeof urgency)}>
          <option value="normal">normal</option><option value="urgent">urgent</option><option value="very_urgent">very_urgent</option>
        </select>
        <label className="admin-checkbox-row"><input type="checkbox" checked={requiresVerification} onChange={(event) => setRequiresVerification(event.target.checked)} />Требуется проверка</label>
        <label>Исполнители</label>
        <select multiple value={assigneeIds.map(String)} onChange={(e) => setAssigneeIds(Array.from(e.currentTarget.selectedOptions).map((o) => Number(o.value)))}>{users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select>
        <label>Проверяющий</label>
        <select value={String(verifierIdInput)} onChange={(e) => setVerifierIdInput(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Не выбран</option>{users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
        <label className="admin-checkbox-row"><input type="checkbox" checked={isRecurring} onChange={(e) => setIsRecurring(e.target.checked)} />Повторять</label>
        {isRecurring ? <>
          <select value={recurrenceType} onChange={(e) => setRecurrenceType(e.target.value as typeof recurrenceType)}><option value="daily">daily</option><option value="weekly">weekly</option><option value="monthly">monthly</option><option value="yearly">yearly</option></select>
          <input type="number" min={1} value={recurrenceInterval} onChange={(e) => setRecurrenceInterval(Number(e.target.value) || 1)} />
          <input type="date" value={recurrenceEndDate} onChange={(e) => setRecurrenceEndDate(e.target.value)} />
        </> : <p className="muted">Если дата не указана, задача будет создана как daily recurring автоматически.</p>}
        <div className="admin-modal-actions"><button type="button" className="ghost-button" onClick={() => setIsCreateOpen(false)}>Отмена</button><button type="submit" className="primary-button">Создать</button></div>
      </form></div> : null}

      {isDetailsOpen && selectedTask ? <div className="admin-modal-backdrop"><div className="admin-modal"><h3>{selectedTask.title}</h3>
        <p>{selectedTask.description || "—"}</p>
        <p>Исполнители: {selectedTask.assignee_user_ids.join(", ") || "—"}</p>
        <p>Проверяющий: {selectedTask.verifier_user_id ?? "—"}</p>
        <p>Due: {selectedTask.due_date ?? "—"} {selectedTask.due_time ?? ""}</p>
        {selectedTask.is_recurring || selectedTask.recurrence_master_task_id ? <div>
          <p>Recurring: {selectedTask.recurrence_type ?? "child"}</p>
          {selectedTask.recurrence_state === "active" ? <button className="secondary-button" onClick={() => token && recurrenceAction(token, selectedTask.id, "pause").then(loadTasks)}>Пауза</button> : null}
          {selectedTask.recurrence_state === "paused" ? <button className="secondary-button" onClick={() => token && recurrenceAction(token, selectedTask.id, "resume").then(loadTasks)}>Возобновить</button> : null}
          {selectedTask.recurrence_state !== "stopped" ? <button className="ghost-button" onClick={() => token && recurrenceAction(token, selectedTask.id, "stop").then(loadTasks)}>Стоп</button> : null}
          <p className="muted">Scope для редактирования: single / future / master (в PATCH).</p>
        </div> : null}
        <div className="admin-modal-actions"><button className="ghost-button" onClick={() => setIsDetailsOpen(false)}>Закрыть</button></div>
      </div></div> : null}
    </div>
  );
};

export default TasksModule;
