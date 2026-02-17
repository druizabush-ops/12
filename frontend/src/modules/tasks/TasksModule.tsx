import { FormEvent, useEffect, useMemo, useState } from "react";

import { UserListItem, getUsers } from "../../api/auth";
import {
  TaskDto,
  TaskFolder,
  completeTask,
  createTask,
  getAttentionTasks,
  getCalendar,
  getTaskFolders,
  getTasksByDate,
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const toDateKey = (value: Date) => value.toISOString().slice(0, 10);
const startOfMonth = (value: Date) => new Date(value.getFullYear(), value.getMonth(), 1);

const parseFlexibleDate = (raw: string): string | null => {
  const cleaned = raw.trim();
  if (!cleaned) {
    return null;
  }
  const parts = cleaned.split(/[\.\-/\s]+/).map((item) => Number(item));
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return null;
  }
  const [day, month, yearRaw] = parts;
  const year = yearRaw < 100 ? 2000 + yearRaw : yearRaw;
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) {
    return null;
  }
  return `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
};

const formatDisplayDate = (apiDate: string | null): string => {
  if (!apiDate) {
    return "";
  }
  const [year, month, day] = apiDate.split("-");
  return `${day}.${month}.${year}`;
};

const urgencyLabel = {
  normal: "Обычная",
  urgent: "Срочная",
  very_urgent: "Очень срочная",
} as const;

const urgencyIcon = {
  normal: "",
  urgent: "🔥",
  very_urgent: "🔥🔥🔥",
} as const;

type Tab = "actual" | "overdue" | "done";

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [calendarCounts, setCalendarCounts] = useState<Record<string, number>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [attentionTasks, setAttentionTasks] = useState<TaskDto[]>([]);
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [folders, setFolders] = useState<TaskFolder[]>([]);
  const [activeFolderId, setActiveFolderId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<Tab>("actual");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [detailsTask, setDetailsTask] = useState<TaskDto | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDateInput, setDueDateInput] = useState(formatDisplayDate(selectedDate));
  const [dueTime, setDueTime] = useState("");
  const [noDueDate, setNoDueDate] = useState(false);
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "very_urgent">("normal");
  const [requiresVerification, setRequiresVerification] = useState(false);
  const [verifierSearch, setVerifierSearch] = useState("");
  const [verifierId, setVerifierId] = useState<number | null>(null);
  const [assigneesSearch, setAssigneesSearch] = useState("");
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [formError, setFormError] = useState("");

  const monthDays = useMemo(() => {
    const first = startOfMonth(monthDate);
    const monthStartWeekday = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
    const days = Array.from({ length: daysInMonth }, (_, index) => {
      const day = new Date(first.getFullYear(), first.getMonth(), index + 1);
      return toDateKey(day);
    });
    return [...Array(monthStartWeekday).fill(""), ...days];
  }, [monthDate]);

  const visibleTasks = useMemo(() => {
    if (activeTab === "overdue") {
      return tasks.filter((task) => task.is_overdue);
    }
    if (activeTab === "done") {
      return tasks.filter((task) => task.status === "done");
    }
    return tasks.filter((task) => task.status !== "done" && !task.is_overdue);
  }, [tasks, activeTab]);

  const filteredVerifiers = useMemo(
    () => users.filter((item) => item.full_name.toLowerCase().includes(verifierSearch.toLowerCase())),
    [users, verifierSearch],
  );

  const filteredAssignees = useMemo(
    () => users.filter((item) => item.full_name.toLowerCase().includes(assigneesSearch.toLowerCase())),
    [users, assigneesSearch],
  );

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
      getTasksByDate(token, selectedDate, { folderId: activeFolderId || undefined, includeDone: true }),
      getAttentionTasks(token),
    ]);

    setTasks(dayTasks);
    setAttentionTasks(attention);
  };

  useEffect(() => {
    if (!token) {
      return;
    }
    void Promise.all([getUsers(token), getTaskFolders(token)]).then(([userList, folderList]) => {
      setUsers(userList);
      setFolders(folderList);
    });
  }, [token]);

  useEffect(() => {
    void loadCalendar();
  }, [token, monthDate]);

  useEffect(() => {
    setDueDateInput(formatDisplayDate(selectedDate));
    void loadTasks();
  }, [token, selectedDate, activeFolderId]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setDueDateInput(formatDisplayDate(selectedDate));
    setDueTime("");
    setNoDueDate(false);
    setUrgency("normal");
    setRequiresVerification(false);
    setVerifierSearch("");
    setVerifierId(null);
    setAssigneesSearch("");
    setAssigneeIds([]);
    setFormError("");
  };

  const onCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) {
      return;
    }

    const normalizedDate = noDueDate ? null : parseFlexibleDate(dueDateInput);
    if (!title.trim()) {
      setFormError("Заполните название задачи.");
      return;
    }
    if (!noDueDate && !normalizedDate) {
      setFormError("Укажите корректную дату или выберите «Без срока».");
      return;
    }

    await createTask(token, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: normalizedDate,
      due_time: dueTime || null,
      urgency,
      requires_verification: requiresVerification,
      verifier_user_id: verifierId,
      assignee_user_ids: assigneeIds,
    });

    resetForm();
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
          <div className="tasks-weekdays">
            {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((day, index) => (
              <span key={day} className={index > 4 ? "weekend" : ""}>{day}</span>
            ))}
          </div>
          <div className="tasks-calendar-grid">
            {monthDays.map((dayKey, idx) => {
              if (!dayKey) {
                return <div key={`empty-${idx}`} className="tasks-day-empty" />;
              }
              const weekDay = (new Date(dayKey).getDay() + 6) % 7;
              return (
                <button
                  key={dayKey}
                  type="button"
                  className={`${dayKey === selectedDate ? "tasks-day active" : "tasks-day"} ${weekDay > 4 ? "weekend" : ""}`}
                  onClick={() => setSelectedDate(dayKey)}
                >
                  <span>{new Date(dayKey).getDate()}</span>
                  <small>{calendarCounts[dayKey] ?? 0}</small>
                </button>
              );
            })}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header">
            <h3>Задачи на {formatDisplayDate(selectedDate)}</h3>
            <div className="tasks-list-controls">
              <select value={activeFolderId} onChange={(event) => setActiveFolderId(event.target.value)}>
                <option value="">Все задачи</option>
                {folders.map((folder) => (
                  <option key={folder.id} value={folder.id}>{folder.name}</option>
                ))}
              </select>
              <button className="primary-button" type="button" onClick={() => setIsCreateOpen(true)}>
                Новая задача
              </button>
            </div>
          </div>

          <div className="tasks-tabs">
            <button type="button" className={activeTab === "actual" ? "active" : ""} onClick={() => setActiveTab("actual")}>Актуальные</button>
            <button type="button" className={activeTab === "overdue" ? "active" : ""} onClick={() => setActiveTab("overdue")}>Просроченные</button>
            <button type="button" className={activeTab === "done" ? "active" : ""} onClick={() => setActiveTab("done")}>Выполненные</button>
          </div>

          <ul className="tasks-list">
            {visibleTasks.map((task) => {
              const canVerify = task.requires_verification && (task.verifier_user_id ?? task.created_by_user_id) === user?.id;
              return (
                <li key={task.id} className={`task-item ${task.is_overdue ? "overdue" : ""} ${task.status === "done" ? "done" : ""}`}>
                  <div>
                    <strong>{task.title}</strong>
                    <div className="muted">
                      Дедлайн: {task.due_date ? formatDisplayDate(task.due_date) : "без срока"} {task.due_time ?? ""}
                    </div>
                    <div className="task-badges">
                      <span className="task-badge">{urgencyLabel[task.urgency]} {urgencyIcon[task.urgency]}</span>
                      <span className="task-badge">{task.status}</span>
                      {task.status === "done" ? <span className="task-badge">Выполнено</span> : null}
                      {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
                    </div>
                  </div>
                  <div className="task-actions">
                    <button type="button" className="ghost-button" onClick={() => setDetailsTask(task)}>Подробнее</button>
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
              <input className="task-title-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название" required />
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Описание"
              />
              <input
                value={dueDateInput}
                onChange={(event) => setDueDateInput(event.target.value)}
                placeholder="ДД.ММ.ГГГГ"
                disabled={noDueDate}
              />
              <label className="admin-checkbox-row">
                <input type="checkbox" checked={noDueDate} onChange={(event) => setNoDueDate(event.target.checked)} />
                Без срока
              </label>
              <input type="time" value={dueTime} onChange={(event) => setDueTime(event.target.value)} disabled={noDueDate} />
              <select value={urgency} onChange={(event) => setUrgency(event.target.value as typeof urgency)}>
                <option value="normal">Обычная</option>
                <option value="urgent">Срочная</option>
                <option value="very_urgent">Очень срочная</option>
              </select>
              <label className="admin-checkbox-row">
                <input
                  type="checkbox"
                  checked={requiresVerification}
                  onChange={(event) => setRequiresVerification(event.target.checked)}
                />
                Требуется проверка
              </label>

              <div className="user-dropdown-wrap">
                <input value={verifierSearch} onChange={(event) => setVerifierSearch(event.target.value)} placeholder="Найти проверяющего" />
                <div className="user-dropdown">
                  {filteredVerifiers.map((item) => (
                    <button key={item.id} type="button" onClick={() => { setVerifierId(item.id); setVerifierSearch(item.full_name); }}>
                      {item.full_name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="user-dropdown-wrap">
                <input value={assigneesSearch} onChange={(event) => setAssigneesSearch(event.target.value)} placeholder="Найти исполнителя" />
                <div className="user-dropdown">
                  {filteredAssignees.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        if (!assigneeIds.includes(item.id)) {
                          setAssigneeIds((prev) => [...prev, item.id]);
                        }
                        setAssigneesSearch("");
                      }}
                    >
                      {item.full_name}
                    </button>
                  ))}
                </div>
                {assigneeIds.length > 0 ? <small>Выбрано: {assigneeIds.join(", ")}</small> : null}
              </div>

              {formError ? <p className="form-error">{formError}</p> : null}
            </div>
            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" onClick={() => { resetForm(); setIsCreateOpen(false); }}>
                Отмена
              </button>
              <button type="submit" className="primary-button">
                Создать
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {detailsTask ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <h3>{detailsTask.title}</h3>
            <p>{detailsTask.description || "Без описания"}</p>
            <p>Срок: {detailsTask.due_date ? formatDisplayDate(detailsTask.due_date) : "Без срока"} {detailsTask.due_time || ""}</p>
            <p>Исполнители: {detailsTask.assignee_user_ids.join(", ") || "—"}</p>
            <p>Проверяющий: {detailsTask.verifier_user_id ?? "—"}</p>
            <div className="admin-modal-actions">
              <button type="button" className="primary-button" onClick={() => setDetailsTask(null)}>Закрыть</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
