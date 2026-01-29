import { apiFetch } from "./client";
import { TokenResponse, UserProfile } from "../types/auth";

// Запрос логина — возвращаем только access_token для хранения на клиенте.
export const loginRequest = async (
  username: string,
  password: string
): Promise<TokenResponse> =>
  apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

// Запрос текущего пользователя по Bearer токену.
export const fetchMe = async (token: string): Promise<UserProfile> =>
  apiFetch<UserProfile>("/auth/me", {
    method: "GET",
    token,
  });
