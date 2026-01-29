import { API_BASE_URL } from "../config";

export type ApiError = {
  status: number;
  message: string;
};

// Унифицированный клиент для запросов к API с автоматическим добавлением токена.
export const apiRequest = async <T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> => {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw {
      status: response.status,
      message: message || "Ошибка запроса",
    } as ApiError;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
};
