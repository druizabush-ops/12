import { apiFetch } from "./client";

export type TaskDto = {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  due_time: string | null;
  status: "active" | "done_pending_verify" | "done";
  priority: "normal" | "urgent" | "very_urgent" | null;
  verifier_user_ids: number[];
  created_by_user_id: number;
  created_at: string;
  completed_at: string | null;
  verified_at: string | null;
  source_type: string | null;
  source_id: string | null;
  assignee_user_ids: number[];
  is_overdue: boolean;
  is_recurring: boolean;
  recurrence_type: "daily" | "weekly" | "monthly" | "yearly" | null;
  recurrence_interval: number | null;
  recurrence_days_of_week: string | null;
  recurrence_end_date: string | null;
  recurrence_master_task_id: string | null;
  recurrence_state: "active" | "paused" | "stopped";
  is_hidden: boolean;
};

export type TaskCalendarDay = {
  date: string;
  count: number;
};

export type TaskBadgeDto = {
  pending_verify_count: number;
  fresh_completed_flag: boolean;
};

export type TaskUserDto = {
  id: number;
  username: string;
};

export type CreateTaskPayload = {
  title: string;
  description?: string | null;
  due_date?: string | null;
  due_time?: string | null;
  priority?: "normal" | "urgent" | "very_urgent" | null;
  verifier_user_ids?: number[];
  assignee_user_ids?: number[];
  source_type?: string | null;
  source_id?: string | null;
  is_recurring?: boolean;
  recurrence_type?: "daily" | "weekly" | "monthly" | "yearly" | null;
  recurrence_interval?: number | null;
  recurrence_days_of_week?: string | null;
  recurrence_end_date?: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  status?: "active" | "done_pending_verify" | "done";
};

export const getUsers = (token: string) => apiFetch<TaskUserDto[]>("/tasks/users", { method: "GET" }, token);

export const getBadges = (token: string) => apiFetch<TaskBadgeDto>("/tasks/badges", { method: "GET" }, token);

export const getCalendar = (token: string, from: string, to: string, tab: "assigned" | "verify" | "created") =>
  apiFetch<TaskCalendarDay[]>(`/tasks/calendar?from=${from}&to=${to}&tab=${tab}`, { method: "GET" }, token);

export const getTasksByDate = (token: string, date: string, tab: "assigned" | "verify" | "created") =>
  apiFetch<TaskDto[]>(`/tasks?date=${date}&tab=${tab}`, { method: "GET" }, token);

export const createTask = (token: string, payload: CreateTaskPayload) =>
  apiFetch<TaskDto>("/tasks", { method: "POST", body: JSON.stringify(payload) }, token);

export const completeTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/complete`, { method: "POST" }, token);

export const verifyTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/verify`, { method: "POST" }, token);

export const returnActive = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/return-active`, { method: "POST" }, token);

export const deleteTask = (token: string, id: string) => apiFetch<void>(`/tasks/${id}`, { method: "DELETE" }, token);

export const updateTask = (token: string, id: string, payload: UpdateTaskPayload) =>
  apiFetch<TaskDto>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);

export const recurrenceAction = (token: string, id: string, action: "pause" | "resume" | "stop") =>
  apiFetch<TaskDto>(`/tasks/${id}/recurrence-action`, { method: "POST", body: JSON.stringify({ action }) }, token);

export const deleteRecurringChildren = (
  token: string,
  id: string,
  mode: "all" | "before" | "after",
  date?: string,
) => apiFetch<{ deleted: number }>(`/tasks/${id}/recurrence-children?mode=${mode}${date ? `&date=${date}` : ""}`, { method: "DELETE" }, token);

export const getTaskById = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}`, { method: "GET" }, token);
