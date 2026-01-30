// Файл описывает страницу входа, чтобы пользователь мог получить токен доступа.
// Страница отделена от остального UI, чтобы маршрут /login был самостоятельным.

import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { requestLogin } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";
import { APP_NAME } from "../config/appConfig";

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      // Логин через JSON, потому что backend принимает обычный application/json без OAuth2PasswordRequestForm.
      // Архитектура BLOCK 11 не меняется: форма вызывает requestLogin и работает через AuthContext.
      const data = await requestLogin(username, password);

      await login(data.access_token);
      navigate("/app", { replace: true });
    } catch (submitError) {
      setError("Не удалось войти. Проверьте логин и пароль.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="login-logo">🏠</span>
          <h1>{APP_NAME}</h1>
          <p>Войдите, чтобы продолжить работу с платформой.</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Логин</span>
            <input
              type="text"
              name="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Введите логин"
              required
            />
          </label>
          <label className="form-field">
            <span>Пароль</span>
            <input
              type="password"
              name="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Введите пароль"
              minLength={6}
              required
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Вход..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
