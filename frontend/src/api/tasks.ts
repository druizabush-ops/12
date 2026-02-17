import { apiFetch } from "./client";

export type TaskDto = {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  due_time: string | null;
  due_at: string | null;
  status: "new" | "in_progress" | "waiting" | "done" | "canceled";
  urgency: "normal" | "urgent" | "very_urgent";
  requires_verification: boolean;
  verifier_user_id: number | null;
  created_by_user_id: number;
  created_at: string;
  completed_at: string | null;
  verified_at: string | null;
  source_type: string | null;
  source_id: string | null;
  folder_id: string | null;
  is_recurring: boolean;
  recurrence_type: "daily" | "weekly" | "monthly" | "yearly" | null;
  recurrence_interval: number | null;
  recurrence_days_of_week: number[];
  recurrence_end_date: string | null;
  recurrence_master_task_id: string | null;
  recurrence_state: "active" | "paused" | "stopped";
  is_hidden: boolean;
  assignee_user_ids: number[];
  is_overdue: boolean;
  needs_attention_for_verifier: boolean;
};

export type TaskFolder = {
  id: string;
  title: string;
  created_by_user_id: number;
  show_active: boolean;
  show_overdue: boolean;
  show_done: boolean;
};

export type TaskCalendarDay = {
  date: string;
  count_active: number;
  count_done: number;
};

export type AuthUser = {
  id: number;
  username: string;
};

export type CreateTaskPayload = {
  title: string;
  description?: string | null;
  due_date?: string | null;
  due_time?: string | null;
  urgency?: "normal" | "urgent" | "very_urgent";
  requires_verification?: boolean;
  verifier_user_id?: number | null;
  assignee_user_ids?: number[];
  source_type?: string | null;
  source_id?: string | null;
  folder_id?: string | null;
  is_recurring?: boolean;
  recurrence_type?: "daily" | "weekly" | "monthly" | "yearly";
  recurrence_interval?: number;
  recurrence_days_of_week?: number[];
  recurrence_end_date?: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  status?: "new" | "in_progress" | "waiting" | "done" | "canceled";
};

export const getCalendar = (token: string, from: string, to: string) =>
  apiFetch<TaskCalendarDay[]>(`/tasks/calendar?from=${from}&to=${to}`, { method: "GET" }, token);

export const getTasksByDate = (token: string, date: string, folderId?: string) =>
  apiFetch<TaskDto[]>(`/tasks?date=${date}${folderId ? `&folder_id=${folderId}` : ""}`, { method: "GET" }, token);

export const createTask = (token: string, payload: CreateTaskPayload) =>
  apiFetch<TaskDto>("/tasks", { method: "POST", body: JSON.stringify(payload) }, token);

export const completeTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/complete`, { method: "POST" }, token);

export const verifyTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/verify`, { method: "POST" }, token);

export const updateTask = (token: string, id: string, payload: UpdateTaskPayload) =>
  apiFetch<TaskDto>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);

export const recurrenceAction = (token: string, id: string, action: "pause" | "resume" | "stop") =>
  apiFetch<TaskDto>(`/tasks/${id}/recurrence-action`, { method: "POST", body: JSON.stringify({ action }) }, token);

export const getAttentionTasks = (token: string) =>
  apiFetch<TaskDto[]>("/tasks/attention", { method: "GET" }, token);

export const getFolders = (token: string) => apiFetch<TaskFolder[]>("/tasks/folders", { method: "GET" }, token);

export const createFolder = (token: string, title: string) =>
  apiFetch<TaskFolder>("/tasks/folders", { method: "POST", body: JSON.stringify({ title }) }, token);

export const patchFolder = (token: string, id: string, payload: Partial<Omit<TaskFolder, "id" | "created_by_user_id">>) =>
  apiFetch<TaskFolder>(`/tasks/folders/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);

export const deleteFolder = (token: string, id: string) => apiFetch<void>(`/tasks/folders/${id}`, { method: "DELETE" }, token);

export const getAuthUsers = (token: string) => apiFetch<AuthUser[]>("/auth/users", { method: "GET" }, token);
