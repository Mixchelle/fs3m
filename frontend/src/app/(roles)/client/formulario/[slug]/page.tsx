"use client";

import React, { use as useUnwrap, useEffect, useMemo, useRef, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { useAuth } from "@/contexts/AuthContext";
import {
  ensureClientSubmission,
  getSubmissionAnswers,
  startReviewSubmission,
  submitSubmission,
  upsertAnswer,
  patchAnswerAttachment,
} from "@/services/submissions";
import { getTemplateDetail, listDomainsByFramework } from "@/services/frameworks";
import { SubmissionItem } from "@/types/submissions.types";
import { DomainItem, TemplateDetail } from "@/types/frameworks.types";
import { Paperclip, Check, File as FileIcon, Image as ImageIcon } from "lucide-react";

/** ===== Tipos locais ===== */
type PartsMap = {
  score?: number;
  policy?: number;
  practice?: number;
  info?: number;
  attachment?: number;
  evidence?: number;
};

type UIQuestion = {
  id: number;        // control id
  code: string;      // ex.: RC.RP-01
  prompt: string;    // título do controle
  parts: PartsMap;   // subperguntas mapeadas por local_code
};

type AttachmentThumb = { name: string; url?: string; isImage?: boolean };

type QAState = {
  policy?: string;
  practice?: string;
  info?: string;
  // compat + multi
  attachmentName?: string | null;
  attachments?: AttachmentThumb[];
  ids?: {
    policy?: number;
    practice?: number;
    info?: number;
    attachment?: number;
  };
};

type Section = {
  id: number;      // domain id
  title: string;   // "RC. Recuperar (RC)"
  questions: UIQuestion[]; // 1 por controle
};

function normCode(s?: string | null) {
  const k = (s || "").trim().toLowerCase();
  if (k === "politica" || k === "policy") return "policy";
  if (k === "pratica" || k === "practice") return "practice";
  if (k === "score" || k === "maturity") return "score";
  if (k === "attachment" || k === "anexo" || k === "anexos") return "attachment";
  if (k === "evidence" || k === "evidencia" || k === "evidências" || k === "evidencias") return "evidence";
  if (k === "info" || k === "informacoes" || k === "informações") return "info";
  return k;
}

function readAnswerValue(value: any): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "object") {
    if ("label" in value && typeof (value as any).label === "string") return (value as any).label;
    if ("value" in value && typeof (value as any).value !== "undefined") return String((value as any).value);
  }
  try { return JSON.stringify(value); } catch { return String(value); }
}

function isImageFilename(name?: string) {
  if (!name) return false;
  const n = name.toLowerCase();
  return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"].some(ext => n.endsWith(ext));
}

