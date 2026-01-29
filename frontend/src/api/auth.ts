// Модуль содержит точечный helper для логина без изменения архитектуры BLOCK 11.
// Логин отправляется как application/x-www-form-urlencoded, потому что backend ждёт OAuth2PasswordRequestForm.
// В браузере важно явно передать body строкой (URLSearchParams + toString), иначе возможен 422 из-за неверного формата.

import { apiFetch } from "./client";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export const requestLogin = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const body = new URLSearchParams({ username, password }).toString();

  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
};
