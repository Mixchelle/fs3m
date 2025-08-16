#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Helpers
mkd() { mkdir -p "$ROOT_DIR/$1"; }
mkf() { [ -f "$ROOT_DIR/$1" ] || (mkdir -p "$(dirname "$ROOT_DIR/$1")" && cat > "$ROOT_DIR/$1"); }

echo "Scaffolding frontend in: $ROOT_DIR"

############################################
# 1) Folders
############################################
mkd "src/app/(auth)/login"
mkd "src/app/(roles)/client"
mkd "src/app/(roles)/analyst"
mkd "src/app/(roles)/manager"
mkd "src/app/(dashboard)"
mkd "src/app/api" # (se precisar rotas internas depois)
mkd "src/components/global"
mkd "src/components/ui"
mkd "src/components/charts"
mkd "src/components/layout"
mkd "src/contexts"
mkd "src/hooks"
mkd "src/lib"
mkd "src/services"
mkd "src/state"
mkd "src/styles/base"
mkd "src/styles/pages"
mkd "src/styles/components"
mkd "src/types"
mkd "src/utils"
mkd "public/assets"
mkd "scripts"

############################################
# 2) Styles (Tailwind + globals)
############################################
mkf "src/styles/base/globals.css" <<'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* CSS vars (light/dark) */
:root {
  --header-h: 56px;
  --sidebar-w: 260px;
}

/* base resets */
html, body, #__next { height: 100%; }
body { @apply bg-background text-foreground; }

/* layout helpers */
.container-page {
  @apply mx-auto max-w-7xl px-4 sm:px-6 lg:px-8;
}
EOF

mkf "src/styles/components/layout.css" <<'EOF'
.header {
  @apply h-[var(--header-h)] border-b bg-card;
}
.sidebar {
  @apply w-[var(--sidebar-w)] border-r bg-card;
}
.content {
  @apply flex-1 p-4;
}
EOF

mkf "src/styles/pages/login.css" <<'EOF'
.login-card {
  @apply max-w-md mx-auto rounded-2xl shadow p-6 bg-card border;
}
EOF

############################################
# 3) lib (axios client, swr config, theme)
############################################
mkf "src/lib/apiClient.ts" <<'EOF'
import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
EOF

mkf "src/lib/swrConfig.ts" <<'EOF'
import useSWR, { SWRConfiguration } from "swr";
import { api } from "./apiClient";

export const defaultSWRConfig: SWRConfiguration = {
  fetcher: (url: string) => api.get(url).then(res => res.data),
  revalidateOnFocus: true,
  shouldRetryOnError: false,
};

export const useApi = (key: string | null) => useSWR(key, defaultSWRConfig.fetcher);
EOF

############################################
# 4) Context API (Auth)
############################################
mkf "src/contexts/AuthContext.tsx" <<'EOF'
"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/apiClient";

type Role = "client" | "analyst" | "manager" | "guest";

type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
} | null;

type AuthContextType = {
  user: User;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) { setLoading(false); return; }

    api.get("/users/me/")
      .then(res => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/users/login/", { email, password });
    localStorage.setItem("token", res.data.token);
    const me = await api.get("/users/me/");
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("token");
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
EOF

############################################
# 5) Hooks
############################################
mkf "src/hooks/useSidebar.ts" <<'EOF'
"use client";

import { useState, useEffect } from "react";

export function useSidebar() {
  const [open, setOpen] = useState(true);
  useEffect(() => {
    const saved = localStorage.getItem("sidebar_open");
    if (saved) setOpen(saved === "1");
  }, []);
  useEffect(() => {
    localStorage.setItem("sidebar_open", open ? "1" : "0");
  }, [open]);
  return { open, setOpen };
}
EOF

############################################
# 6) Services (API wrappers)
############################################
mkf "src/services/auth.ts" <<'EOF'
import { api } from "@/lib/apiClient";

export async function login(email: string, password: string) {
  const res = await api.post("/users/login/", { email, password });
  return res.data;
}

export async function me() {
  const res = await api.get("/users/me/");
  return res.data;
}
EOF

mkf "src/services/assessments.ts" <<'EOF'
import { api } from "@/lib/apiClient";

export async function runAssessment(submissionId: number, type = "maturity-1-5") {
  const res = await api.post(`/assessments/run/${submissionId}/?type=${type}`);
  return res.data;
}

export async function getAssessment(assessmentId: number) {
  const res = await api.get(`/assessments/${assessmentId}/`);
  return res.data;
}
EOF

mkf "src/services/recommendations.ts" <<'EOF'
import { api } from "@/lib/apiClient";

export async function listRecommendationsBySubmission(submissionId: number) {
  const res = await api.get(`/recommendations/?submission=${submissionId}`);
  return res.data;
}
EOF

mkf "src/services/actionPlans.ts" <<'EOF'
import { api } from "@/lib/apiClient";

export async function listActionPlans(submissionId?: number) {
  const url = submissionId ? `/actionplans/?submission=${submissionId}` : "/actionplans/";
  const res = await api.get(url);
  return res.data;
}
EOF

############################################
# 7) Types
############################################
mkf "src/types/user.ts" <<'EOF'
export type Role = "client" | "analyst" | "manager" | "guest";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
};
EOF

