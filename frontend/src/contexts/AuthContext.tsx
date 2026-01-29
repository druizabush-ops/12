import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { apiRequest } from "../api/client";

type AuthUser = {
  id: number | string;
  username: string;
};

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = "core-platform-token";

// Провайдер авторизации хранит токен и пользователя, полученного через /auth/me.
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchUser = useCallback(async (activeToken: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<AuthUser>("/auth/me", {}, activeToken);
      setUser(data);
    } catch (error) {
      // При ошибке авторизации очищаем токен, чтобы вернуть пользователя на логин.
      setToken(null);
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchUser(token);
      return;
    }
    setUser(null);
  }, [token, fetchUser]);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setToken(data.access_token);
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({ token, user, isLoading, login, logout }),
    [token, user, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth должен использоваться внутри AuthProvider");
  }
  return context;
};
