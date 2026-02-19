import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  TaskDto,
  completeTask,
  createTask,
  getCalendar,
  getTaskBadges,
  getTaskById,
  getTasksByDate,
  updateTask,
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

const priorityFlames = (priority: TaskDto["priority"]) => {
  if (priority === "very_urgent") return "🔥🔥🔥";
  if (priority === "urgent") return "🔥🔥";
  if (priority === "normal") return "🔥";
  return "—";
};

const TasksModule = ({ permissions }: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const isAdmin = Boolean(permissions?.manage_access || permissions?.admin || permissions?.can_manage_access);

  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [calendarCounts, setCalendarCounts] = useState<Record<string, number>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<TaskDto | null>(null);
  const [detailTask, setDetailTask] = useState<TaskDto | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(selectedDate);
  const [dueTime, setDueTime] = useState("");
  const [priority, setPriority] = useState<"normal" | "urgent" | "very_urgent" | "">("normal");
  const [verifierIdInput, setVerifierIdInput] = useState("");
  const [assigneesInput, setAssigneesInput] = useState("");
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrenceType, setRecurrenceType] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
  const [recurrenceInterval, setRecurrenceInterval] = useState("1");
  const [recurrenceDaysOfWeek, setRecurrenceDaysOfWeek] = useState<string[]>([]);
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [formError, setFormError] = useState("");

  const [pendingVerifyCount, setPendingVerifyCount] = useState(0);
  const [freshCompletedFlag, setFreshCompletedFlag] = useState(false);

  const monthDays = useMemo(() => {
    const first = startOfMonth(monthDate);
    const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    return Array.from({ length: daysInMonth }, (_, index) => {
      const day = new Date(first.getFullYear(), first.getMonth(), index + 1);
      return toDateKey(day);
    });
  }, [monthDate]);

  const calendarShift = useMemo(() => {
    const firstDay = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
    const jsWeekday = firstDay.getDay();
    return (jsWeekday + 6) % 7;
  }, [monthDate]);

  const activeTasks = useMemo(() => tasks.filter((task) => task.status === "active" && !task.is_overdue), [tasks]);
  const overdueTasks = useMemo(() => tasks.filter((task) => task.status === "active" && task.is_overdue), [tasks]);
  const doneTasks = useMemo(() => tasks.filter((task) => task.status === "done"), [tasks]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setDueDate(selectedDate);
    setDueTime("");
    setPriority("normal");
    setVerifierIdInput("");
    setAssigneesInput("");
    setIsRecurring(false);
    setRecurrenceType("daily");
    setRecurrenceInterval("1");
    setRecurrenceDaysOfWeek([]);
    setRecurrenceEndDate("");
    setFormError("");
  };

  const fillFormFromTask = (task: TaskDto) => {
    setTitle(task.title);
    setDescription(task.description ?? "");
    setDueDate(task.due_date ?? "");
    setDueTime(task.due_time ?? "");
    setPriority(task.priority ?? "normal");
    setVerifierIdInput(task.verifier_user_id ? String(task.verifier_user_id) : "");
    setAssigneesInput(task.assignee_user_ids.join(", "));
    setIsRecurring(task.is_recurring);
    setRecurrenceType(task.recurrence_type ?? "daily");
    setRecurrenceInterval(String(task.recurrence_interval ?? 1));
    setRecurrenceDaysOfWeek((task.recurrence_days_of_week ?? "").split(",").filter(Boolean));
    setRecurrenceEndDate(task.recurrence_end_date ?? "");
    setFormError("");
  };

  const loadCalendar = async () => {
    if (!token) return;
    const from = toDateKey(startOfMonth(monthDate));
    const to = toDateKey(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0));
    const data = await getCalendar(token, from, to);
    setCalendarCounts(Object.fromEntries(data.map((item) => [item.date, item.count])));
  };

  const loadTasks = async () => {
    if (!token) return;
    setTasks(await getTasksByDate(token, selectedDate));
  };

  const loadBadges = async () => {
    if (!token) return;
    const badges = await getTaskBadges(token);
    setPendingVerifyCount(badges.pending_verify_count);
    setFreshCompletedFlag(badges.fresh_completed_flag);
  };

  useEffect(() => {
    void loadCalendar();
  }, [token, monthDate]);

  useEffect(() => {
    setDueDate(selectedDate);
    void loadTasks();
  }, [token, selectedDate]);

  useEffect(() => {
    void loadBadges();
  }, [token]);

  const onToday = async () => {
    const today = new Date();
    setMonthDate(startOfMonth(today));
    setSelectedDate(toDateKey(today));
    await Promise.all([loadCalendar(), loadTasks()]);
  };

  const onSubmitTask = async (event: FormEvent) => {
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

    const assigneeIds = assigneesInput
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((value) => Number.isInteger(value) && value > 0);

    const payload = {
      title: title.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      due_time: dueTime || null,
      priority: priority || null,
      verifier_user_id: verifierIdInput ? Number(verifierIdInput) : null,
      assignee_user_ids: assigneeIds,
      is_recurring: isRecurring,
      recurrence_type: isRecurring ? recurrenceType : null,
      recurrence_interval: isRecurring ? interval : null,
      recurrence_days_of_week: isRecurring && recurrenceType === "weekly" ? recurrenceDaysOfWeek.join(",") : null,
      recurrence_end_date: isRecurring && recurrenceEndDate ? recurrenceEndDate : null,
    };

    if (editingTask) {
      await updateTask(token, editingTask.id, payload);
    } else {
      await createTask(token, payload);
    }

    setIsCreateOpen(false);
    setEditingTask(null);
    resetForm();
    await Promise.all([loadTasks(), loadCalendar(), loadBadges()]);
  };

  const onComplete = async (taskId: string) => {
    if (!token) return;
    await completeTask(token, taskId);
    await Promise.all([loadTasks(), loadBadges()]);
  };

  const onVerify = async (taskId: string) => {
    if (!token) return;
    await verifyTask(token, taskId);
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

  const openCreateModal = () => {
    setEditingTask(null);
    resetForm();
    setIsCreateOpen(true);
  };

  const openEditModal = (task: TaskDto) => {
    setEditingTask(task);
    fillFormFromTask(task);
    setIsCreateOpen(true);
  };

  const renderTaskList = (items: TaskDto[], emptyText: string) => (
    <ul className="tasks-list">
      {items.length === 0 ? <li className="muted">{emptyText}</li> : null}
      {items.map((task) => {
        const canVerify = task.status === "done_pending_verify" && user?.id === task.created_by_user_id;
        const canEdit = task.status === "active" && (user?.id === task.created_by_user_id || isAdmin);
        return (
          <li key={task.id} className={`task-item ${task.is_overdue ? "overdue" : ""} ${task.status === "done" ? "done" : ""}`}>
            <div>
              <strong>{task.title}</strong>
              <div className="muted">
                Дедлайн: {task.due_date ?? "без срока"}
                {task.due_time ? <span className="task-due-time">{task.due_time}</span> : null}
              </div>
              <div className="task-badges">
                <span className="task-badge">{priorityFlames(task.priority)}</span>
                <span className="task-badge">{task.status}</span>
                {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
              </div>
              {task.recurrence_master_task_id ? (
                <button type="button" className="link-button" onClick={() => void onOpenMasterTask(task)}>
                  Открыть исходную задачу
                </button>
              ) : null}
            </div>
            <div className="task-actions">
              <button type="button" className="ghost-button" onClick={() => setDetailTask(task)}>
                Подробнее
              </button>
              {canEdit ? (
                <button type="button" className="ghost-button" onClick={() => openEditModal(task)}>
                  Редактировать
                </button>
              ) : null}
              {task.status === "active" ? (
                <button type="button" className="secondary-button" onClick={() => onComplete(task.id)}>
                  Выполнить
                </button>
              ) : null}
              {canVerify ? (
                <button type="button" className="ghost-button" onClick={() => onVerify(task.id)}>
                  Проверить
                </button>
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
        <p>
          Календарь задач и контроль просроченных обязательств. Проверка: <strong>{pendingVerifyCount}</strong>
          {freshCompletedFlag ? <span className="task-badge task-badge-danger tasks-verify-alert">!</span> : null}
        </p>
      </div>
      <div className="tasks-layout">
        <section className="page-card tasks-calendar">
          <div className="tasks-calendar-header">
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() - 1, 1))}>
              ←
            </button>
            <strong>{monthDate.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}</strong>
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 1))}>
              →
            </button>
          </div>
          <button className="secondary-button tasks-today-button" type="button" onClick={() => void onToday()}>
            Сегодня
          </button>
          <div className="tasks-calendar-weekdays">
            {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>
          <div className="tasks-calendar-grid" data-has-events={Object.keys(calendarCounts).length > 0}>
            {Array.from({ length: calendarShift }).map((_, idx) => (
              <div key={`empty-${idx}`} className="tasks-day-empty" />
            ))}
            {monthDays.map((dayKey) => (
              <button
                key={dayKey}
                type="button"
                className={dayKey === selectedDate ? "tasks-day active" : "tasks-day"}
                onClick={() => setSelectedDate(dayKey)}
              >
                <span>{dayOfMonth(dayKey)}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header">
            <h3>Задачи на {selectedDate}</h3>
            <button className="primary-button" type="button" onClick={openCreateModal}>
              Новая задача
            </button>
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
          <form className="admin-modal" onSubmit={onSubmitTask}>
            <h3>{editingTask ? "Редактировать задачу" : "Новая задача"}</h3>
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
              <input
                value={verifierIdInput}
                onChange={(event) => setVerifierIdInput(event.target.value)}
                placeholder="ID проверяющего (опционально)"
              />
              <input
                value={assigneesInput}
                onChange={(event) => setAssigneesInput(event.target.value)}
                placeholder="ID исполнителей через запятую"
              />

              <label>
                <input type="checkbox" checked={isRecurring} onChange={(event) => setIsRecurring(event.target.checked)} /> Повторение
              </label>
              {isRecurring ? (
                <div className="admin-column">
                  <select value={recurrenceType} onChange={(event) => setRecurrenceType(event.target.value as typeof recurrenceType)}>
                    <option value="daily">daily</option>
                    <option value="weekly">weekly</option>
                    <option value="monthly">monthly</option>
                    <option value="yearly">yearly</option>
                  </select>
                  <input
                    type="number"
                    min={1}
                    value={recurrenceInterval}
                    onChange={(event) => setRecurrenceInterval(event.target.value)}
                    placeholder="Интервал"
                  />
                  {recurrenceType === "weekly" ? (
                    <div className="task-weekdays">
                      {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                        <label key={day}>
                          <input
                            type="checkbox"
                            checked={recurrenceDaysOfWeek.includes(String(day))}
                            onChange={(event) => {
                              setRecurrenceDaysOfWeek((prev) =>
                                event.target.checked ? [...prev, String(day)] : prev.filter((item) => item !== String(day)),
                              );
                            }}
                          />
                          {day}
                        </label>
                      ))}
                    </div>
                  ) : null}
                  <input
                    type="date"
                    value={recurrenceEndDate}
                    onChange={(event) => setRecurrenceEndDate(event.target.value)}
                    placeholder="Дата окончания"
                  />
                </div>
              ) : null}
              {formError ? <p className="form-error">{formError}</p> : null}
            </div>
            <div className="admin-modal-actions">
              <button
                type="button"
                className="ghost-button"
                onClick={() => {
                  setIsCreateOpen(false);
                  setEditingTask(null);
                }}
              >
                Отмена
              </button>
              <button type="submit" className="primary-button">
                {editingTask ? "Сохранить" : "Создать"}
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {detailTask ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <h3>Подробнее</h3>
            <div className="admin-column">
              <p><strong>Название:</strong> {detailTask.title}</p>
              <p><strong>Описание:</strong> {detailTask.description || "—"}</p>
              <p><strong>Создал:</strong> {detailTask.created_by_name}</p>
              <p><strong>Исполнители:</strong> {detailTask.assignee_names.join(", ") || "—"}</p>
              <p><strong>Проверяющий:</strong> {detailTask.verifier_name || "—"}</p>
              <p><strong>Срок:</strong> {detailTask.due_date || "—"} {detailTask.due_time || ""}</p>
              <p><strong>Повторение:</strong> {detailTask.is_recurring ? `${detailTask.recurrence_type ?? ""}, интервал ${detailTask.recurrence_interval ?? 1}` : "нет"}</p>
              <p><strong>Статус:</strong> {detailTask.status}</p>
              <p><strong>Создана:</strong> {detailTask.created_at}</p>
              <p><strong>Завершена:</strong> {detailTask.completed_at || "—"}</p>
              <p><strong>Подтверждена:</strong> {detailTask.verified_at || "—"}</p>
            </div>
            <div className="admin-modal-actions">
              <button type="button" className="primary-button" onClick={() => setDetailTask(null)}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