mkf "src/types/recommendation.ts" <<'EOF'
export type Recommendation = {
  id: number;
  nome: string;
  categoria: string;
  aplicabilidade: "Política" | "Prática" | "Ambas";
  tecnologia: string;
  nist: string;
  prioridade: "baixa" | "media" | "alta";
  responsavel: string;
  data_inicio: string;
  data_fim: string;
  meses: number;
  detalhes: string;
  investimentos: string;
  riscos: string;
  justificativa: string;
  observacoes: string;
  urgencia: "1"|"2"|"3"|"4"|"5";
  gravidade: "1"|"2"|"3"|"4"|"5";
  cumprida: boolean;
  perguntaId: string;
};
EOF

mkf "src/types/actionPlan.ts" <<'EOF'
import { Recommendation } from "./recommendation";

export type ActionPlan = {
  id: number;
  cliente: any;
  criado_por: any;
  observacoes: string;
  data_criacao: string;
  data_atualizacao: string;
  prazo?: string;
  gravidade?: string;
  urgencia?: string;
  categoria?: string;
  orcamentoMax?: string;
  submission_id?: number|null;
  recomendacoes: (Recommendation & { ordem: number; status: string; data_alteracao: string })[];
};
EOF

mkf "src/types/assessment.ts" <<'EOF'
export type AssessmentBucket = {
  level: "FUNCTION" | "CATEGORY" | "CONTROL";
  code: string;
  name: string;
  order: number;
  metrics: any;
};

export type Assessment = {
  id: number;
  framework: any;
  assessment_type: any;
  summary: { media_geral: number; objetivo: number; status: string };
  buckets: AssessmentBucket[];
};
EOF

############################################
# 8) Components (global/layout/ui)
############################################
mkf "src/components/global/Header.tsx" <<'EOF'
"use client";
import Link from "next/link";

export default function Header() {
  return (
    <header className="header flex items-center justify-between px-4">
      <Link href="/" className="font-semibold">FS3M</Link>
      <nav className="flex items-center gap-4 text-sm">
        <Link href="/(roles)/client">Client</Link>
        <Link href="/(roles)/analyst">Analyst</Link>
        <Link href="/(roles)/manager">Manager</Link>
      </nav>
    </header>
  );
}
EOF

mkf "src/components/global/Sidebar.tsx" <<'EOF'
"use client";
import Link from "next/link";
import { useSidebar } from "@/hooks/useSidebar";

export default function Sidebar() {
  const { open, setOpen } = useSidebar();
  return (
    <aside className={`sidebar hidden md:block`}>
      <div className="p-4 flex items-center justify-between">
        <span className="font-medium">Navigation</span>
        <button className="text-xs underline" onClick={() => setOpen(!open)}>
          {open ? "Collapse" : "Expand"}
        </button>
      </div>
      {open && (
        <ul className="px-4 pb-4 space-y-2 text-sm">
          <li><Link href="/(dashboard)">Dashboard</Link></li>
          <li><Link href="/(roles)/client">Client area</Link></li>
          <li><Link href="/(roles)/analyst">Analyst area</Link></li>
          <li><Link href="/(roles)/manager">Manager area</Link></li>
          <li><Link href="/(auth)/login">Login</Link></li>
        </ul>
      )}
    </aside>
  );
}
EOF

mkf "src/components/global/Footer.tsx" <<'EOF'
export default function Footer() {
  return (
    <footer className="border-t py-4 text-xs text-center text-muted-foreground">
      © {new Date().getFullYear()} FS3M — All rights reserved.
    </footer>
  );
}
EOF

