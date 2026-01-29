import React, { useState } from "react";
import { login } from "../api/auth";

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await login(username, password);
      localStorage.setItem("accessToken", result.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main style={{ maxWidth: 320, margin: "0 auto", padding: "2rem" }}>
      <h1>Вход</h1>

      {/* 
        Архитектура BLOCK 11 не меняется.
        Экран логина остаётся в существующем routing и shell,
        редиректы и защита выполняются через RequireAuth и SmartRedirect.
      */}
      <form onSubmit={handleSubmit}>
        <label>
          Логин
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </label>

        <label>
          Пароль
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Вход..." : "Войти"}
        </button>
      </form>

      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </main>
  );
};

export default LoginPage;
