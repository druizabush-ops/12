import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  AuthUser,
  TaskDto,
  TaskFolder,
  completeTask,
  createFolder,
  createTask,
  deleteFolder,
  getAttentionTasks,
  getAuthUsers,
  getCalendar,
  getFolders,
  getTasksByDate,
  patchFolder,
  recurrenceAction,
  verifyTask,
} from "../../api/tasks";
import { useAuth } from "../../contexts/AuthContext";
import { ModuleRuntimeProps } from "../../types/module";

const pad = (v: number) => String(v).padStart(2, "0");
const formatDateKey = (y: number, m: number, d: number) => `${y}-${pad(m)}-${pad(d)}`;
const todayKey = () => {
  const now = new Date();
  return formatDateKey(now.getFullYear(), now.getMonth() + 1, now.getDate());
};
const parseDateKey = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return { year, month, day };
};
const TasksModule = (_: ModuleRuntimeProps) => {
  const { token, user } = useAuth();
  const [selectedDate, setSelectedDate] = useState(() => todayKey());
  const [monthCursor, setMonthCursor] = useState(() => {
    const t = parseDateKey(todayKey());
    return { year: t.year, month: t.month };
  });
  const [calendarCounts, setCalendarCounts] = useState<Record<string, { active: number; done: number }>>({});
  const [tasks, setTasks] = useState<TaskDto[]>([]);
  const [attentionTasks, setAttentionTasks] = useState<TaskDto[]>([]);
  const [folders, setFolders] = useState<TaskFolder[]>([]);
  const [activeFolderId, setActiveFolderId] = useState<string | undefined>(undefined);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [toast, setToast] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isFolderSettingsOpen, setIsFolderSettingsOpen] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(selectedDate);
  const [assigneeId, setAssigneeId] = useState<number | "">("");
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrenceType, setRecurrenceType] = useState<"daily" | "weekly" | "monthly" | "yearly">("daily");
  const [recurrenceInterval, setRecurrenceInterval] = useState(1);
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [recurrenceDaysOfWeek, setRecurrenceDaysOfWeek] = useState<number[]>([]);

  const weekdayLabels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  const calendarCells = useMemo(() => {
    const firstOfMonth = new Date(monthCursor.year, monthCursor.month - 1, 1);
    const firstDayWeekIndex = (firstOfMonth.getDay() + 6) % 7;
    const daysInMonth = new Date(monthCursor.year, monthCursor.month, 0).getDate();
    const cells: Array<{ key: string; day: number; col: number } | null> = [];
    for (let i = 0; i < firstDayWeekIndex; i += 1) cells.push(null);
    for (let day = 1; day <= daysInMonth; day += 1) {
      const idx = firstDayWeekIndex + day - 1;
      cells.push({ key: formatDateKey(monthCursor.year, monthCursor.month, day), day, col: idx % 7 });
    }
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [monthCursor]);

  const loadCalendar = async () => {
    if (!token) return;
    const from = formatDateKey(monthCursor.year, monthCursor.month, 1);
    const to = formatDateKey(monthCursor.year, monthCursor.month, new Date(monthCursor.year, monthCursor.month, 0).getDate());
    const data = await getCalendar(token, from, to);
    setCalendarCounts(Object.fromEntries(data.map((item) => [item.date, { active: item.count_active, done: item.count_done }])));
  };

  const loadTasks = async () => {
    if (!token) return;
    const [dayTasks, attention] = await Promise.all([getTasksByDate(token, selectedDate, activeFolderId), getAttentionTasks(token)]);
    setTasks(dayTasks);
    setAttentionTasks(attention);
  };

  useEffect(() => {
    if (!token) return;
    void Promise.all([getFolders(token).then(setFolders), getAuthUsers(token).then(setUsers)]);
  }, [token]);

  useEffect(() => {
    void loadCalendar();
  }, [token, monthCursor]);

  useEffect(() => {
    setDueDate(selectedDate);
    void loadTasks();
  }, [token, selectedDate, activeFolderId]);

  const onCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !title.trim()) return;
    const assignee = assigneeId || user?.id;
    await createTask(token, {
      title: title.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      assignee_user_ids: assignee ? [assignee] : [],
      folder_id: activeFolderId,
      is_recurring: isRecurring,
      recurrence_type: isRecurring ? recurrenceType : undefined,
      recurrence_interval: isRecurring ? recurrenceInterval : undefined,
      recurrence_days_of_week: isRecurring ? recurrenceDaysOfWeek : undefined,
      recurrence_end_date: isRecurring && recurrenceEndDate ? recurrenceEndDate : undefined,
    });
    setTitle("");
    setDescription("");
    setRecurrenceEndDate("");
    setIsCreateOpen(false);
    await Promise.all([loadTasks(), loadCalendar()]);
  };

  const onToday = async () => {
    const now = todayKey();
    const parsed = parseDateKey(now);
    setMonthCursor({ year: parsed.year, month: parsed.month });
    setSelectedDate(now);
    await Promise.all([loadCalendar(), loadTasks()]);
  };

  const activeTasks = tasks.filter((task) => task.status !== "done" && task.due_date === selectedDate && !task.is_hidden);
  const overdueTasks = tasks.filter((task) => task.status !== "done" && task.due_date && task.due_date < todayKey() && !task.is_hidden);
  const doneTasks = tasks.filter((task) => task.status === "done");
  const activeFolder = folders.find((item) => item.id === activeFolderId);

  return (
    <div className="page tasks-page">
      <div className="page-header"><h2>Задачи</h2></div>
      {toast ? <div className="task-toast">{toast}</div> : null}
      <div className="task-tabs-wrap">
        <div className="task-tabs-scroll">
          <button type="button" className={!activeFolderId ? "task-tab active" : "task-tab"} onClick={() => setActiveFolderId(undefined)}>Все</button>
          {folders.map((folder) => <button key={folder.id} type="button" className={activeFolderId === folder.id ? "task-tab active" : "task-tab"} onClick={() => setActiveFolderId(folder.id)}>{folder.title}</button>)}
        </div>
        <button type="button" className="secondary-button" onClick={async () => { if (!token) return; const folder = await createFolder(token, `Папка ${folders.length + 1}`); setFolders((prev) => [...prev, folder]); setActiveFolderId(folder.id); }}>+ Папка</button>
      </div>
      <div className="tasks-layout">
        <section className="page-card tasks-calendar">
          <div className="tasks-calendar-header">
            <button className="ghost-button" type="button" onClick={() => setMonthCursor((prev) => ({ year: prev.month === 1 ? prev.year - 1 : prev.year, month: prev.month === 1 ? 12 : prev.month - 1 }))}>←</button>
            <strong>{new Date(monthCursor.year, monthCursor.month - 1, 1).toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}</strong>
            <button className="ghost-button" type="button" onClick={() => setMonthCursor((prev) => ({ year: prev.month === 12 ? prev.year + 1 : prev.year, month: prev.month === 12 ? 1 : prev.month + 1 }))}>→</button>
          </div>
          <button className="secondary-button" type="button" onClick={onToday}>Сегодня</button>
          <div className="tasks-calendar-grid weekday-row">{weekdayLabels.map((label, idx) => <div key={label} className={idx >= 5 ? "weekday weekend" : "weekday"}>{label}</div>)}</div>
          <div className="tasks-calendar-grid">
            {calendarCells.map((cell, index) => {
              if (!cell) return <div key={`empty-${index}`} className="tasks-day-empty" />;
              const count = calendarCounts[cell.key] ?? { active: 0, done: 0 };
              return <button key={cell.key} type="button" className={`${cell.key === selectedDate ? "tasks-day active" : "tasks-day"} ${cell.col >= 5 ? "weekend" : ""}`} onClick={() => setSelectedDate(cell.key)}><span>{cell.day}</span><small>{count.active}</small>{count.done > 0 ? <i className="done-dot" /> : null}</button>;
            })}
          </div>
        </section>

        <section className="page-card tasks-list-wrap">
          <div className="tasks-list-header"><h3>{selectedDate}</h3><div><button className="ghost-button" type="button" onClick={() => setIsFolderSettingsOpen(true)}>⚙</button><button className="primary-button" type="button" onClick={() => setIsCreateOpen(true)}>Новая задача</button></div></div>

          <h4>Актуальные</h4><ul className="tasks-list">{activeTasks.map((task) => <li key={task.id} className="task-item"><strong>{task.title}</strong><button type="button" className="secondary-button" onClick={async () => { if (!token) return; await completeTask(token, task.id); await loadTasks(); }}>Выполнить</button></li>)}</ul>
          <h4>Просроченные</h4><ul className="tasks-list">{overdueTasks.map((task) => <li key={task.id} className="task-item overdue"><strong>{task.title}</strong><button type="button" className="secondary-button" onClick={async () => { if (!token) return; await completeTask(token, task.id); await loadTasks(); }}>Выполнить</button></li>)}</ul>
          <h4>Выполненные</h4><ul className="tasks-list">{doneTasks.map((task) => <li key={task.id} className="task-item"><strong>{task.title}</strong></li>)}</ul>

          <div className="tasks-attention"><h4>На проверку</h4><ul>{attentionTasks.map((task) => <li key={task.id}><button className="ghost-button" type="button" onClick={async () => { if (!token) return; await verifyTask(token, task.id); await loadTasks(); }}>{task.title}</button></li>)}</ul></div>
        </section>
      </div>

      {isCreateOpen ? <div className="admin-modal-backdrop"><form className="admin-modal" onSubmit={onCreateTask}><h3 className="task-form-title">Новая задача</h3><div className="admin-column"><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название" required /><textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание" /><input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} /><select value={assigneeId} onChange={(event) => setAssigneeId(event.target.value ? Number(event.target.value) : "")}><option value="">Текущий пользователь</option>{users.map((item) => <option key={item.id} value={item.id}>{item.username}</option>)}</select><label><input type="checkbox" checked={isRecurring} onChange={(e) => setIsRecurring(e.target.checked)} /> Повторять</label>{isRecurring ? <div className="recurring-block"><select value={recurrenceType} onChange={(e) => setRecurrenceType(e.target.value as typeof recurrenceType)}><option value="daily">daily</option><option value="weekly">weekly</option><option value="monthly">monthly</option><option value="yearly">yearly</option></select><input type="number" min={1} value={recurrenceInterval} onChange={(e) => setRecurrenceInterval(Number(e.target.value) || 1)} /><input type="date" value={recurrenceEndDate} onChange={(e) => setRecurrenceEndDate(e.target.value)} />{recurrenceType === "weekly" ? <div className="weekday-picks">{weekdayLabels.map((d, idx) => <label key={d}><input type="checkbox" checked={recurrenceDaysOfWeek.includes(idx)} onChange={(e) => setRecurrenceDaysOfWeek((prev) => e.target.checked ? [...prev, idx] : prev.filter((v) => v !== idx))} />{d}</label>)}</div> : null}</div> : null}</div><div className="admin-modal-actions"><button type="button" className="ghost-button" onClick={() => setIsCreateOpen(false)}>Отмена</button><button type="submit" className="primary-button">Создать</button></div></form></div> : null}

      {isFolderSettingsOpen && activeFolder ? <div className="admin-modal-backdrop"><div className="admin-modal"><h3>Папка: {activeFolder.title}</h3><div className="admin-column"><input value={activeFolder.title} onChange={async (e) => { if (!token) return; const patched = await patchFolder(token, activeFolder.id, { title: e.target.value }); setFolders((prev) => prev.map((f) => f.id === patched.id ? patched : f)); }} /><label><input type="checkbox" checked={activeFolder.show_active} onChange={async (e) => { if (!token) return; const patched = await patchFolder(token, activeFolder.id, { show_active: e.target.checked }); setFolders((prev) => prev.map((f) => f.id === patched.id ? patched : f)); }} /> Актуальные</label><label><input type="checkbox" checked={activeFolder.show_overdue} onChange={async (e) => { if (!token) return; const patched = await patchFolder(token, activeFolder.id, { show_overdue: e.target.checked }); setFolders((prev) => prev.map((f) => f.id === patched.id ? patched : f)); }} /> Просроченные</label><label><input type="checkbox" checked={activeFolder.show_done} onChange={async (e) => { if (!token) return; const patched = await patchFolder(token, activeFolder.id, { show_done: e.target.checked }); setFolders((prev) => prev.map((f) => f.id === patched.id ? patched : f)); }} /> Выполненные</label><button className="ghost-button" type="button" onClick={async () => { if (!token) return; await deleteFolder(token, activeFolder.id); setFolders((prev) => prev.filter((f) => f.id !== activeFolder.id)); setActiveFolderId(undefined); setIsFolderSettingsOpen(false); }}>Удалить папку</button></div><div className="admin-modal-actions"><button className="primary-button" type="button" onClick={() => setIsFolderSettingsOpen(false)}>Закрыть</button></div></div></div> : null}

      <div className="task-rec-actions"><button type="button" className="ghost-button" onClick={async () => { if (!token || !tasks[0]) return; await recurrenceAction(token, tasks[0].id, "pause"); setToast("Повторение поставлено на паузу"); await loadTasks(); }}>Pause</button><button type="button" className="ghost-button" onClick={async () => { if (!token || !tasks[0]) return; await recurrenceAction(token, tasks[0].id, "resume"); setToast("Повторение возобновлено"); await loadTasks(); }}>Resume</button><button type="button" className="ghost-button" onClick={async () => { if (!token || !tasks[0]) return; await recurrenceAction(token, tasks[0].id, "stop"); setToast("Повторение остановлено"); await loadTasks(); }}>Stop</button></div>
    </div>
  );
};

export default TasksModule;
