// src/app/(roles)/client/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  ensureClientSubmission,
  listClientSubmissions,
  submitSubmission,
  type SubmissionItem,
} from "@/services/submissions";
import { useAuth } from "@/contexts/AuthContext";

const DEFAULT_TEMPLATE_SLUG = "nist-csf-2-pt"; // <- CORRETO

function statusBadgeColor(s: SubmissionItem["status"]) {
  switch (s) {
    case "draft": return "bg-amber-100 text-amber-800 border-amber-200";
    case "in_review": return "bg-indigo-100 text-indigo-800 border-indigo-200";
    case "pending": return "bg-orange-100 text-orange-800 border-orange-200";
    case "submitted": return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "archived": return "bg-zinc-100 text-zinc-700 border-zinc-200";
    default: return "bg-muted text-foreground border-border";
  }
}
function statusLabel(s: SubmissionItem["status"]) {
  return s === "draft" ? "Rascunho"
    : s === "in_review" ? "Em análise"
    : s === "pending" ? "Pendente"
    : s === "submitted" ? "Concluído"
    : s === "archived" ? "Arquivado" : s;
}

export default function ClientPage() {
  const { user } = useAuth();
  const [clientId, setClientId] = useState<number | null>(null);

  useEffect(() => {
    let id: number | null = null;
    if (user?.role?.toLowerCase() === "subcliente") {
      id = (user as any)?.cliente?.id ?? user?.id ?? null;
    } else if (user?.id) {
      id = user.id;
    } else {
      try {
        const raw = localStorage.getItem("user");
        if (raw) {
          const u = JSON.parse(raw);
          id = u?.tipo === "subcliente" ? (u?.cliente?.id ?? u?.id ?? null) : (u?.id ?? null);
        }
      } catch {}
    }
    setClientId(id);
  }, [user]);

  const [subs, setSubs] = useState<SubmissionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!clientId) return;
    (async () => {
      setLoading(true);
      setErr(null);
      try {
        // garante que exista ao menos uma submission
        await ensureClientSubmission(clientId, DEFAULT_TEMPLATE_SLUG);
        // lista e hidrata (com template/framework)
        const all = await listClientSubmissions(clientId);
        setSubs(all);
      } catch (e) {
        console.error(e);
        setErr("Não foi possível carregar seus formulários.");
      } finally {
        setLoading(false);
      }
    })();
  }, [clientId]);

  const groups = useMemo(() => {
    const g: Record<string, SubmissionItem[]> = { draft: [], in_review: [], pending: [], submitted: [], archived: [] };
    subs.forEach((s) => { (g[s.status] ||= []).push(s); });
    return g;
  }, [subs]);

  const goToForm = (s: SubmissionItem) => {
    localStorage.setItem("nomeFormulario", s.template.name);
    localStorage.setItem("statusFormulario", s.status);
    localStorage.setItem("formularioRespondidoId", String(s.id));
    window.location.href = `/client/formulario/${s.template.slug}`; // ajuste a rota se necessário
  };

  const onSubmit = async (s: SubmissionItem) => {
    const updated = await submitSubmission(s.id);
    setSubs((prev) => prev.map((x) => (x.id === s.id ? updated : x)));
  };

  return (
    <AppShell>
      <div className="container-page p-6">
        <h1 className="text-xl font-semibold mb-1">Área do Cliente</h1>
        <p className="text-sm text-muted-foreground mb-6">Acompanhe seus formulários por status.</p>

        {loading && <p className="text-sm">Carregando…</p>}
        {err && <p className="text-sm text-red-600">{err}</p>}

        {!loading && !err && (
          <div className="space-y-8">
            {(["draft","in_review","pending","submitted"] as SubmissionItem["status"][]).map((section) => {
              const items = groups[section] || [];
              if (items.length === 0) return null;
              return (
                <section key={section}>
                  <h2 className="text-base font-medium mb-3">{statusLabel(section)}</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {items.map((s) => (
                      <div key={s.id} className="rounded-xl border border-border bg-card p-4 shadow-sm">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="font-medium leading-tight">{s.template.name}</h3>
                            <p className="text-xs text-muted-foreground">
                              {s.framework.name} · v{s.template.version}
                            </p>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full border ${statusBadgeColor(s.status)}`}>
                            {statusLabel(s.status)}
                          </span>
                        </div>

                        <div className="mt-3 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Progresso</span>
                            <span className="font-medium">{Number(s.progress) || 0}%</span>
                          </div>
                          <div className="mt-1 h-2 w-full rounded bg-muted overflow-hidden">
                            <div className="h-2 bg-primary" style={{ width: `${Math.min(Number(s.progress) || 0, 100)}%` }} />
                          </div>
                          <p className="mt-2 text-xs text-muted-foreground">
                            Atualizado em {new Date(s.updated_at).toLocaleDateString()}
                          </p>
                        </div>

                        <div className="mt-4 flex items-center gap-2">
                          <button
                            className="inline-flex items-center rounded-md bg-primary text-white text-sm px-3 py-1.5 hover:opacity-90"
                            onClick={() => goToForm(s)}
                          >
                            {s.status === "draft" ? "Continuar" : "Abrir"}
                          </button>

                          {s.status === "draft" && (
                            <button
                              className="inline-flex items-center rounded-md border border-border bg-card text-sm px-3 py-1.5 hover:bg-muted"
                              onClick={() => onSubmit(s)}
                            >
                              Finalizar (enviar)
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              );
            })}

            {subs.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Ainda não há formulários. Tente novamente em instantes.
              </p>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
