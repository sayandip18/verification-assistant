"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Officer } from "./types";

type AuthContextValue = {
  officer: Officer | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [officer, setOfficer] = useState<Officer | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    api
      .me()
      .then(setOfficer)
      .catch(() => setOfficer(null))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (!officer && pathname !== "/login") {
      router.replace("/login");
    }
    if (officer && pathname === "/login") {
      router.replace("/");
    }
  }, [officer, pathname, ready, router]);

  const login = useCallback(async (email: string, password: string) => {
    const session = await api.login(email, password);
    setOfficer(session);
    router.replace("/");
  }, [router]);

  const logout = useCallback(async () => {
    await api.logout();
    setOfficer(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo(() => ({ officer, ready, login, logout }), [officer, ready, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
