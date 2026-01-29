// Минимальные типы для аутентификации и профиля пользователя.

export type UserProfile = {
  id: number;
  username: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
