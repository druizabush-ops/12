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
  task_kind: "MAKE_ORDER" | "SEND_ORDER";
  title_template: string;
  description_template: string | null;
  assignee_user_ids: number[];
  verifier_user_ids: number[] | null;
  is_enabled: boolean;
  schedule_weekday: number;
  schedule_due_time: string | null;
  horizon_days: number;
  linked_task_master_id: string | null;
  state: "active" | "paused" | "stopped";
};

export type CounterpartySettingsDto = { task_creator_user_id: number | null };

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

export const getCounterpartySettings = (token: string) => apiFetch<CounterpartySettingsDto>("/counterparties/settings", { method: "GET" }, token);
export const updateCounterpartySettings = (token: string, payload: CounterpartySettingsDto) =>
  apiFetch<CounterpartySettingsDto>("/counterparties/settings", { method: "PATCH", body: JSON.stringify(payload) }, token);

export const getAutoTaskRules = (token: string, counterpartyId: number) =>
  apiFetch<RuleDto[]>(`/counterparties/${counterpartyId}/auto-tasks`, { method: "GET" }, token);
export const createAutoTaskRule = (token: string, counterpartyId: number, payload: unknown) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-tasks`, { method: "POST", body: JSON.stringify(payload) }, token);
export const updateAutoTaskRule = (token: string, counterpartyId: number, ruleId: number, payload: unknown, action?: "keep" | "replace") =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-tasks/${ruleId}${action ? `?action=${action}` : ""}`, { method: "PATCH", body: JSON.stringify(payload) }, token);
export const pauseAutoTaskRule = (token: string, counterpartyId: number, ruleId: number) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-tasks/${ruleId}/pause`, { method: "POST" }, token);
export const resumeAutoTaskRule = (token: string, counterpartyId: number, ruleId: number) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-tasks/${ruleId}/resume`, { method: "POST" }, token);
export const stopAutoTaskRule = (token: string, counterpartyId: number, ruleId: number) =>
  apiFetch<RuleDto>(`/counterparties/${counterpartyId}/auto-tasks/${ruleId}/stop`, { method: "POST" }, token);
