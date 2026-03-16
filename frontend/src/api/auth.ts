import { API_BASE_URL } from "../config/appConfig";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export const requestLogin = async (username: string, password: string): Promise<LoginResponse> => {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });

  if (!response.ok) {
    throw new Error("login_failed");
  }

  return response.json();
};
