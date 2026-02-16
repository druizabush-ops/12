import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  TaskDto,
  completeTask,
  createTask,
  getAttentionTasks,
  getCalendar,
  getTasksByDate,
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const toDateKey = (value: Date) => value.toISOString().slice(0, 10);

const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [calendarCounts, setCalendarCounts] = useState<Record<string, number>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [attentionTasks, setAttentionTasks] = useState<TaskDto[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(selectedDate);
  const [dueTime, setDueTime] = useState("");
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "very_urgent">("normal");
  const [requiresVerification, setRequiresVerification] = useState(false);
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
    const [dayTasks, attention] = await Promise.all([
      getTasksByDate(token, selectedDate),
      getAttentionTasks(token),
    ]);

    setTasks(dayTasks);
    setAttentionTasks(attention);
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
      urgency,
      requires_verification: requiresVerification,
      verifier_user_id: verifierIdInput ? Number(verifierIdInput) : null,
      assignee_user_ids: assigneeIds,
    });

    setTitle("");
    setDescription("");
    setDueTime("");
    setUrgency("normal");
    setRequiresVerification(false);
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
                <span>{new Date(dayKey).getDate()}</span>
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

          <ul className="tasks-list">
            {tasks.map((task) => {
              const canVerify = task.requires_verification && (task.verifier_user_id ?? task.created_by_user_id) === user?.id;
              return (
                <li key={task.id} className={task.is_overdue ? "task-item overdue" : "task-item"}>
                  <div>
                    <strong>{task.title}</strong>
                    <div className="muted">
                      Дедлайн: {task.due_date ?? "без срока"} {task.due_time ?? ""}
                    </div>
                    <div className="task-badges">
                      <span className="task-badge">{task.urgency}</span>
                      <span className="task-badge">{task.status}</span>
                      {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
                    </div>
                  </div>
                  <div className="task-actions">
                    {task.status !== "done" ? (
                      <button type="button" className="secondary-button" onClick={() => onComplete(task.id)}>
                        Выполнить
                      </button>
                    ) : null}
                    {canVerify && !task.verified_at ? (
                      <button type="button" className="ghost-button" onClick={() => onVerify(task.id)}>
                        Проверить
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="tasks-attention">
            <h4>На углублённую проверку</h4>
            {attentionTasks.length === 0 ? <p className="muted">Нет просроченных задач для проверки.</p> : null}
            <ul className="tasks-attention-list">
              {attentionTasks.map((task) => (
                <li key={task.id}>{task.title}</li>
              ))}
            </ul>
          </div>
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
              <select value={urgency} onChange={(event) => setUrgency(event.target.value as typeof urgency)}>
                <option value="normal">normal</option>
                <option value="urgent">urgent</option>
                <option value="very_urgent">very_urgent</option>
              </select>
              <label className="admin-checkbox-row">
                <input
                  type="checkbox"
                  checked={requiresVerification}
                  onChange={(event) => setRequiresVerification(event.target.checked)}
                />
                Требуется проверка
              </label>
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
