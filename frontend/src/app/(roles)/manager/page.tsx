"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  FileText,
  Search,
  CheckCircle2,
  Users,
  LayoutGrid,
  PieChart as PieIcon,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// =====================
// Types
// =====================
export type Formulario = {
  id: string;
  nome_cliente: string;
  nome_formulario: string;
  status: "rascunho" | "em_analise" | "concluido";
  atualizado_em: string; // ISO
};

export type FrameworkStat = {
  framework: "NIST 2.0" | "CIS Controls" | "ISO 27001" | "LGPD" | string;
  clientes: number;
};

export type AnalystStat = {
  nome: string;
  total: number;
  ativos: number;
};

export type DashboardDTO = {
  porFramework: FrameworkStat[];
  porAnalista: AnalystStat[];
  formularios: {
    rascunhos: Formulario[];
    emAnalise: Formulario[];
    concluidos: Formulario[];
  };
};

// =====================
// Mocked fetch (keep the shape to swap for real API later)
// =====================
async function fetchManagerDashboard(): Promise<DashboardDTO> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        porFramework: [
          { framework: "NIST 2.0", clientes: 15 },
          { framework: "CIS Controls", clientes: 12 },
          { framework: "ISO 27001", clientes: 8 },
          { framework: "LGPD", clientes: 20 },
        ],
        porAnalista: [
          { nome: "Ana Silva", total: 8, ativos: 3 },
          { nome: "João Santos", total: 12, ativos: 5 },
          { nome: "Maria Costa", total: 6, ativos: 2 },
          { nome: "Pedro Lima", total: 9, ativos: 4 },
        ],
        formularios: {
          rascunhos: [
            {
              id: "r1",
              nome_cliente: "ACME Corp",
              nome_formulario: "NIST 2.0 - Diagnóstico",
              status: "rascunho",
              atualizado_em: "2025-08-08T10:10:00Z",
            },
            {
              id: "r2",
              nome_cliente: "Beta Ltda",
              nome_formulario: "Questionário Inicial",
              status: "rascunho",
              atualizado_em: "2025-08-09T09:00:00Z",
            },
          ],
          emAnalise: [
            {
              id: "a1",
              nome_cliente: "Cypher S.A.",
              nome_formulario: "NIST 2.0 - Avaliação",
              status: "em_analise",
              atualizado_em: "2025-08-09T14:30:00Z",
            },
            {
              id: "a2",
              nome_cliente: "Delta Inc",
              nome_formulario: "Gap Assessment",
              status: "em_analise",
              atualizado_em: "2025-08-07T16:45:00Z",
            },
          ],
          concluidos: [
            {
              id: "c1",
              nome_cliente: "Zeta Bank",
              nome_formulario: "Relatório Executivo",
              status: "concluido",
              atualizado_em: "2025-08-05T18:00:00Z",
            },
          ],
        },
      });
    }, 250);
  });
}

// =====================
// Helpers
// =====================
function formatDate(iso?: string) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleDateString();
  } catch {
    return "-";
  }
}

const StatusPill = ({ status }: { status: Formulario["status"] }) => {
  const token =
    status === "rascunho"
      ? "--status-draft"
      : status === "em_analise"
      ? "--status-review"
      : "--status-done";

  // usa color-mix pra um fundo suave com contraste ok nos 2 temas
  const bg = `color-mix(in srgb, var(${token}) 15%, transparent)`;
  const fg = `var(${token})`;

  const Icon =
    status === "rascunho" ? FileText : status === "em_analise" ? Search : CheckCircle2;

  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: bg, color: fg }}
    >
      <Icon className="mr-1 h-3.5 w-3.5" />
      {status.replace("_", " ")}
    </span>
  );
};

