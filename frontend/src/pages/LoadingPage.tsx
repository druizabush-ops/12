// Файл отображает статус загрузки, чтобы пользователь видел ожидание авторизации.
// Вынос в отдельную страницу избавляет от повторения разметки в нескольких местах.

const LoadingPage = () => (
  <div className="page loading-page">
    <div className="spinner" />
    <p>Загружаем профиль...</p>
  </div>
);

export default LoadingPage;
