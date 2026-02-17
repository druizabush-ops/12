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
  assignee_user_ids: number[];
  is_overdue: boolean;
  needs_attention_for_verifier: boolean;
  is_recurring: boolean;
  recurrence_type: "daily" | "weekly" | "monthly" | "yearly" | null;
  recurrence_interval: number | null;
  recurrence_days_of_week: number[] | null;
  recurrence_end_date: string | null;
  recurrence_master_task_id: string | null;
  recurrence_state: "active" | "paused" | "stopped" | null;
  is_hidden: boolean;
};

export type TaskFolderDto = {
  id: string;
  name: string;
  created_by_user_id: number;
  filter_json: Record<string, unknown>;
  created_at: string;
};

export type TaskCalendarDay = {
  date: string;
  count: number;
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
  is_recurring?: boolean;
  recurrence_type?: "daily" | "weekly" | "monthly" | "yearly" | null;
  recurrence_interval?: number | null;
  recurrence_days_of_week?: number[] | null;
  recurrence_end_date?: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  status?: "new" | "in_progress" | "waiting" | "done" | "canceled";
  apply_scope?: "single" | "future" | "master";
};

export const getCalendar = (token: string, from: string, to: string) =>
  apiFetch<TaskCalendarDay[]>(`/tasks/calendar?from=${from}&to=${to}`, { method: "GET" }, token);

export const getTasksByDate = (token: string, date: string, options?: { folderId?: string }) => {
  const query = new URLSearchParams({ date });
  if (options?.folderId) query.set("folder_id", options.folderId);
  return apiFetch<TaskDto[]>(`/tasks?${query.toString()}`, { method: "GET" }, token);
};

export const createTask = (token: string, payload: CreateTaskPayload) =>
  apiFetch<TaskDto>("/tasks", { method: "POST", body: JSON.stringify(payload) }, token);

export const updateTask = (token: string, id: string, payload: UpdateTaskPayload) =>
  apiFetch<TaskDto>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);

export const completeTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/complete`, { method: "POST" }, token);

export const verifyTask = (token: string, id: string) =>
  apiFetch<TaskDto>(`/tasks/${id}/verify`, { method: "POST" }, token);

export const getFolders = (token: string) => apiFetch<TaskFolderDto[]>("/tasks/folders", { method: "GET" }, token);
export const createFolder = (token: string, payload: { name: string; filter_json?: Record<string, unknown> }) =>
  apiFetch<TaskFolderDto>("/tasks/folders", { method: "POST", body: JSON.stringify(payload) }, token);
export const updateFolder = (token: string, id: string, payload: { name?: string; filter_json?: Record<string, unknown> }) =>
  apiFetch<TaskFolderDto>(`/tasks/folders/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);
export const deleteFolder = (token: string, id: string) =>
  apiFetch<void>(`/tasks/folders/${id}`, { method: "DELETE" }, token);
export const recurrenceAction = (token: string, taskId: string, action: "pause" | "resume" | "stop") =>
  apiFetch<TaskDto>(`/tasks/${taskId}/recurrence-action`, { method: "POST", body: JSON.stringify({ action }) }, token);
export const getAttentionTasks = (token: string) => apiFetch<TaskDto[]>("/tasks/attention", { method: "GET" }, token);
