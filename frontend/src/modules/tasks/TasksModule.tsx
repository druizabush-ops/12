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
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const toDateKey = (value: Date) => value.toISOString().slice(0, 10);
const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);
const dayOfMonth = (value: string) => Number(value.split("-")[2] ?? "1");
const parseDateKey = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
};

type TaskTab = "assigned" | "verify" | "created";

const tabLabel = (tab: TaskTab) => {
  if (tab === "verify") return "На проверку";
  if (tab === "created") return "Поставленные";
  return "Все задачи";
};

const weekDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [taskTab, setTaskTab] = useState<TaskTab>("assigned");
  const [badges, setBadges] = useState({ pending_verify_count: 0, fresh_completed_count: 0 });
  const [users, setUsers] = useState<TaskUserDto[]>([]);
  const [userQuery, setUserQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

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
    const first = startOfMonth(monthDate);
    const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    return Array.from({ length: daysInMonth }, (_, index) => {
      const day = new Date(first.getFullYear(), first.getMonth(), index + 1);
      return toDateKey(day);
    });
  }, [monthDate]);

  const activeTasks = useMemo(() => tasks.filter((task) => !task.is_overdue && task.status !== "done"), [tasks]);
  const overdueTasks = useMemo(() => tasks.filter((task) => task.is_overdue), [tasks]);
  const doneTasks = useMemo(() => tasks.filter((task) => task.status === "done"), [tasks]);

  const filteredUsers = useMemo(
    () => users.filter((item) => item.username.toLowerCase().includes(userQuery.toLowerCase())),
    [users, userQuery],
  );

  const loadTasks = async () => {
    if (!token) return;
    setTasks(await getTasksByDate(token, selectedDate, taskTab));
  };

  const loadBadges = async () => {
    if (!token) return;
    setBadges(await getBadges(token));
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

  const onToday = async () => {
    const today = new Date();
    const dateKey = toDateKey(today);
    setMonthDate(startOfMonth(today));
    setSelectedDate(dateKey);
    if (token) {
      setTasks(await getTasksByDate(token, dateKey, taskTab));
      setBadges(await getBadges(token));
    }
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

    setTitle("");
    setDescription("");
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
    setIsCreateOpen(false);
    await Promise.all([loadTasks(), loadBadges()]);
  };

  const onOpenMasterTask = async (task: TaskDto) => {
    if (!token || !task.recurrence_master_task_id) return;
    const master = await getTaskById(token, task.recurrence_master_task_id);
    const dateKey = master.due_date ?? toDateKey(new Date());
    const parsedDate = parseDateKey(dateKey);
    setMonthDate(startOfMonth(parsedDate));
    setSelectedDate(dateKey);
  };

  const togglePickerId = (ids: number[], setIds: (value: number[]) => void, id: number) => {
    setIds(ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);
  };

  const renderTaskList = (items: TaskDto[], emptyText: string) => (
    <ul className="tasks-list">
      {items.length === 0 ? <li className="muted">{emptyText}</li> : null}
      {items.map((task) => {
        const canVerify = task.status === "done_pending_verify" && (task.verifier_user_ids.includes(user?.id ?? 0) || user?.id === task.created_by_user_id);
        const canReturn = task.status !== "active" && user?.id === task.created_by_user_id;
        const canComplete = task.status === "active" && (task.assignee_user_ids.includes(user?.id ?? 0) || task.created_by_user_id === user?.id);
        return (
          <li key={task.id} className={`task-item ${task.is_overdue ? "overdue" : ""} ${task.status === "done" ? "done" : ""}`}>
            <div>
              <strong>{task.title}</strong>
              <div className="muted">Дедлайн: {task.due_date ?? "без срока"}{task.due_time ? ` ${task.due_time}` : ""}</div>
              <div className="task-badges">
                <span className="task-badge">{task.status}</span>
                {task.status === "done_pending_verify" ? <span className="task-badge task-badge-success">Можно проверить</span> : null}
                {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
              </div>
              {task.recurrence_master_task_id ? (
                <button type="button" className="link-button" onClick={() => void onOpenMasterTask(task)}>
                  Подробнее
                </button>
              ) : null}
            </div>
            <div className="task-actions">
              {canComplete ? <button type="button" className="secondary-button" onClick={() => void completeTask(token!, task.id).then(loadTasks)}>Выполнить</button> : null}
              {canVerify ? <button type="button" className="ghost-button" onClick={() => void verifyTask(token!, task.id).then(loadTasks)}>Проверить</button> : null}
              {canReturn ? <button type="button" className="ghost-button" onClick={() => void returnActive(token!, task.id).then(loadTasks)}>Вернуть в активные</button> : null}
              {task.status === "active" && user?.id === task.created_by_user_id ? (
                <button type="button" className="ghost-button" onClick={() => void deleteTask(token!, task.id).then(loadTasks)}>Удалить</button>
              ) : null}
              {task.is_recurring && !task.recurrence_master_task_id && user?.id === task.created_by_user_id ? (
                <>
                  <button type="button" className="ghost-button" onClick={() => void recurrenceAction(token!, task.id, "pause").then(loadTasks)}>Пауза</button>
                  <button type="button" className="ghost-button" onClick={() => void recurrenceAction(token!, task.id, "resume").then(loadTasks)}>Возобновить</button>
                  <button type="button" className="ghost-button" onClick={() => void recurrenceAction(token!, task.id, "stop").then(loadTasks)}>Стоп</button>
                  <button type="button" className="ghost-button" onClick={() => void deleteRecurringChildren(token!, task.id, "all").then(loadTasks)}>Удалить children</button>
                </>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="page tasks-page">
      <div className="page-header">
        <h2>Задачи</h2>
      </div>
      <div className="admin-tabs">
        {(["assigned", "verify", "created"] as TaskTab[]).map((tab) => (
          <button key={tab} type="button" className={taskTab === tab ? "primary-button" : "secondary-button"} onClick={() => setTaskTab(tab)}>
            {tabLabel(tab)}
            {tab === "verify" ? <span className="tasks-tab-badge">{badges.pending_verify_count}/{badges.fresh_completed_count}</span> : null}
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
          <button className="secondary-button tasks-today-button" type="button" onClick={() => void onToday()}>Сегодня</button>
          <div className="tasks-weekdays">{weekDays.map((day, i) => <span key={day} className={i >= 5 ? "weekend" : ""}>{day}</span>)}</div>
          <div className="tasks-calendar-grid">
            {monthDays.map((dayKey) => {
              const day = parseDateKey(dayKey);
              const jsDay = day.getDay();
              const isWeekend = jsDay === 0 || jsDay === 6;
              return (
                <button key={dayKey} type="button" className={`tasks-day ${dayKey === selectedDate ? "active" : ""} ${isWeekend ? "weekend" : ""}`} onClick={() => setSelectedDate(dayKey)}>
                  <span>{dayOfMonth(dayKey)}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header">
            <h3>{tabLabel(taskTab)}: {selectedDate}</h3>
            <button className="primary-button" type="button" onClick={() => setIsCreateOpen(true)}>Новая задача</button>
          </div>
          <h4>Актуальные</h4>
          {renderTaskList(activeTasks, "Нет актуальных задач.")}
          <h4>Просроченные</h4>
          {renderTaskList(overdueTasks, "Нет просроченных задач.")}
          <h4>Выполненные</h4>
          {renderTaskList(doneTasks, "Нет выполненных задач.")}
        </section>
      </div>

      {isCreateOpen ? (
        <div className="admin-modal-backdrop">
          <form className="admin-modal" onSubmit={onCreateTask}>
            <h3>Новая задача</h3>
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

              <label><input type="checkbox" checked={isRecurring} onChange={(event) => setIsRecurring(event.target.checked)} /> Повторение</label>
              {isRecurring ? (
                <div className="admin-column">
                  <select value={recurrenceType} onChange={(event) => setRecurrenceType(event.target.value as typeof recurrenceType)}>
                    <option value="daily">daily</option><option value="weekly">weekly</option><option value="monthly">monthly</option><option value="yearly">yearly</option>
                  </select>
                  <input type="number" min={1} value={recurrenceInterval} onChange={(event) => setRecurrenceInterval(event.target.value)} placeholder="Интервал" />
                  {recurrenceType === "weekly" ? (
                    <div className="task-weekdays">{["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((day, index) => (
                      <label key={day}><input type="checkbox" checked={recurrenceDaysOfWeek.includes(String(index + 1))} onChange={(event) => setRecurrenceDaysOfWeek((prev) => event.target.checked ? [...prev, String(index + 1)] : prev.filter((item) => item !== String(index + 1)))} />{day}</label>
                    ))}</div>
                  ) : null}
                  <input type="date" value={recurrenceEndDate} onChange={(event) => setRecurrenceEndDate(event.target.value)} placeholder="Дата окончания" />
                </div>
              ) : null}
              {formError ? <p className="form-error">{formError}</p> : null}
            </div>
            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" onClick={() => setIsCreateOpen(false)}>Отмена</button>
              <button type="submit" className="primary-button">Создать</button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
