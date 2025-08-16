"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setTokens, clearTokens, getAccessToken } from "@/lib/apiClient";

// Papel em PT (mantemos "guest" como fallback)
export type RolePt = "cliente" | "subcliente" | "analista" | "gestor" | "guest";

export type User = {
  id: number;
  nome?: string;
  name?: string;
  email: string;
  role: RolePt;            // << usar PT aqui
  permissoes?: string[];   // << trazemos do backend se vier
} | null;

type AuthContextType = {
  user: User;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function normalizeRolePt(role?: string | null): RolePt {
  const r = (role || "").toLowerCase();
  if (["cliente", "client"].includes(r)) return "cliente";
  if (["subcliente", "subclient"].includes(r)) return "subcliente";
  if (["analista", "analyst"].includes(r)) return "analista";
  if (["gestor", "manager", "admin", "administrator"].includes(r)) return "gestor";
  return "guest";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  // carrega sessão existente
  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/users/me/")
      .then((res) => {
        const u = res.data;
        setUser({
          id: u.id,
          email: u.email,
          name: u.name || u.nome,
          nome: u.nome,
          role: normalizeRolePt(u.role),
          // traga permissões se existirem com qualquer chave
          permissoes: u.permissoes || u.permissions || u.perms || [],
        });
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post("/auth/token/", { email, password });
    setTokens(data.access, data.refresh);

    const me = await api.get("/users/me/");
    const u = me.data;
    setUser({
      id: u.id,
      email: u.email,
      name: u.name || u.nome,
      nome: u.nome,
      role: normalizeRolePt(u.role),
      permissoes: u.permissoes || u.permissions || u.perms || [],
    });
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
