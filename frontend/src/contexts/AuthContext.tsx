// Файл хранит контекст авторизации, чтобы токен и пользователь были доступны везде.
// Мы держим логику входа и выхода здесь, чтобы избежать дублирования по страницам.

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";

type User = {
  id: number;
  username: string;
};

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (tokenValue: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = "auth_token";

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }, []);

  const fetchUser = useCallback(
    async (currentToken: string) => {
      setIsLoading(true);

      try {
        const data = await apiFetch<User>("/auth/me", { method: "GET" }, currentToken);
        setUser(data);
      } catch (error) {
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    },
    [clearAuth]
  );

  useEffect(() => {
    if (token) {
      void fetchUser(token);
      return;
    }

    setUser(null);
  }, [token, fetchUser]);

  const login = useCallback(
    async (tokenValue: string) => {
      setToken(tokenValue);
      localStorage.setItem(TOKEN_STORAGE_KEY, tokenValue);
      await fetchUser(tokenValue);
    },
    [fetchUser]
  );

  const logout = useCallback(() => {
    clearAuth();
    navigate("/login", { replace: true });
  }, [clearAuth, navigate]);

  const value = useMemo(
    () => ({
      token,
      user,
      isLoading,
      login,
      logout,
    }),
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
