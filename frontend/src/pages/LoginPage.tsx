import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

// Страница логина с базовой формой авторизации.
export const LoginPage = () => {
  const { login, token, isLoading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      navigate("/app", { replace: true });
    }
  }, [token, navigate]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await login(username, password);
      navigate("/app", { replace: true });
    } catch {
      setError("Не удалось войти. Проверьте логин и пароль.");
    }
  };

  return (
    <div className="auth-wrapper">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Вход в платформу</h1>
        <p className="muted">
          Используйте корпоративные учётные данные, чтобы получить доступ к модулям.
        </p>
        <label className="field">
          <span>Логин</span>
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Введите логин"
            autoComplete="username"
            required
          />
        </label>
        <label className="field">
          <span>Пароль</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Минимум 6 символов"
            autoComplete="current-password"
            required
          />
        </label>
        {error && <div className="error-banner">{error}</div>}
        <button type="submit" className="primary-button" disabled={isLoading}>
          {isLoading ? "Входим..." : "Войти"}
        </button>
      </form>
    </div>
  );
};
