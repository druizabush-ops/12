import { API_BASE_URL } from "../config/apiConfig";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

type ApiFetchOptions = RequestInit & {
  token?: string | null;
};

// Унифицированная обёртка над fetch для всего приложения.
// Она добавляет base URL и при наличии токена подставляет Authorization.
export const apiFetch = async <T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> => {
  const { token, headers, ...rest } = options;
  const resolvedHeaders = new Headers(headers);

  if (token) {
    resolvedHeaders.set("Authorization", `Bearer ${token}`);
  }

  if (!resolvedHeaders.has("Content-Type") && rest.body) {
    resolvedHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: resolvedHeaders,
  });

  if (!response.ok) {
    let errorDetails: unknown = null;
    try {
      errorDetails = await response.json();
    } catch {
      errorDetails = await response.text();
    }
    throw new ApiError("API request failed", response.status, errorDetails);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
};
