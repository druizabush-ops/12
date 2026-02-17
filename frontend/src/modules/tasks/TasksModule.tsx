import { FormEvent, useEffect, useMemo, useState } from "react";

import { TaskDto, completeTask, createTask, getCalendar, getTasksByDate, verifyTask } from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const toDateKey = (value: Date) => value.toISOString().slice(0, 10);
const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);
const dayOfMonth = (value: string) => Number(value.split("-")[2] ?? "1");

const priorityFlames = (priority: TaskDto["priority"]) => {
  if (priority === "very_urgent") return "🔥🔥🔥";
  if (priority === "urgent") return "🔥🔥";
  if (priority === "normal") return "🔥";
  return "—";
};

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [calendarCounts, setCalendarCounts] = useState<Record<string, number>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(selectedDate);
  const [dueTime, setDueTime] = useState("");
  const [priority, setPriority] = useState<"normal" | "urgent" | "very_urgent" | "">("normal");
  const [verifierIdInput, setVerifierIdInput] = useState("");
  const [assigneesInput, setAssigneesInput] = useState("");

  const monthDays = useMemo(() => {
    const first = startOfMonth(monthDate);
    const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    return Array.from({ length: daysInMonth }, (_, index) => {
      const day = new Date(first.getFullYear(), first.getMonth(), index + 1);
      return toDateKey(day);
    });
  }, [monthDate]);

  const activeTasks = useMemo(
    () => tasks.filter((task) => !task.is_overdue && task.status !== "done"),
    [tasks],
  );
  const overdueTasks = useMemo(() => tasks.filter((task) => task.is_overdue), [tasks]);
  const doneTasks = useMemo(() => tasks.filter((task) => task.status === "done"), [tasks]);

  const loadCalendar = async () => {
    if (!token) {
      return;
    }
    const from = toDateKey(startOfMonth(monthDate));
    const to = toDateKey(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0));
    const data = await getCalendar(token, from, to);
    setCalendarCounts(Object.fromEntries(data.map((item) => [item.date, item.count])));
  };

  const loadTasks = async () => {
    if (!token) {
      return;
    }
    setTasks(await getTasksByDate(token, selectedDate));
  };

  useEffect(() => {
    void loadCalendar();
  }, [token, monthDate]);

  useEffect(() => {
    setDueDate(selectedDate);
    void loadTasks();
  }, [token, selectedDate]);

  const onCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !title.trim()) {
      return;
    }

    const assigneeIds = assigneesInput
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((value) => Number.isInteger(value) && value > 0);

    await createTask(token, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      due_time: dueTime || null,
      priority: priority || null,
      verifier_user_id: verifierIdInput ? Number(verifierIdInput) : null,
      assignee_user_ids: assigneeIds,
    });

    setTitle("");
    setDescription("");
    setDueTime("");
    setPriority("normal");
    setVerifierIdInput("");
    setAssigneesInput("");
    setIsCreateOpen(false);
    await Promise.all([loadTasks(), loadCalendar()]);
  };

  const onComplete = async (taskId: string) => {
    if (!token) {
      return;
    }
    await completeTask(token, taskId);
    await loadTasks();
  };

  const onVerify = async (taskId: string) => {
    if (!token) {
      return;
    }
    await verifyTask(token, taskId);
    await loadTasks();
  };

  const renderTaskList = (items: TaskDto[], emptyText: string) => (
    <ul className="tasks-list">
      {items.length === 0 ? <li className="muted">{emptyText}</li> : null}
      {items.map((task) => {
        const canVerify = task.status === "done_pending_verify" && user?.id === task.verifier_user_id;
        return (
          <li key={task.id} className={task.is_overdue ? "task-item overdue" : "task-item"}>
            <div>
              <strong>{task.title}</strong>
              <div className="muted">
                Дедлайн: {task.due_date ?? "без срока"} {task.due_time ?? ""}
              </div>
              <div className="task-badges">
                <span className="task-badge">{priorityFlames(task.priority)}</span>
                <span className="task-badge">{task.status}</span>
                {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
              </div>
            </div>
            <div className="task-actions">
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
        <p>Календарь задач и контроль просроченных обязательств.</p>
      </div>
      <div className="tasks-layout">
        <section className="page-card tasks-calendar">
          <div className="tasks-calendar-header">
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() - 1, 1))}>
              ←
            </button>
            <strong>
              {monthDate.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}
            </strong>
            <button className="ghost-button" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 1))}>
              →
            </button>
          </div>
          <div className="tasks-calendar-grid">
            {monthDays.map((dayKey) => (
              <button
                key={dayKey}
                type="button"
                className={dayKey === selectedDate ? "tasks-day active" : "tasks-day"}
                onClick={() => setSelectedDate(dayKey)}
              >
                <span>{dayOfMonth(dayKey)}</span>
                <small>{calendarCounts[dayKey] ?? 0}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header">
            <h3>Задачи на {selectedDate}</h3>
            <button className="primary-button" type="button" onClick={() => setIsCreateOpen(true)}>
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
          <form className="admin-modal" onSubmit={onCreateTask}>
            <h3>Новая задача</h3>
            <div className="admin-column">
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название" required />
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Описание"
              />
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
            </div>
            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" onClick={() => setIsCreateOpen(false)}>
                Отмена
              </button>
              <button type="submit" className="primary-button">
                Создать
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
