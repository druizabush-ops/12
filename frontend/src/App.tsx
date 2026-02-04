// Файл содержит верхнеуровневый роутинг приложения и связывает все страницы.
// Маршруты вынесены сюда, чтобы точка входа оставалась чистой и предсказуемой.

import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import { ModuleContainer } from "./components/ModuleContainer";
import HelpPage from "./pages/HelpPage";
import LoginPage from "./pages/LoginPage";
import RequireAuth from "./routes/RequireAuth";
import SmartRedirect from "./routes/SmartRedirect";

const App = () => (
  <Routes>
    <Route path="/" element={<SmartRedirect />} />
    <Route path="/login" element={<LoginPage />} />
    <Route
      path="/app"
      element={
        <RequireAuth>
          <AppLayout />
        </RequireAuth>
      }
    >
      <Route index element={<HelpPage />} />
      <Route path="help" element={<HelpPage />} />
      <Route path="modules/:modulePath" element={<ModuleContainer />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

export default App;