const Table = ({ data }: { data: Formulario[] }) => (
  <div className="overflow-x-auto rounded-xl border border-border">
    <table className="w-full text-sm">
      <thead className="bg-muted text-muted-foreground">
        <tr>
          <th className="px-3 py-2 text-left font-medium">Cliente</th>
          <th className="px-3 py-2 text-left font-medium">Formulário</th>
          <th className="px-3 py-2 text-left font-medium">Status</th>
          <th className="px-3 py-2 text-left font-medium">Última atualização</th>
        </tr>
      </thead>
      <tbody>
        {data.map((f) => (
          <tr key={f.id} className="odd:bg-background even:bg-muted">
            <td className="px-3 py-2">{f.nome_cliente || "-"}</td>
            <td className="px-3 py-2">{f.nome_formulario || "-"}</td>
            <td className="px-3 py-2">
              <StatusPill status={f.status} />
            </td>
            <td className="px-3 py-2">{formatDate(f.atualizado_em)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// =====================
// Page
// =====================
export default function ManagerDashboard() {
  const [data, setData] = useState<DashboardDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchManagerDashboard()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  const resumo = useMemo(() => {
    if (!data) return { r: 0, a: 0, c: 0 };
    return {
      r: data.formularios.rascunhos.length,
      a: data.formularios.emAnalise.length,
      c: data.formularios.concluidos.length,
    };
  }, [data]);

  const donutData = useMemo(
    () => [
      { name: "Rascunho", value: resumo.r },
      { name: "Em Análise", value: resumo.a },
      { name: "Concluído", value: resumo.c },
    ],
    [resumo]
  );

  return (
    <AppShell>
      <div className="p-4 md:p-6">

        {/* ========== Linha 1: Cards por Framework ========== */}
        <section className="mb-6">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-foreground">
            <LayoutGrid className="h-4 w-4" /> Clientes por Framework
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {(data?.porFramework || []).map((fw) => (
              <div key={fw.framework} className="rounded-xl border border-border bg-card p-4">
                <p className="text-sm font-medium text-foreground">{fw.framework}</p>
                <div className="mt-2 text-3xl font-semibold text-foreground">{fw.clientes}</div>
                <p className="text-xs text-muted-foreground mt-1">clientes</p>
              </div>
            ))}
          </div>
        </section>

        {/* ========== Linha 2: Cards por Analista ========== */}
        <section className="mb-6">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-foreground">
            <Users className="h-4 w-4" /> Clientes por Analista
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {(data?.porAnalista || []).map((an) => (
              <div key={an.nome} className="rounded-xl border border-border bg-card p-4">
                <p className="text-sm font-medium text-foreground">{an.nome}</p>
                <div className="mt-2 flex items-end gap-4">
                  <div>
                    <div className="text-2xl font-semibold text-foreground">{an.total}</div>
                    <p className="text-xs text-muted-foreground">Total</p>
                  </div>
                  <div>
                    <div className="text-2xl font-semibold" style={{ color: "var(--status-done)" }}>{an.ativos}</div>
                    <p className="text-xs text-muted-foreground">Ativos</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ========== Linha 3: Tabelas de formulários ========== */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {/* Rascunho */}
          <div className="rounded-2xl border border-border bg-card p-4">
            <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-foreground">
              <FileText className="h-4 w-4" /> Formulários em Rascunho
            </h3>
            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando...</p>
            ) : data && data.formularios.rascunhos.length ? (
              <Table data={data.formularios.rascunhos} />
            ) : (
              <p className="text-sm text-muted-foreground">Nenhum formulário em rascunho.</p>
            )}
          </div>

          {/* Em análise */}
          <div className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
                <Search className="h-4 w-4" /> Formulários em Análise
              </h3>
              <a href="/analista/analises" className="text-sm" style={{ color: "var(--primary)" }}>
                Ver todos 👁️
              </a>
            </div>
            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando...</p>
            ) : data && data.formularios.emAnalise.length ? (
              <Table data={data.formularios.emAnalise} />
            ) : (
              <p className="text-sm text-muted-foreground">Nenhum formulário em análise.</p>
            )}
          </div>

          {/* Concluídos */}
          <div className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
                <CheckCircle2 className="h-4 w-4" /> Formulários Concluídos
              </h3>
              <a href="/analista/relatorios" className="text-sm" style={{ color: "var(--primary)" }}>
                Ver todos 👁️
              </a>
            </div>
            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando...</p>
            ) : data && data.formularios.concluidos.length ? (
              <Table data={data.formularios.concluidos} />
            ) : (
              <p className="text-sm text-muted-foreground">Nenhum formulário concluído.</p>
            )}
          </div>
        </section>

        {/* ========== Linha 4: Gráficos ========== */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-border bg-card p-4">
            <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-foreground">
              <LayoutGrid className="h-4 w-4" /> Distribuição por Framework
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.porFramework || []}>
                  <XAxis
                    dataKey="framework"
                    tick={{ fontSize: 12, fill: "var(--foreground)" }}
                    angle={-25}
                    dy={10}
                    interval={0}
                  />
                  <YAxis allowDecimals={false} tick={{ fill: "var(--foreground)" }} />
                  <Tooltip
                    contentStyle={{ background: "var(--card)", border: `1px solid var(--border)`, color: "var(--foreground)" }}
                    labelStyle={{ color: "var(--foreground)" }}
                    itemStyle={{ color: "var(--foreground)" }}
                  />
                  <Bar dataKey="clientes" radius={[6, 6, 0, 0]} fill="var(--chart-2)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-4">
            <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-foreground">
              <PieIcon className="h-4 w-4" /> Status dos Formulários
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={donutData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={85} paddingAngle={2}>
                    <Cell fill="var(--chart-1)" />
                    <Cell fill="var(--chart-2)" />
                    <Cell fill="var(--chart-3)" />
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "var(--card)", border: `1px solid var(--border)`, color: "var(--foreground)" }}
                    labelStyle={{ color: "var(--foreground)" }}
                    itemStyle={{ color: "var(--foreground)" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex items-center gap-6 text-sm text-foreground">
              <span className="inline-flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ background: "var(--chart-1)" }} />
                Rascunho: {resumo.r}
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ background: "var(--chart-2)" }} />
                Em Análise: {resumo.a}
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ background: "var(--chart-3)" }} />
                Concluído: {resumo.c}
              </span>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
