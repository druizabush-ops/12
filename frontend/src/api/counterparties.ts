import { apiFetch } from "./client";

export type CounterpartyFolderDto = {
  id: number;
  parent_id: number | null;
  name: string;
  sort_order: number | null;
};

export type CounterpartyDto = {
  id: number;
  folder_id: number | null;
  group_id: number | null;
  is_archived: boolean;
  status: "active" | "inactive" | "archived";
  sort_order: number | null;
  name: string;
  legal_name: string | null;
  city: string | null;
  product_group: string | null;
  department: string | null;
  website: string | null;
  login: string | null;
  password: string | null;
  messenger: string | null;
  phone: string | null;
  email: string | null;
  order_day_of_week: number | null;
  order_deadline_time: string | null;
  delivery_day_of_week: number | null;
  defect_notes: string | null;
  inn: string | null;
  kpp: string | null;
  ogrn: string | null;
  legal_address: string | null;
  bank_name: string | null;
  bank_bik: string | null;
  account: string | null;
  corr_account: string | null;
};

export type RuleDto = {
  id: number;
  counterparty_id: number;
  is_enabled: boolean;
  title: string;
  kind: "order_request" | "custom";
  schedule: {
    recurrence_type: "daily" | "weekly" | "monthly" | "yearly";
    recurrence_interval: number;
    recurrence_days_of_week: number[];
    recurrence_end_date: string;
  };
  primary_task: { assignee_user_id: number; text: string; due_time: string | null };
  review_task: { enabled: boolean; assignee_user_id: number | null; text: string | null; due_time: string | null };
  binding: { primary_master_task_id: string; review_master_task_id: string | null } | null;
};

export const getCounterpartyFolders = (token: string) => apiFetch<CounterpartyFolderDto[]>("/counterparties/folders", { method: "GET" }, token);
export const createCounterpartyFolder = (token: string, payload: Partial<CounterpartyFolderDto>) =>
  apiFetch<CounterpartyFolderDto>("/counterparties/folders", { method: "POST", body: JSON.stringify(payload) }, token);
export const updateCounterpartyFolder = (token: string, id: number, payload: Partial<CounterpartyFolderDto>) =>
  apiFetch<CounterpartyFolderDto>(`/counterparties/folders/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);
export const getCounterparties = (token: string, includeArchived = false) =>
  apiFetch<CounterpartyDto[]>(`/counterparties?include_archived=${includeArchived}`, { method: "GET" }, token);
export const createCounterparty = (token: string, payload: Partial<CounterpartyDto>) =>
  apiFetch<CounterpartyDto>("/counterparties", { method: "POST", body: JSON.stringify(payload) }, token);
export const updateCounterparty = (token: string, id: number, payload: Partial<CounterpartyDto>) =>
  apiFetch<CounterpartyDto>(`/counterparties/${id}`, { method: "PUT", body: JSON.stringify(payload) }, token);
export const archiveCounterparty = (token: string, id: number) => apiFetch<CounterpartyDto>(`/counterparties/${id}/archive`, { method: "POST" }, token);
export const restoreCounterparty = (token: string, id: number) => apiFetch<CounterpartyDto>(`/counterparties/${id}/restore`, { method: "POST" }, token);

export const getAutoTaskRules = (token: string, counterpartyId: number) =>
  apiFetch<RuleDto[]>(`/counterparties/${counterpartyId}/auto-task-rules`, { method: "GET" }, token);
export const createAutoTaskRule = (token: string, counterpartyId: number, payload: unknown) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-task-rules`, { method: "POST", body: JSON.stringify(payload) }, token);
export const updateAutoTaskRule = (token: string, counterpartyId: number, ruleId: number, payload: unknown) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-task-rules/${ruleId}`, { method: "PUT", body: JSON.stringify(payload) }, token);
