// Минимальная точка входа React-приложения.
// Файл существует для проверки запуска и отображения базового текста.
// Минимальность — только отрисовка простого компонента.

import React from "react";
import ReactDOM from "react-dom/client";

const App = () => (
  <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
    <h1>Core Platform</h1>
    <p>Минимальный фронтенд Block 0 запущен.</p>
  </div>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
