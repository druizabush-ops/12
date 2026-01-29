import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { fetchMe, loginRequest } from "../api/auth";
import { STORAGE_KEYS } from "../config/storageKeys";
import { UserProfile } from "../types/auth";

type AuthContextValue = {
  token: string | null;
  user: UserProfile | null;
  isLoading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Провайдер аутентификации хранит токен и пользователя и синхронизирует их с localStorage.
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEYS.authToken)
  );
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.authToken);
  }, []);

  const loadUser = useCallback(
    async (activeToken: string) => {
      setIsLoading(true);
      try {
        const profile = await fetchMe(activeToken);
        setUser(profile);
      } catch {
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    },
    [clearAuth]
  );

  const signIn = useCallback(
    async (username: string, password: string) => {
      const data = await loginRequest(username, password);
      localStorage.setItem(STORAGE_KEYS.authToken, data.access_token);
      setToken(data.access_token);
      await loadUser(data.access_token);
    },
    [loadUser]
  );

  const signOut = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  React.useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    void loadUser(token);
  }, [token, loadUser]);

  const value = useMemo(
    () => ({ token, user, isLoading, signIn, signOut }),
    [token, user, isLoading, signIn, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth должен использоваться внутри AuthProvider");
  }
  return context;
};
