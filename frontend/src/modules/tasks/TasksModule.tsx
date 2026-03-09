import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  TaskDto,
  TaskUserDto,
  completeTask,
  createTask,
  deleteRecurringChildren,
  deleteTask,
  downloadTasksTemplate,
  exportTasksExcel,
  getBadges,
  getTaskById,
  getTasksImportPreview,
  getTasksByDate,
  getUsers,
  importTasksExcel,
  TasksImportPreviewResponse,
  TasksImportPreviewRow,
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

type TaskTab = "assigned" | "verify" | "created";

type CalendarCell = { date: Date; isCurrentMonth: boolean; isToday: boolean; isSelected: boolean };
type AdminActionType = "template" | "export" | "import";
type PinPurpose = "template" | "export" | "import";

const tabLabel = (tab: TaskTab) => {
  if (tab === "verify") return "На проверку";
  if (tab === "created") return "Поставленные";
  return "Мои задачи";
};

const weekDays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const weekDayOptions = [
  { value: "1", label: "Пн" },
  { value: "2", label: "Вт" },
  { value: "3", label: "Ср" },
  { value: "4", label: "Чт" },
  { value: "5", label: "Пт" },
  { value: "6", label: "Сб" },
  { value: "7", label: "Вс" },
];

const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const me = user?.id ?? 0;

  const [monthDate, setMonthDate] = useState(() => startOfMonth(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => formatDateKey(new Date()));
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [taskTab, setTaskTab] = useState<TaskTab>("assigned");
  const [badges, setBadges] = useState({ verify_total: 0, verify_need_action: false });
  const [users, setUsers] = useState<TaskUserDto[]>([]);
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
  const [pinPurpose, setPinPurpose] = useState<PinPurpose | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [adminPin, setAdminPin] = useState("");
  const [adminError, setAdminError] = useState("");
  const [isAdminBusy, setIsAdminBusy] = useState(false);
  const [preview, setPreview] = useState<TasksImportPreviewResponse | null>(null);
  const [importFileName, setImportFileName] = useState("");
  const [importResult, setImportResult] = useState<{
    created: number;
    updated: number;
    skipped: number;
    errors: Array<{ row: number; message: string }>;
  } | null>(null);

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

  const statusLabel = (status: TaskDto["status"]) => {
    if (status === "done") return "Выполнена";
    if (status === "done_pending_verify") return "На проверке";
    return "Активная";
  };

  const priorityLabel = (value: TaskDto["priority"] | "") => {
    if (value === "very_urgent") return "Очень срочно";
    if (value === "urgent") return "Срочно";
    if (value === "normal") return "Обычная";
    return "Не задано";
  };

  const priorityFire = (value: TaskDto["priority"]) => {
    if (value === "very_urgent") return "🔥🔥🔥";
    if (value === "urgent") return "🔥";
    if (value === "normal") return "";
    return "…";
  };

  const recurrenceTypeLabel = (value: "daily" | "weekly" | "monthly" | "yearly") => {
    if (value === "weekly") return "Еженедельно";
    if (value === "monthly") return "Ежемесячно";
    if (value === "yearly") return "Ежегодно";
    return "Ежедневно";
  };

  const canComplete = (task: TaskDto) => task.status === "active" && task.assignee_user_ids.includes(me);
  const canVerify = (task: TaskDto) => task.status === "done_pending_verify" && task.verifier_user_ids.includes(me);
  const canEdit = (task: TaskDto) => task.status === "active" && task.created_by_user_id === me;
  const canDelete = (task: TaskDto) => task.status === "active" && task.created_by_user_id === me;
  const canReturnActive = (task: TaskDto) =>
    task.status === "done" && (task.created_by_user_id === me || task.verifier_user_ids.includes(me));

  const visibleTasks = useMemo(() => {
    if (taskTab !== "created") return tasks;
    return tasks.filter((task) => !(task.assignee_user_ids.length === 1 && task.assignee_user_ids[0] === task.created_by_user_id));
  }, [tasks, taskTab]);

  const activeTasks = useMemo(() => {
    if (taskTab === "assigned") {
      return visibleTasks.filter((task) => !task.is_overdue && (task.status === "active" || task.status === "done_pending_verify"));
    }
    if (taskTab === "verify") {
      return visibleTasks.filter((task) => !task.is_overdue && (task.status === "active" || task.status === "done_pending_verify"));
    }
    return visibleTasks.filter((task) => !task.is_overdue && task.status === "active");
  }, [visibleTasks, taskTab]);

  const overdueTasks = useMemo(() => visibleTasks.filter((task) => task.is_overdue && task.status !== "done"), [visibleTasks]);
  const doneTasks = useMemo(() => visibleTasks.filter((task) => task.status === "done"), [visibleTasks]);

  const verifyTotalFromTasks = useMemo(() => {
    if (taskTab !== "verify") return badges.verify_total;
    return tasks.filter((task) => task.status !== "done").length;
  }, [taskTab, tasks, badges.verify_total]);

  const verifyNeedActionFromTasks = useMemo(() => {
    if (taskTab !== "verify") return badges.verify_need_action;
    return tasks.some((task) => task.status === "done_pending_verify");
  }, [taskTab, tasks, badges.verify_need_action]);

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
      setFormError("Для еженедельного повторения выберите хотя бы один день недели.");
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
    await Promise.all([loadTasks(), syncDetails(detailsTask.id), loadBadges()]);
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

  const toggleWeekday = (value: string) => {
    setRecurrenceDaysOfWeek((prev) =>
      prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value],
    );
  };

  const runTaskAction = async (action: () => Promise<unknown>, taskId?: string, closeDetails?: boolean) => {
    await action();
    await loadTasks();
    await loadBadges();
    if (closeDetails) {
      setDetailsTask(null);
      return;
    }
    if (taskId) {
      await syncDetails(taskId);
    }
  };

  const openAdminPinModal = (action: AdminActionType) => {
    setPinPurpose(action);
    setAdminPin("");
    setAdminError("");
  };

  const closePinModal = (clearPin = true) => {
    setPinPurpose(null);
    if (clearPin) {
      setAdminPin("");
    }
    setAdminError("");
    setIsAdminBusy(false);
  };

  const closeImportModal = () => {
    setImportOpen(false);
    setPreview(null);
    setImportResult(null);
    setImportFileName("");
    setAdminError("");
  };

  const downloadBlobFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const runAdminAction = async () => {
    if (!pinPurpose || !adminPin.trim()) {
      setAdminError("Введите PIN");
      return;
    }
    setAdminError("");
    setIsAdminBusy(true);
    try {
      if (pinPurpose === "template") {
        const blob = await downloadTasksTemplate(adminPin.trim());
        downloadBlobFile(blob, "tasks_template.xlsx");
        closePinModal();
        return;
      }
      if (pinPurpose === "export") {
        const blob = await exportTasksExcel(adminPin.trim());
        downloadBlobFile(blob, "tasks_export.xlsx");
        closePinModal();
        return;
      }
      setImportOpen(true);
      closePinModal(false);
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      if (message.includes("Invalid admin PIN")) {
        setAdminError("Неверный PIN");
      } else {
        setAdminError("Не удалось выполнить действие");
      }
      setIsAdminBusy(false);
    }
  };

  const onPickImportFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !adminPin.trim()) return;
    setImportFileName(file.name);
    setImportResult(null);
    setAdminError("");
    try {
      const data = await getTasksImportPreview(adminPin.trim(), file);
      setPreview(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      if (message.includes("Invalid admin PIN")) {
        setAdminError("Неверный PIN");
      } else {
        setAdminError("Не удалось получить предпросмотр");
      }
    }
  };

  const onPreviewCellChange = (rowNumber: number, key: string, value: string) => {
    setPreview((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        rows: prev.rows.map((row) => (row.row_number === rowNumber ? { ...row, values: { ...row.values, [key]: value } } : row)),
      };
    });
  };

  const submitImport = async () => {
    if (!preview) return;
    setIsAdminBusy(true);
    setAdminError("");
    try {
      const result = await importTasksExcel(adminPin.trim(), { rows: preview.rows as TasksImportPreviewRow[] });
      setImportResult(result);
      await Promise.all([loadTasks(), loadBadges()]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      setAdminError(message.includes("Invalid admin PIN") ? "Неверный PIN" : "Не удалось импортировать данные");
    } finally {
      setIsAdminBusy(false);
    }
  };

  const renderTaskList = (items: TaskDto[], emptyText: string) => (
    <ul className="tasks-list">
      {items.length === 0 ? <li className="muted">{emptyText}</li> : null}
      {items.map((task) => (
        <li
          key={task.id}
          className={`task-item ${task.is_overdue ? "overdue" : ""} ${task.status === "done" ? "done" : ""} ${task.status === "done_pending_verify" ? "pending-verify" : ""}`}
        >
          <div className="task-item-main">
            <strong>{task.title}</strong>
            <div className="muted">
              Дедлайн: {task.due_date ?? "без срока"}
              {task.due_time ? <span className="task-due-time">{task.due_time}</span> : null}
            </div>
            <div className="task-badges">
              <span className="task-badge">{statusLabel(task.status)}</span>
              <span className="task-badge">Срочность: {priorityLabel(task.priority)} {priorityFire(task.priority)}</span>
              {task.status === "done_pending_verify" ? <span className="task-badge task-badge-success">Можно проверить</span> : null}
              {task.is_overdue ? <span className="task-badge task-badge-danger">Просрочено</span> : null}
            </div>
            <button type="button" className="link-button" onClick={() => void openTaskDetails(task.id)}>Подробнее</button>
          </div>
          <div className="task-actions-inline">
            {canComplete(task) ? <button type="button" title="Выполнить" onClick={() => void runTaskAction(() => completeTask(token!, task.id), task.id)}>✔</button> : null}
            {canVerify(task) ? <button type="button" title="Проверить" onClick={() => void runTaskAction(() => verifyTask(token!, task.id), task.id)}>✅</button> : null}
            {canEdit(task) ? <button type="button" title="Редактировать" onClick={() => { setDetailsTask(task); openEdit(); }}>✏</button> : null}
            {canDelete(task) ? <button type="button" title="Удалить" onClick={() => void runTaskAction(() => deleteTask(token!, task.id), undefined, true)}>🗑</button> : null}
            {canReturnActive(task) ? <button type="button" title="Вернуть в active" onClick={() => void runTaskAction(() => returnActive(token!, task.id), task.id)}>↩</button> : null}
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
          <div className="task-datetime-row">
            <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
            <input type="time" value={dueTime} onChange={(event) => setDueTime(event.target.value)} />
          </div>
          <select value={priority} onChange={(event) => setPriority(event.target.value as typeof priority)}>
            <option value="normal">Обычная</option>
            <option value="urgent">Срочно</option>
            <option value="very_urgent">Очень срочно</option>
            <option value="">Не задано</option>
          </select>
          <label className="task-recurring-toggle">
            <input type="checkbox" checked={isRecurring} onChange={(event) => setIsRecurring(event.target.checked)} /> Повторяющаяся задача
          </label>
          {isRecurring ? (
            <div className="task-recurring-box">
              <select value={recurrenceType} onChange={(event) => setRecurrenceType(event.target.value as typeof recurrenceType)}>
                <option value="daily">Ежедневно</option>
                <option value="weekly">Еженедельно</option>
                <option value="monthly">Ежемесячно</option>
                <option value="yearly">Ежегодно</option>
              </select>
              <input
                type="number"
                min={1}
                value={recurrenceInterval}
                onChange={(event) => setRecurrenceInterval(event.target.value)}
                placeholder="Интервал"
              />
              {recurrenceType === "weekly" ? (
                <div className="task-weekdays-pills">
                  {weekDayOptions.map((item) => (
                    <label key={item.value}>
                      <input type="checkbox" checked={recurrenceDaysOfWeek.includes(item.value)} onChange={() => toggleWeekday(item.value)} /> {item.label}
                    </label>
                  ))}
                </div>
              ) : null}
              <input type="date" value={recurrenceEndDate} onChange={(event) => setRecurrenceEndDate(event.target.value)} />
            </div>
          ) : null}
          <div className="task-picker-columns">
            <div>
              <strong>Исполнители</strong>
              <div className="task-chips">{assigneeIds.map((id) => <span key={`a-${id}`} className="task-chip">{users.find((u) => u.id === id)?.username ?? id}</span>)}</div>
              <ul className="task-user-list">{users.map((item) => <li key={`a-${item.id}`}><label><input type="checkbox" checked={assigneeIds.includes(item.id)} onChange={() => togglePickerId(assigneeIds, setAssigneeIds, item.id)} /> {item.username}</label></li>)}</ul>
            </div>
            <div>
              <strong>Проверяющие</strong>
              <div className="task-chips">{verifierIds.map((id) => <span key={`v-${id}`} className="task-chip">{users.find((u) => u.id === id)?.username ?? id}</span>)}</div>
              <ul className="task-user-list">{users.map((item) => <li key={`v-${item.id}`}><label><input type="checkbox" checked={verifierIds.includes(item.id)} onChange={() => togglePickerId(verifierIds, setVerifierIds, item.id)} /> {item.username}</label></li>)}</ul>
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
      <div className="page-header tasks-page-header">
        <h2>Задачи</h2>
        <div className="tasks-admin-actions">
          <button type="button" className="secondary-button" onClick={() => openAdminPinModal("template")}>Скачать шаблон</button>
          <button type="button" className="secondary-button" onClick={() => openAdminPinModal("export")}>Экспорт</button>
          <button type="button" className="secondary-button" onClick={() => openAdminPinModal("import")}>Импорт</button>
        </div>
      </div>
      <div className="admin-tabs">
        {(["assigned", "verify", "created"] as TaskTab[]).map((tab) => (
          <button key={tab} type="button" className={taskTab === tab ? "primary-button" : "secondary-button"} onClick={() => setTaskTab(tab)}>
            {tabLabel(tab)}
            {tab === "verify" ? <span className="tasks-tab-badge">{verifyTotalFromTasks}{verifyNeedActionFromTasks ? " ❗" : ""}</span> : null}
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
            <p>Срок: {detailsTask.due_date || "—"} {detailsTask.due_time ? <span className="task-due-time">{detailsTask.due_time}</span> : null}</p>
            <p>Срочность: {priorityLabel(detailsTask.priority)} {priorityFire(detailsTask.priority)}</p>
            <p>Повторение: {detailsTask.is_recurring ? `${recurrenceTypeLabel(detailsTask.recurrence_type ?? "daily")} / ${detailsTask.recurrence_interval ?? 1}` : "нет"}</p>
            <p>Статус: {statusLabel(detailsTask.status)}</p>
            <div className="task-actions">
              {canEdit(detailsTask) ? <button type="button" className="secondary-button" onClick={openEdit}>Редактировать</button> : null}
              {canComplete(detailsTask) ? <button type="button" className="secondary-button" onClick={() => void runTaskAction(() => completeTask(token!, detailsTask.id), detailsTask.id)}>Выполнить</button> : null}
              {canVerify(detailsTask) ? <button type="button" className="secondary-button" onClick={() => void runTaskAction(() => verifyTask(token!, detailsTask.id), detailsTask.id)}>Проверить</button> : null}
              {canReturnActive(detailsTask) ? <button type="button" className="ghost-button" onClick={() => void runTaskAction(() => returnActive(token!, detailsTask.id), detailsTask.id)}>Вернуть в active</button> : null}
              {canDelete(detailsTask) ? <button type="button" className="ghost-button" onClick={() => void runTaskAction(() => deleteTask(token!, detailsTask.id), undefined, true)}>Удалить</button> : null}
              {detailsTask.is_recurring && !detailsTask.recurrence_master_task_id && (user?.id === detailsTask.created_by_user_id) ? <button type="button" className="ghost-button" onClick={() => void deleteRecurringChildren(token!, detailsTask.id, "all").then(async () => { await loadTasks(); await syncDetails(detailsTask.id); })}>Удалить children</button> : null}
            </div>
            <div className="admin-modal-actions"><button type="button" className="ghost-button" onClick={() => setDetailsTask(null)}>Закрыть</button></div>
          </div>
        </div>
      ) : null}

      {pinPurpose ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal tasks-admin-pin-modal">
            <h3>
              {pinPurpose === "template" ? "Скачать шаблон" : pinPurpose === "export" ? "Экспорт задач" : "Импорт задач"}
            </h3>
            <p className="muted">Введите PIN администратора для продолжения.</p>
            <input
              type="password"
              value={adminPin}
              onChange={(event) => setAdminPin(event.target.value)}
              placeholder="PIN"
              autoFocus
            />
            {adminError ? <p className="form-error">{adminError}</p> : null}

            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" onClick={() => closePinModal()}>Отмена</button>
              <button type="button" className="primary-button" onClick={() => void runAdminAction()} disabled={isAdminBusy}>
                {isAdminBusy ? "Выполняется..." : "Продолжить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {importOpen ? (
        <div className="admin-modal-backdrop">
          <div className="admin-modal tasks-admin-modal">
            <h3>Импорт задач из Excel</h3>
            <div className="tasks-import-help">
              <h4>Инструкция</h4>
              <ul>
                <li>Шаблон — это готовый Excel-файл с нужными колонками и примером заполнения.</li>
                <li>Экспорт выгружает все задачи, чтобы посмотреть структуру и при необходимости отредактировать её.</li>
                <li>Импорт загружает задачи в систему: новые строки создаются, строки с существующим ID обновляются.</li>
                <li>Перед импортом лучше скачать шаблон или экспорт и сверить структуру данных.</li>
                <li>Обязательные поля в таблице помечены звёздочкой и выделены жирным.</li>
                <li><strong>creator_id</strong> обязателен, пользователи указываются по ID.</li>
                <li>Если ID исполнителей пустой — исполнитель назначается как создатель.</li>
                <li>Если ID проверяющих пустой — проверка не требуется.</li>
                <li>Статус <code>done</code> требует заполненного поля даты/времени завершения.</li>
                <li>Статус <code>done_pending_verify</code> импортировать нельзя.</li>
                <li>Повторяющиеся задачи импортируются только как master, дочерние создаются автоматически.</li>
                <li>Импорт построчный: ошибка в одной строке не блокирует остальные.</li>
                <li>Перед подтверждением вы можете проверить и исправить данные прямо в таблице ниже.</li>
              </ul>
            </div>
            <div className="tasks-import-controls">
              <input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => void onPickImportFile(event)} />
              {importFileName ? <p className="muted">Файл: {importFileName}</p> : null}
            </div>
            {preview ? (
              <>
                <p className="muted">Всего строк: {preview.total_rows}. Валидных: {preview.valid_rows}. С ошибками: {preview.invalid_rows}.</p>
                <div className="tasks-preview-table-wrap">
                  <table className="tasks-preview-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        {preview.columns.map((col) => <th key={col.key}>{col.label}</th>)}
                        <th>Действие</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.rows.map((row) => (
                        <tr key={row.row_number} className={row.errors.length ? "row-invalid" : ""}>
                          <td>{row.row_number}</td>
                          {preview.columns.map((col) => (
                            <td key={`${row.row_number}-${col.key}`}>
                              <input
                                className={col.required ? "required-cell" : ""}
                                value={row.values[col.key] ?? ""}
                                onChange={(event) => onPreviewCellChange(row.row_number, col.key, event.target.value)}
                              />
                            </td>
                          ))}
                          <td>{row.values._import_action === "update" ? "Обновление" : "Создание"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="tasks-import-result">
                  {preview.row_errors.map((item) => (
                    <p key={`e-${item.row}`} className="form-error">Строка {item.row}: {item.errors.join("; ")}</p>
                  ))}
                </div>
              </>
            ) : null}
            {importResult ? (
              <div className="tasks-import-result">
                <p>Создано: {importResult.created}, Обновлено: {importResult.updated}, Пропущено: {importResult.skipped}</p>
                {importResult.errors.map((item) => <p key={`${item.row}-${item.message}`} className="form-error">Строка {item.row}: {item.message}</p>)}
              </div>
            ) : null}
            {adminError ? <p className="form-error">{adminError}</p> : null}
            <div className="admin-modal-actions">
              <button type="button" className="ghost-button" onClick={closeImportModal}>Закрыть</button>
              <button type="button" className="primary-button" disabled={!preview || isAdminBusy} onClick={() => void submitImport()}>
                {isAdminBusy ? "Импорт..." : "Подтвердить импорт"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default TasksModule;