mkf "src/components/layout/AppShell.tsx" <<'EOF'
"use client";

import Header from "@/components/global/Header";
import Sidebar from "@/components/global/Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
EOF

############################################
# 9) App Router: layout, pages
############################################
mkf "src/app/layout.tsx" <<'EOF'
import type { Metadata } from "next";
import "@/styles/base/globals.css";
import "@/styles/components/layout.css";
import "@/styles/pages/login.css";
import { AuthProvider } from "@/contexts/AuthContext";

export const metadata: Metadata = {
  title: "FS3M",
  description: "Security Maturity Management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
EOF

mkf "src/app/page.tsx" <<'EOF'
import AppShell from "@/components/layout/AppShell";

export default function Home() {
  return (
    <AppShell>
      <div className="container-page">
        <h1 className="text-2xl font-semibold mb-2">Welcome to FS3M</h1>
        <p className="text-sm text-muted-foreground">
          Choose a role in the top nav or sidebar to begin.
        </p>
      </div>
    </AppShell>
  );
}
EOF

mkf "src/app/(auth)/login/page.tsx" <<'EOF'
"use client";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(email, password);
  }
  return (
    <div className="min-h-[calc(100vh-56px)] grid place-items-center">
      <form onSubmit={onSubmit} className="login-card space-y-4 w-full">
        <h2 className="text-lg font-semibold">Sign in</h2>
        <input
          className="w-full border rounded-md px-3 py-2"
          placeholder="email"
          value={email}
          onChange={(e)=>setEmail(e.target.value)}
        />
        <input
          className="w-full border rounded-md px-3 py-2"
          type="password"
          placeholder="password"
          value={password}
          onChange={(e)=>setPassword(e.target.value)}
        />
        <button className="w-full border rounded-md px-3 py-2 hover:bg-accent">Login</button>
      </form>
    </div>
  );
}
EOF

mkf "src/app/(roles)/client/page.tsx" <<'EOF'
import AppShell from "@/components/layout/AppShell";

export default function ClientPage() {
  return (
    <AppShell>
      <div className="container-page">
        <h1 className="text-xl font-semibold mb-4">Client Area</h1>
        <p className="text-sm text-muted-foreground">Client dashboard and reports go here.</p>
      </div>
    </AppShell>
  );
}
EOF

mkf "src/app/(roles)/analyst/page.tsx" <<'EOF'
import AppShell from "@/components/layout/AppShell";

export default function AnalystPage() {
  return (
    <AppShell>
      <div className="container-page">
        <h1 className="text-xl font-semibold mb-4">Analyst Area</h1>
        <p className="text-sm text-muted-foreground">Assessments, recommendations and analysis tools.</p>
      </div>
    </AppShell>
  );
}
EOF

mkf "src/app/(roles)/manager/page.tsx" <<'EOF'
import AppShell from "@/components/layout/AppShell";

export default function ManagerPage() {
  return (
    <AppShell>
      <div className="container-page">
        <h1 className="text-xl font-semibold mb-4">Manager Area</h1>
        <p className="text-sm text-muted-foreground">KPIs, action plans and approvals.</p>
      </div>
    </AppShell>
  );
}
EOF

mkf "src/app/(dashboard)/page.tsx" <<'EOF'
import AppShell from "@/components/layout/AppShell";

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="container-page">
        <h1 className="text-xl font-semibold mb-4">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Overview of assessments and maturity.</p>
      </div>
    </AppShell>
  );
}
EOF

############################################
# 10) Tailwind config tweaks (optional ids)
############################################
# add basic color aliases if tailwind config exists
TW="$ROOT_DIR/tailwind.config.ts"
if [ -f "$TW" ] && ! grep -q "background" "$TW"; then
  tmp="$(mktemp)"
  node - <<'JS' "$TW" "$tmp"
const fs = require('fs');
const [,,inFile,outFile] = process.argv;
let s = fs.readFileSync(inFile,'utf8');
s = s.replace(/theme:\s*{[^}]*}/s, (m)=> {
  if (m.includes('extend')) return m;
  return m.replace(/theme:\s*{/, 'theme: { extend: { colors: { background: "#0b0b0c", foreground: "#fafafa", card: "#111113", accent: "#1f1f22", muted: "#8a8a8a" } }, ');
});
fs.writeFileSync(outFile, s);
JS
  mv "$tmp" "$TW"
fi

echo "Done. ✅"
