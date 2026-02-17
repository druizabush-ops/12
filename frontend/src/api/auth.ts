import { apiFetch } from "./client";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type AuthUser = {
  id: number;
  full_name: string;
};

export const requestLogin = (username: string, password: string) =>
  apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const getUsers = (token: string) => apiFetch<AuthUser[]>("/auth/users", { method: "GET" }, token);
