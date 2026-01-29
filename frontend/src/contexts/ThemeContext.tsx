import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { STORAGE_KEYS } from "../config/storageKeys";

type ThemeMode = "light" | "dark";

type ThemeContextValue = {
  theme: ThemeMode;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const resolveInitialTheme = (): ThemeMode => {
  const stored = localStorage.getItem(STORAGE_KEYS.theme);
  return stored === "dark" ? "dark" : "light";
};

// Провайдер темы управляет светлой/тёмной схемой и сохраняет выбор пользователя.
export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [theme, setTheme] = useState<ThemeMode>(() => resolveInitialTheme());

  const applyTheme = useCallback((nextTheme: ThemeMode) => {
    setTheme(nextTheme);
    localStorage.setItem(STORAGE_KEYS.theme, nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  }, []);

  const toggleTheme = useCallback(() => {
    applyTheme(theme === "light" ? "dark" : "light");
  }, [applyTheme, theme]);

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme должен использоваться внутри ThemeProvider");
  }
  return context;
};
