// Файл описывает API-обёртку для логина, чтобы запросы шли через единый apiFetch.
// OAuth2PasswordRequestForm не используем, потому что логин принят как обычный JSON API.
// Архитектура BLOCK 11 не меняется, мы только фиксируем формат запроса.

import { apiFetch } from "./client";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type UserListItem = {
  id: number;
  full_name: string;
};

export const requestLogin = (username: string, password: string) =>
  apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const getUsers = (token: string) => apiFetch<UserListItem[]>("/auth/users", { method: "GET" }, token);
