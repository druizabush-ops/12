import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  TaskDto,
  TaskUserDto,
  completeTask,
  createTask,
  deleteRecurringChildren,
  deleteTask,
  getBadges,
  getTaskById,
  getTasksByDate,
  getUsers,
  recurrenceAction,
  returnActive,
  updateTask,
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const formatDateKey = (value: Date) => {
  const y = value.getFullYear();
  const m = String(value.getMonth() + 1).padStart(2, "0");
  const d = String(value.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};
const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);
const parseDateKey = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
};

type TaskTab = "assigned" | "verify" | "created";

type CalendarCell = { date: Date; isCurrentMonth: boolean; isToday: boolean; isSelected: boolean };

const tabLabel = (tab: TaskTab) => {
  if (tab === "verify") return "На проверку";
  if (tab === "created") return "Поставленные";
  return "Мои задачи";
};

const weekDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => formatDateKey(new Date()));
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [taskTab, setTaskTab] = useState<TaskTab>("assigned");
  const [badges, setBadges] = useState({ verify_total: 0, verify_need_action: false });
  const [users, setUsers] = useState<TaskUserDto[]>([]);
  const [userQuery, setUserQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [detailsTask, setDetailsTask] = useState<TaskDto | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(selectedDate);
  const [dueTime, setDueTime] = useState("");
  const [priority, setPriority] = useState<"normal" | "urgent" | "very_urgent" | "">("normal");
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [verifierIds, setVerifierIds] = useState<number[]>([]);
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrenceType, setRecurrenceType] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
  const [recurrenceInterval, setRecurrenceInterval] = useState("1");
  const [recurrenceDaysOfWeek, setRecurrenceDaysOfWeek] = useState<string[]>([]);
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [formError, setFormError] = useState("");

  const monthDays = useMemo(() => {
    const firstDayOfMonth = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
    const offset = (firstDayOfMonth.getDay() + 6) % 7;
    const startDate = new Date(firstDayOfMonth);
    startDate.setDate(startDate.getDate() - offset);
    return Array.from({ length: 42 }, (_, index): CalendarCell => {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + index);
      const key = formatDateKey(date);
      return {
        date,
        isCurrentMonth: date.getMonth() === monthDate.getMonth(),
        isToday: key === formatDateKey(new Date()),
        isSelected: key === selectedDate,
      };
    });
  }, [monthDate, selectedDate]);

  const activeTasks = useMemo(() => tasks.filter((task) => !task.is_overdue && task.status === "active"), [tasks]);
  const overdueTasks = useMemo(() => tasks.filter((task) => task.is_overdue && task.status !== "done"), [tasks]);
  const doneTasks = useMemo(() => tasks.filter((task) => task.status === "done"), [tasks]);

  const filteredUsers = useMemo(
    () => users.filter((item) => item.username.toLowerCase().includes(userQuery.toLowerCase())),
    [users, userQuery],
  );

  const canManageTask = (task: TaskDto) => {
    const me = user?.id ?? 0;
    return me === task.created_by_user_id || task.verifier_user_ids.includes(me) || (user?.roles ?? []).includes("admin");
  };

  const loadTasks = async () => {
    if (!token) return;
    setTasks(await getTasksByDate(token, selectedDate, taskTab));
  };

  const loadBadges = async () => {
    if (!token) return;
    setBadges(await getBadges(token));
  };

  const syncDetails = async (taskId: string) => {
    if (!token) return;
    setDetailsTask(await getTaskById(token, taskId));
  };

  useEffect(() => {
    if (!token) return;
    void getUsers(token).then(setUsers);
  }, [token]);

  useEffect(() => {
    setDueDate(selectedDate);
    void loadTasks();
    void loadBadges();
  }, [token, selectedDate, taskTab]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setDueDate(selectedDate);
    setDueTime("");
    setPriority("normal");
    setAssigneeIds([]);
    setVerifierIds([]);
    setIsRecurring(false);
    setRecurrenceType("daily");
    setRecurrenceInterval("1");
    setRecurrenceDaysOfWeek([]);
    setRecurrenceEndDate("");
    setFormError("");
  };

  const onToday = () => {
    const today = new Date();
    const dateKey = formatDateKey(today);
    setMonthDate(startOfMonth(today));
    setSelectedDate(dateKey);
  };

  const onCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    setFormError("");
    if (!token || !title.trim()) return;

    const interval = Number(recurrenceInterval || "1");
    if (isRecurring && interval < 1) {
      setFormError("Интервал повторения должен быть не меньше 1.");
      return;
    }
    if (isRecurring && recurrenceType === "weekly" && recurrenceDaysOfWeek.length === 0) {
      setFormError("Для weekly нужно выбрать хотя бы один день недели.");
      return;
    }

    await createTask(token, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      due_time: dueTime || null,
      priority: priority || null,
      verifier_user_ids: verifierIds,
      assignee_user_ids: assigneeIds,
      is_recurring: isRecurring,
      recurrence_type: isRecurring ? recurrenceType : null,
      recurrence_interval: isRecurring ? interval : null,
      recurrence_days_of_week: isRecurring && recurrenceType === "weekly" ? recurrenceDaysOfWeek.join(",") : null,
      recurrence_end_date: isRecurring && recurrenceEndDate ? recurrenceEndDate : null,
    });

    setIsCreateOpen(false);
    resetForm();
    await Promise.all([loadTasks(), loadBadges()]);
  };

  const onEditTask = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !detailsTask) return;
    await updateTask(token, detailsTask.id, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      due_time: dueTime || null,
      priority: priority || null,
      verifier_user_ids: verifierIds,
      assignee_user_ids: assigneeIds,
    });
    setIsEditMode(false);
    await Promise.all([loadTasks(), syncDetails(detailsTask.id)]);
  };

  const openTaskDetails = async (taskId: string) => {
    if (!token) return;
    setIsEditMode(false);
    setDetailsTask(await getTaskById(token, taskId));
  };

  const openEdit = () => {
    if (!detailsTask) return;
    setTitle(detailsTask.title);
    setDescription(detailsTask.description ?? "");
    setDueDate(detailsTask.due_date ?? "");
    setDueTime(detailsTask.due_time ?? "");
    setPriority(detailsTask.priority ?? "normal");
    setAssigneeIds(detailsTask.assignee_user_ids);
    setVerifierIds(detailsTask.verifier_user_ids);
    setIsRecurring(detailsTask.is_recurring);
    setRecurrenceType(detailsTask.recurrence_type ?? "daily");
    setRecurrenceInterval(String(detailsTask.recurrence_interval ?? 1));
    setRecurrenceDaysOfWeek(detailsTask.recurrence_days_of_week ? detailsTask.recurrence_days_of_week.split(",") : []);
    setRecurrenceEndDate(detailsTask.recurrence_end_date ?? "");
    setIsEditMode(true);
  };

  const togglePickerId = (ids: number[], setIds: (value: number[]) => void, id: number) => {
    setIds(ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);
  };

  const renderTaskList = (items: TaskDto[], emptyText: string) => (
    <ul className="tasks-list">
      {items.length === 0 ? <li className="muted">{emptyText}</li> : null}
      {items.map((task) => (
        <li key={task.id} className={`task-item ${task.is_overdue ? "overdue" : ""} ${task.status === "done" ? "done" : ""}`}>
          <div>
            <strong>{task.title}</strong>
            <div className="muted">Дедлайн: {task.due_date ?? "без срока"}{task.due_time ? ` ${task.due_time}` : ""}</div>
            <div className="task-badges">
              <span className="task-badge">{task.status}</span>
              {task.verifier_user_ids.length > 0 ? <span className="task-badge task-badge-success">Можно проверить</span> : null}
              {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
            </div>
            <button type="button" className="link-button" onClick={() => void openTaskDetails(task.id)}>Подробнее</button>
          </div>
        </li>
      ))}
    </ul>
  );

  const renderTaskForm = (onSubmit: (event: FormEvent) => Promise<void>, titleText: string) => (
    <div className="admin-modal-backdrop">
      <form className="admin-modal" onSubmit={(event) => void onSubmit(event)}>
        <h3>{titleText}</h3>
        <div className="admin-column">
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название" required />
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание" />
          <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
          <input type="time" value={dueTime} onChange={(event) => setDueTime(event.target.value)} />
          <select value={priority} onChange={(event) => setPriority(event.target.value as typeof priority)}>
            <option value="normal">normal</option>
            <option value="urgent">urgent</option>
            <option value="very_urgent">very_urgent</option>
          </select>
          <input value={userQuery} onChange={(event) => setUserQuery(event.target.value)} placeholder="Поиск пользователя" />
          <div className="task-picker-columns">
            <div>
              <strong>Исполнители</strong>
              <div className="task-chips">{assigneeIds.map((id) => <span key={`a-${id}`} className="task-chip">{users.find((u) => u.id === id)?.username ?? id}</span>)}</div>
              <ul className="task-user-list">{filteredUsers.map((item) => <li key={`a-${item.id}`}><label><input type="checkbox" checked={assigneeIds.includes(item.id)} onChange={() => togglePickerId(assigneeIds, setAssigneeIds, item.id)} /> {item.username}</label></li>)}</ul>
            </div>
            <div>
              <strong>Проверяющие</strong>
              <div className="task-chips">{verifierIds.map((id) => <span key={`v-${id}`} className="task-chip">{users.find((u) => u.id === id)?.username ?? id}</span>)}</div>
              <ul className="task-user-list">{filteredUsers.map((item) => <li key={`v-${item.id}`}><label><input type="checkbox" checked={verifierIds.includes(item.id)} onChange={() => togglePickerId(verifierIds, setVerifierIds, item.id)} /> {item.username}</label></li>)}</ul>
            </div>
          </div>
          {formError ? <p className="form-error">{formError}</p> : null}
        </div>
        <div className="admin-modal-actions">
          <button type="button" className="ghost-button" onClick={() => { setIsCreateOpen(false); setIsEditMode(false); }}>Отмена</button>
          <button type="submit" className="primary-button">Сохранить</button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="page tasks-page">
      <div className="page-header"><h2>Задачи</h2></div>
      <div className="admin-tabs">
        {(["assigned", "verify", "created"] as TaskTab[]).map((tab) => (
          <button key={tab} type="button" className={taskTab === tab ? "primary-button" : "secondary-button"} onClick={() => setTaskTab(tab)}>
            {tabLabel(tab)}
            {tab === "verify" ? <span className="tasks-tab-badge">{badges.verify_total}{badges.verify_need_action ? " ❗" : ""}</span> : null}
          </button>
        ))}
      </div>
      <div className="tasks-layout">
        <section className="page-card tasks-calendar">
          <div className="tasks-calendar-header">
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() - 1, 1))}>←</button>
            <strong>{monthDate.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}</strong>
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 1))}>→</button>
          </div>
          <button className="secondary-button tasks-today-button" type="button" onClick={onToday}>Сегодня</button>
          <div className="tasks-weekdays">{weekDays.map((day, i) => <span key={day} className={i >= 5 ? "weekend" : ""}>{day}</span>)}</div>
          <div className="tasks-calendar-grid">
            {monthDays.map((cell) => {
              const dayKey = formatDateKey(cell.date);
              const isWeekend = cell.date.getDay() === 0 || cell.date.getDay() === 6;
              return (
                <button key={dayKey} type="button" className={`tasks-day ${cell.isSelected ? "active" : ""} ${isWeekend ? "weekend" : ""} ${cell.isCurrentMonth ? "" : "outside"}`} onClick={() => setSelectedDate(dayKey)}>
                  <span>{cell.date.getDate()}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header">
            <h3>{tabLabel(taskTab)}: {selectedDate}</h3>
            <button className="primary-button" type="button" onClick={() => { resetForm(); setIsCreateOpen(true); }}>Новая задача</button>
          </div>
          <h4>Актуальные</h4>
          {renderTaskList(activeTasks, "Нет актуальных задач.")}
          <h4>Просроченные</h4>
          {renderTaskList(overdueTasks, "Нет просроченных задач.")}
          <h4>Выполненные</h4>
          {renderTaskList(doneTasks, "Нет выполненных задач.")}
        </section>
      </div>

      {isCreateOpen ? renderTaskForm(onCreateTask, "Новая задача") : null}
      {isEditMode ? renderTaskForm(onEditTask, "Редактирование") : null}

      {detailsTask && !isEditMode ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <h3>{detailsTask.title}</h3>
            <p>{detailsTask.description || "—"}</p>
            <p>Постановщик: {users.find((item) => item.id === detailsTask.created_by_user_id)?.username ?? detailsTask.created_by_user_id}</p>
            <p>Исполнители: {detailsTask.assignee_user_ids.map((id) => users.find((item) => item.id === id)?.username ?? id).join(", ") || "—"}</p>
            <p>Проверяющие: {detailsTask.verifier_user_ids.map((id) => users.find((item) => item.id === id)?.username ?? id).join(", ") || "—"}</p>
            <p>Срок: {detailsTask.due_date || "—"} {detailsTask.due_time || ""}</p>
            <p>Повторение: {detailsTask.is_recurring ? `${detailsTask.recurrence_type ?? ""} / ${detailsTask.recurrence_interval ?? 1}` : "нет"}</p>
            <p>Статус: {detailsTask.status}</p>
            <div className="task-actions">
              {detailsTask.status === "active" && canManageTask(detailsTask) ? <button type="button" className="secondary-button" onClick={openEdit}>Редактировать</button> : null}
              {detailsTask.status === "active" && detailsTask.assignee_user_ids.includes(user?.id ?? 0) ? <button type="button" className="secondary-button" onClick={() => void completeTask(token!, detailsTask.id).then(async () => { await loadTasks(); await syncDetails(detailsTask.id); })}>Выполнить</button> : null}
              {detailsTask.status === "done_pending_verify" && detailsTask.verifier_user_ids.includes(user?.id ?? 0) ? <button type="button" className="secondary-button" onClick={() => void verifyTask(token!, detailsTask.id).then(async () => { await loadTasks(); await syncDetails(detailsTask.id); })}>Подтвердить</button> : null}
              {detailsTask.status === "done" && canManageTask(detailsTask) ? <button type="button" className="ghost-button" onClick={() => void returnActive(token!, detailsTask.id).then(async () => { await loadTasks(); await syncDetails(detailsTask.id); })}>Вернуть в active</button> : null}
              {detailsTask.status === "active" && ((user?.id === detailsTask.created_by_user_id) || (user?.roles ?? []).includes("admin")) ? <button type="button" className="ghost-button" onClick={() => void deleteTask(token!, detailsTask.id).then(async () => { setDetailsTask(null); await loadTasks(); })}>Удалить</button> : null}
              {detailsTask.is_recurring && !detailsTask.recurrence_master_task_id && (user?.id === detailsTask.created_by_user_id) ? <button type="button" className="ghost-button" onClick={() => void deleteRecurringChildren(token!, detailsTask.id, "all").then(async () => { await loadTasks(); await syncDetails(detailsTask.id); })}>Удалить children</button> : null}
            </div>
            <div className="admin-modal-actions"><button type="button" className="ghost-button" onClick={() => setDetailsTask(null)}>Закрыть</button></div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
