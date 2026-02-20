import { Navigate } from "react-router-dom";
import { useModules } from "../hooks/useModules";

const AppHomePage = () => {
  const { modules, isLoading } = useModules();

  if (isLoading) {
    return <p>Загрузка...</p>;
  }

  const visibleModules = modules.filter((moduleItem) => moduleItem.has_access);
  const firstModule = visibleModules[0];

  if (!firstModule) {
    return <Navigate to="/app/help" replace />;
  }

  return <Navigate to={`/app/modules/${firstModule.path}`} replace />;
};

export default AppHomePage;
