const API_BASE_URL = "http://localhost:8000";

type LoginResponse = {
  access_token: string;
};

export const login = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  // Отправляем form-urlencoded, потому что backend использует OAuth2PasswordRequestForm и принимает только такой формат.
  // Архитектура BLOCK 11 не меняется: здесь только исправление формата запроса без изменения маршрутизации и shell.
  const body = new URLSearchParams({
    username,
    password,
  });

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  if (!response.ok) {
    throw new Error("Не удалось выполнить вход");
  }

  return response.json();
};
