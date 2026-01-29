// Минимальный экран загрузки, чтобы не показывать пустой экран при запросе /auth/me.
export const LoadingPage = () => (
  <div className="loading-screen">
    <div className="loader" />
    <p>Проверяем доступ...</p>
  </div>
);
