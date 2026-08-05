import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  clearStoredToken,
  getMe,
  getMyWorkspace,
  getStoredToken,
  login as apiLogin,
  setStoredToken,
  UnauthorizedError,
} from "../api/client";
import type { Me } from "../api/client";

interface AuthContextValue {
  token: string | null;
  user: Me | null;
  isAuthenticated: boolean;
  /** True while the current token's identity is being resolved via /auth/me. */
  isLoading: boolean;
  login: (userId: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<Me | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => getStoredToken() !== null);

  // Whenever the token changes (including on mount, if one was already in
  // sessionStorage), resolve the current identity via /auth/me. A 401 means
  // the stored token is stale/invalid, so it's cleared.
  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    getMe()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
        }
        // Every user gets a personal workspace by default — ensure it exists
        // as soon as their identity resolves, rather than requiring them to
        // know a "create my workspace" action exists. Idempotent server-side
        // and non-blocking: a failure here shouldn't break login.
        getMyWorkspace().catch(() => {});
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof UnauthorizedError) {
          clearStoredToken();
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (userId: string) => {
    const { token: newToken } = await apiLogin(userId);
    setStoredToken(newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: token !== null && user !== null,
      isLoading,
      login,
      logout,
    }),
    [token, user, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