/** ===== Página ===== */
export default function NistFormPage({
  params,
}: { params: Promise<{ slug: string }> }) {
  const { user } = useAuth();
  const { slug } = useUnwrap(params);

  // resolve clientId (cliente/subcliente)
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
          id = u?.tipo === "subcliente" ? u?.cliente?.id ?? u?.id ?? null : u?.id ?? null;
        }
      } catch {}
    }
    setClientId(id);
  }, [user]);

  // submissão e template
  const [sub, setSub] = useState<SubmissionItem | null>(null);
  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [answers, setAnswers] = useState<Record<number, QAState>>({});
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  // UI state
  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [qIndex, setQIndex] = useState(0);

  const isReadOnly =
    sub?.status === "in_review" ||
    sub?.status === "submitted" ||
    sub?.status === "archived";

  // ===== boot =====
  useEffect(() => {
    if (!clientId) return;

    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const dash = await ensureClientSubmission(clientId, slug);
        if (!dash.submission) {
          setSub(null);
          setSections([]);
          return;
        }
        setSub(dash.submission);

        const tpl = await getTemplateDetail(dash.submission.template.id);
        setTemplate(tpl);

        const domains = await listDomainsByFramework(tpl.framework.id);

        // monta seções a partir dos domains (controls -> questions)
        const builtSections: Section[] = (domains as DomainItem[])
          .map((dom) => {
            const title = dom.code ? `${dom.code}. ${dom.title}` : dom.title;

            const qs: UIQuestion[] = ((dom as any).controls || []).map((c: any) => {
              const parts: PartsMap = {};
              for (const q of c.questions || []) {
                const key = normCode(q.local_code);
                if (["score", "policy", "practice", "info", "attachment", "evidence"].includes(key)) {
                  (parts as any)[key] = q.id;
                }
              }
              return { id: c.id, code: c.code, prompt: c.title, parts };
            });

            qs.sort((a, b) => a.code.localeCompare(b.code, undefined, { numeric: true }));
            return { id: dom.id, title, questions: qs };
          })
          .map((s) => ({ ...s, questions: s.questions.filter((q) => Object.keys(q.parts).length > 0) }))
          .filter((s) => s.questions.length > 0);

        builtSections.sort((a, b) => a.title.localeCompare(b.title, undefined, { numeric: true }));

        const DOMAIN_ORDER = ["GV", "ID", "PR", "DE", "RS", "RC"] as const;

        builtSections.sort((a, b) => {
        // tenta extrair o código do domínio no início do título (ex.: "GV. Governança")
        const getCode = (t: string) => {
            const m = t.match(/^([A-Z]{2})\b/);
            return m ? m[1] : "";
        };

        const ac = getCode(a.title);
        const bc = getCode(b.title);

        const ai = DOMAIN_ORDER.indexOf(ac);
        const bi = DOMAIN_ORDER.indexOf(bc);

        // ordena pela ordem fixa; desconhecidos vão para o fim
        if (ai !== bi) return (ai === -1 ? Number.POSITIVE_INFINITY : ai) - (bi === -1 ? Number.POSITIVE_INFINITY : bi);

        // empate (mesmo domínio ou códigos desconhecidos): ordena natural pelo título
        return a.title.localeCompare(b.title, undefined, { numeric: true });
        });
        setSections(builtSections);
        if (builtSections.length) {
          setActiveSectionId(builtSections[0].id);
          setQIndex(0);
        }

        // respostas existentes
        const existing = await getSubmissionAnswers(dash.submission.id);
        const byQid = new Map<number, any>();
        for (const a of existing) byQid.set(a.question, a);

        const mapped: Record<number, QAState> = {};
        for (const sec of builtSections) {
          for (const uiq of sec.questions) {
            const st: QAState = { ids: {}, attachments: [] };

            if (uiq.parts.policy) {
              const a = byQid.get(uiq.parts.policy);
              if (a) { st.policy = readAnswerValue(a.value); st.ids!.policy = a.id; }
            }
            if (uiq.parts.practice) {
              const a = byQid.get(uiq.parts.practice);
              if (a) { st.practice = readAnswerValue(a.value); st.ids!.practice = a.id; }
            }
            if (uiq.parts.info) {
              const a = byQid.get(uiq.parts.info);
              if (a) { st.info = readAnswerValue(a.value) || a.evidence || ""; st.ids!.info = a.id; }
            }
            if (uiq.parts.attachment) {
              const a = byQid.get(uiq.parts.attachment);
              if (a?.attachment) {
                const name = String(a.attachment).split("/").pop() || String(a.attachment);
                st.attachmentName = a.attachment as string;
                st.attachments = [{ name, url: a.attachment as string, isImage: isImageFilename(name) }];
                st.ids!.attachment = a.id;
              }
            }

            if (st.policy || st.practice || st.info || st.attachments?.length) {
              mapped[uiq.id] = st;
            }
          }
        }
        setAnswers(mapped);
      } catch (e) {
        console.error(e);
        setErr("Não foi possível carregar o formulário.");
      } finally {
        setLoading(false);
      }
    })();
  }, [clientId, slug]);

  // flatten p/ progresso
  const flatQuestions = useMemo(
    () => sections.flatMap((s) => s.questions.map((q) => ({ ...q, domainId: s.id }))),
    [sections]
  );

  const activeSection = useMemo(
    () => sections.find((s) => s.id === activeSectionId) || null,
    [sections, activeSectionId]
  );

  const currentQuestion = useMemo(
    () => activeSection?.questions[qIndex] || null,
    [activeSection, qIndex]
  );

  // progresso geral (feito = política + prática preenchidos, se existirem)
  const isDone = (q: UIQuestion) => {
    const reqs = ["policy", "practice"].filter((k) => (q.parts as any)[k]);
    if (reqs.length === 0) return true;
    const a = answers[q.id];
    return reqs.every((k) => (a as any)?.[k]);
  };

  const progress = useMemo(() => {
    const total = flatQuestions.length || 1;
    const done = flatQuestions.filter(isDone).length;
    return { done, total, pct: Math.round((100 * done) / total) };
  }, [flatQuestions, answers]);

  const sectionComplete = (sec: Section) => sec.questions.every(isDone);

  /** ===== Persistência ===== */
  const saveField = async (control: UIQuestion, patch: Partial<QAState>) => {
    if (!sub || !control) return;

    setAnswers((prev) => ({
      ...prev,
      [control.id]: { ...prev[control.id], ...patch, ids: { ...(prev[control.id]?.ids || {}) } },
    }));

    const cur = { ...answers[control.id], ...patch };
    const ids = cur.ids || {};

    if (typeof patch.policy !== "undefined" && control.parts.policy) {
      const saved = await upsertAnswer({
        submission: sub.id,
        question: control.parts.policy,
        value: patch.policy ?? "",
      });
      ids.policy = saved.id;
    }

    if (typeof patch.practice !== "undefined" && control.parts.practice) {
      const saved = await upsertAnswer({
        submission: sub.id,
        question: control.parts.practice,
        value: patch.practice ?? "",
      });
      ids.practice = saved.id;
    }

    if (typeof patch.info !== "undefined" && control.parts.info) {
      const saved = await upsertAnswer({
        submission: sub.id,
        question: control.parts.info,
        value: patch.info ?? "",
      });
      ids.info = saved.id;
    }

    // opcional: espelhar score (quando existir)
    if (control.parts.score && (typeof patch.policy !== "undefined" || typeof patch.practice !== "undefined")) {
      const score = patch.practice || patch.policy || "";
      await upsertAnswer({ submission: sub.id, question: control.parts.score, value: score });
    }

    setAnswers((prev) => ({
      ...prev,
      [control.id]: { ...prev[control.id], ids },
    }));
  };

  // ===== Anexos (multi) =====
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const onPickFiles = async (control: UIQuestion, files: FileList | null) => {
    if (!sub || !control.parts.attachment || !files || files.length === 0) return;

    // garante answerId de attachment
    let answerId = answers[control.id]?.ids?.attachment;
    if (!answerId) {
      const created = await upsertAnswer({ submission: sub.id, question: control.parts.attachment, value: "" });
      answerId = created.id;
      setAnswers((prev) => ({
        ...prev,
        [control.id]: { ...(prev[control.id] || {}), ids: { ...(prev[control.id]?.ids || {}), attachment: answerId } },
      }));
    }

    // cria thumbs locais e envia em sequência
    const newThumbs: AttachmentThumb[] = [];
    for (const f of Array.from(files)) {
      const localUrl = URL.createObjectURL(f);
      newThumbs.push({ name: f.name, url: localUrl, isImage: isImageFilename(f.name) });
    }

    setAnswers((prev) => {
      const cur = prev[control.id] || {};
      const merged = [...(cur.attachments || []), ...newThumbs];
      return { ...prev, [control.id]: { ...cur, attachments: merged, attachmentName: merged[0]?.name ?? null } };
    });

    // upload real (um por vez)
    for (const f of Array.from(files)) {
      try {
        const updated = await patchAnswerAttachment(answerId!, f);
        // tenta trocar a primeira thumb com mesmo nome pelo retorno oficial
        if (updated?.attachment) {
          const serverName = String(updated.attachment).split("/").pop() || f.name;
          setAnswers((prev) => {
            const cur = prev[control.id] || {};
            const atts = (cur.attachments || []).map((t) =>
              t.name === f.name ? { ...t, name: serverName, url: String(updated.attachment), isImage: isImageFilename(serverName) } : t
            );
            return { ...prev, [control.id]: { ...cur, attachments: atts, attachmentName: atts[0]?.name ?? null } };
          });
        }
      } catch (e) {
        // se falhar, remove a thumb que criei
        setAnswers((prev) => {
          const cur = prev[control.id] || {};
          const atts = (cur.attachments || []).filter((t) => t.name !== f.name);
          return { ...prev, [control.id]: { ...cur, attachments: atts, attachmentName: atts[0]?.name ?? null } };
        });
      }
    }
  };

  /** ===== Navegação ===== */
  const gotoNext = () => {
    if (!activeSection) return;
    if (qIndex < activeSection.questions.length - 1) {
      setQIndex((i) => i + 1);
    } else {
      const idx = sections.findIndex((s) => s.id === activeSection.id);
      if (idx >= 0 && idx < sections.length - 1) {
        setActiveSectionId(sections[idx + 1].id); setQIndex(0);
      }
    }
  };

  const gotoPrev = () => {
    if (!activeSection) return;
    if (qIndex > 0) {
      setQIndex((i) => i - 1);
    } else {
      const idx = sections.findIndex((s) => s.id === activeSection.id);
      if (idx > 0) {
        const prevSec = sections[idx - 1]; setActiveSectionId(prevSec.id); setQIndex(prevSec.questions.length - 1);
      }
    }
  };

  /** ===== DotMap (roxo, numerado) ===== */
  const sectionDots = useMemo(() => {
    if (!activeSection) return [];
    return activeSection.questions.map((q, i) => {
      const a = answers[q.id];
      return {
        idx: i,
        id: q.id,
        done: isDone(q),
        hasAttachment: !!(a?.attachments && a.attachments.length > 0) || !!a?.attachmentName,
      };
    });
  }, [activeSection, answers]);

  const Dot: React.FC<{
    index: number;
    active: boolean;
    done: boolean;
    hasAttachment: boolean;
    onClick: () => void;
  }> = ({ index, active, done, hasAttachment, onClick }) => (
    <button
      onClick={onClick}
      title={`Controle ${index + 1}`}
      className={[
        "relative h-8 w-8 rounded-full border transition",
        done ? "bg-violet-600 border-violet-600 text-white" : "bg-card border-border text-muted-foreground",
        active ? "ring-2 ring-violet-400 scale-105" : "",
        "flex items-center justify-center text-[11px] font-medium"
      ].join(" ")}
    >
      {index + 1}
      {done && (
        <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-white text-violet-600 border border-violet-200 flex items-center justify-center">
          <Check className="h-3 w-3" />
        </span>
      )}
      {hasAttachment && <span className="absolute -bottom-1 -right-1 text-[10px]">📎</span>}
    </button>
  );

  /** ===== Render ===== */
  return (
    <AppShell>
      <div className="p-4 md:p-6 max-w-screen-2xl mx-auto">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">
              {template?.name ?? "NIST CSF 2.0"} {template?.version ? `· v${template.version}` : ""}
            </h1>
            <p className="text-sm text-muted-foreground">
              {sub?.framework?.name} — Status:{" "}
              <b>
                {sub?.status === "draft" ? "Rascunho" :
                 sub?.status === "in_review" ? "Em análise" :
                 sub?.status === "pending" ? "Pendente" :
                 sub?.status === "submitted" ? "Concluído" : "Arquivado"}
              </b>
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isReadOnly && (
              <button
                onClick={async () => { if (!sub) return; const u = await startReviewSubmission(sub.id); setSub(u); }}
                className="rounded-md border border-border bg-card px-3 py-1.5 text-sm hover:bg-muted"
              >
                Enviar para análise
              </button>
            )}
            {!isReadOnly && (
              <button
                onClick={async () => { if (!sub) return; const u = await submitSubmission(sub.id); setSub(u); }}
                className="rounded-md bg-primary text-white px-3 py-1.5 text-sm hover:opacity-90"
              >
                Concluir
              </button>
            )}
          </div>
        </div>

        {/* progresso geral */}
        <div className="mb-6 rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progresso: {progress.done}/{progress.total}</span>
            <span className="font-medium">{progress.pct}%</span>
          </div>
          <div className="mt-2 h-2 w-full rounded bg-muted overflow-hidden">
            <div className="h-2 bg-primary" style={{ width: `${progress.pct}%` }} />
          </div>
        </div>

        {loading && <p className="text-sm">Carregando…</p>}
        {err && <p className="text-sm text-red-600">{err}</p>}

        {!loading && !err && sections.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* sidebar com domínios + dot map */}
            <aside className="lg:col-span-4 xl:col-span-3">
              <div className="rounded-xl border border-border bg-card p-3">
                <ul className="space-y-1">
                  {sections.map((s) => {
                    const active = s.id === activeSectionId;
                    const complete = sectionComplete(s);
                    return (
                      <li key={s.id}>
                        <button
                          onClick={() => { setActiveSectionId(s.id); setQIndex(0); }}
                          className={`w-full text-left px-3 py-2 rounded-lg border transition ${
                            active ? "bg-primary/10 border-primary/30" : "bg-card border-border hover:bg-muted"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-sm">{s.title}</span>
                            <span className={`text-xs rounded-full px-2 py-0.5 border ${
                              complete ? "bg-violet-50 text-violet-700 border-violet-200"
                                       : "bg-amber-50 text-amber-700 border-amber-200"
                            }`}>
                              {complete ? "✔" : `${s.questions.filter(isDone).length}/${s.questions.length}`}
                            </span>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>

                {/* Dot map do domínio ativo (roxo) */}
                {activeSection && (
                  <div className="mt-4">
                    <div className="mb-2 text-xs text-muted-foreground">
                      Controles em {activeSection.title}
                    </div>
                    <div className="grid grid-cols-6 gap-2">
                      {sectionDots.map((d) => (
                        <Dot
                          key={d.id}
                          index={d.idx}
                          active={activeSection.questions[qIndex]?.id === d.id}
                          done={d.done}
                          hasAttachment={d.hasAttachment}
                          onClick={() => {
                            const idx = activeSection.questions.findIndex((q) => q.id === d.id);
                            if (idx >= 0) setQIndex(idx);
                          }}
                        />
                      ))}
                    </div>
                    <div className="mt-3 flex items-center gap-3 text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><span className="h-2 w-2 inline-block rounded-full bg-violet-600" /> completo</span>
                      <span className="inline-flex items-center gap-1"><span className="h-2 w-2 inline-block rounded-full border border-border bg-card" /> pendente</span>
                      <span className="inline-flex items-center gap-1">📎 com anexo</span>
                    </div>
                  </div>
                )}
              </div>
            </aside>

            {/* conteúdo perguntas */}
            <section className="lg:col-span-8 xl:col-span-9">
              {currentQuestion ? (
                <div className="rounded-xl border border-border bg-card p-4 md:p-5">
                  <div className="mb-2 text-xs text-muted-foreground">
                    {activeSection?.title} · {qIndex + 1} de {activeSection?.questions.length}
                  </div>
                  <h2 className="text-base md:text-lg font-medium">
                    {currentQuestion.code}: {currentQuestion.prompt}
                  </h2>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Política */}
                    <div>
                      <label className="block text-sm mb-1">Política</label>
                      <select
                        disabled={isReadOnly || !currentQuestion.parts.policy}
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                        value={answers[currentQuestion.id]?.policy ?? ""}
                        onChange={(e) => saveField(currentQuestion, { policy: e.target.value })}
                      >
                        <option value="" disabled>Selecione</option>
                        <option value="Inicial">1 - Inicial</option>
                        <option value="Repetido">2 - Repetido</option>
                        <option value="Definido">3 - Definido</option>
                        <option value="Gerenciado">4 - Gerenciado</option>
                        <option value="Otimizado">5 - Otimizado</option>
                      </select>
                    </div>

                    {/* Prática */}
                    <div>
                      <label className="block text-sm mb-1">Prática</label>
                      <select
                        disabled={isReadOnly || !currentQuestion.parts.practice}
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                        value={answers[currentQuestion.id]?.practice ?? ""}
                        onChange={(e) => saveField(currentQuestion, { practice: e.target.value })}
                      >
                        <option value="" disabled>Selecione</option>
                        <option value="Inicial">1 - Inicial</option>
                        <option value="Repetido">2 - Repetido</option>
                        <option value="Definido">3 - Definido</option>
                        <option value="Gerenciado">4 - Gerenciado</option>
                        <option value="Otimizado">5 - Otimizado</option>
                      </select>
                    </div>
                  </div>

                  {/* info */}
                  <div className="mt-4">
                    <label className="block text-sm mb-1">Informações adicionais</label>
                    <textarea
                      disabled={isReadOnly || !currentQuestion.parts.info}
                      value={answers[currentQuestion.id]?.info ?? ""}
                      onChange={(e) => saveField(currentQuestion, { info: e.target.value })}
                      rows={3}
                      className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                    />
                  </div>

                  {/* anexos: botão de ícone + input invisível + galeria */}
                  <div className="mt-4">
                    <div className="flex items-center gap-2">
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        className="hidden"
                        onChange={(e) => onPickFiles(currentQuestion, e.target.files)}
                        disabled={isReadOnly || !currentQuestion.parts.attachment}
                      />
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isReadOnly || !currentQuestion.parts.attachment}
                        className="inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-sm text-violet-700 hover:bg-violet-100 disabled:opacity-60"
                        title="Adicionar anexos"
                      >
                        <Paperclip className="h-4 w-4" />
                        Anexar
                      </button>
                    </div>

                    {/* galeria */}
                    {answers[currentQuestion.id]?.attachments && answers[currentQuestion.id]!.attachments!.length > 0 && (
                      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {answers[currentQuestion.id]!.attachments!.map((att, idx) => (
                          <div key={`${att.name}-${idx}`} className="group rounded-lg border border-border bg-card overflow-hidden">
                            <div className="h-24 w-full flex items-center justify-center bg-muted/40">
                              {att.isImage ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img src={att.url} alt={att.name} className="h-full w-full object-cover" />
                              ) : (
                                <div className="flex flex-col items-center text-muted-foreground">
                                  <FileIcon className="h-8 w-8" />
                                  <span className="text-[10px] mt-1 uppercase">{att.name.split(".").pop()}</span>
                                </div>
                              )}
                            </div>
                            <div className="px-2 py-1.5 text-xs truncate" title={att.name}>
                              {att.name}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* navegação */}
                  <div className="mt-6 flex items-center justify-between">
                    <button
                      onClick={gotoPrev}
                      disabled={!activeSection || (activeSection && qIndex === 0 && sections.findIndex((s) => s.id === activeSection.id) === 0)}
                      className="rounded-md border border-border bg-card px-3 py-1.5 text-sm disabled:opacity-60"
                    >
                      Anterior
                    </button>
                    <div className="text-xs text-muted-foreground">
                      {qIndex + 1} / {activeSection?.questions.length}
                    </div>
                    <button
                      onClick={gotoNext}
                      className="rounded-md border border-border bg-card px-3 py-1.5 text-sm"
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Selecione uma seção para começar.</p>
              )}
            </section>
          </div>
        )}

        {!loading && !err && sections.length === 0 && (
          <p className="text-sm text-muted-foreground">Este template ainda não possui perguntas mapeadas.</p>
        )}
      </div>
    </AppShell>
  );
}
