import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

// Страница логина: запрашивает username/password и сохраняет токен при успехе.
export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await signIn(username.trim(), password);
      navigate("/app", { replace: true });
    } catch {
      setError("Не удалось войти. Проверьте логин и пароль.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Вход в платформу</h1>
        <p className="login-card__subtitle">
          Используйте корпоративные данные доступа.
        </p>
        <form className="login-form" onSubmit={handleSubmit}>
          <label className="login-form__field">
            <span>Имя пользователя</span>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className="login-form__field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className="login-form__error">{error}</p>}
          <button className="login-form__submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Входим..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
};
