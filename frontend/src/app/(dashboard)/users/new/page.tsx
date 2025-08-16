"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import { useAuth } from "@/contexts/AuthContext";

import { listFrameworks, Framework } from "@/services/frameworks";

import {
  createUser,
  listUsers,
  Role as RoleApi,         // seu service pode ter tipo próprio; aqui não usamos
  UserCreatePayload,
  UserListItem,
} from "@/services/users";

const FORM_OPCOES = [{ id: 201, label: "NIST 2.0 de Maturidade" }];
const PERMISSOES_OPCOES = [
  { key: "aprovar_relatorios", label: "Aprovar Relatórios" },
  { key: "criar_analistas", label: "Criar Novos Analistas" },
];

type RolePt = "gestor" | "analista" | "cliente" | "subcliente";
type LocalForm = UserCreatePayload & {
  empresa?: string;
  formularios_ids: number[];
  permissoes: string[];
  role: RolePt; // forçamos PT aqui
};

export default function NewUserPage() {
  const router = useRouter();
  const { user } = useAuth(); // agora vem com role em PT e permissoes[]

  const loggedRole = (user?.role || "guest").toString().toLowerCase();
  const perms = (user?.permissoes || []) as string[];
  const canCreateAnalyst = loggedRole === "gestor" || perms.includes("criar_analistas");
const [frameworks, setFrameworks] = useState<Framework[]>([]);
const [loadingFrameworks, setLoadingFrameworks] = useState(false);
const [fwError, setFwError] = useState<string | null>(null);
  // papéis visíveis conforme logado
  const allowedRoles: RolePt[] = useMemo(() => {
    if (loggedRole === "gestor") return ["gestor", "analista", "cliente", "subcliente"];
    if (loggedRole === "analista") return canCreateAnalyst ? ["analista", "cliente", "subcliente"] : ["cliente", "subcliente"];
    if (loggedRole === "cliente") return ["subcliente"];
    return ["cliente"]; // fallback
  }, [loggedRole, canCreateAnalyst]);

  const [form, setForm] = useState<LocalForm>({
    nome: "",
    email: "",
    role: allowedRoles[0] ?? "cliente",
    password: "",
    cliente: null,
    gestor_referente: null,
    is_active: true,
    empresa: "",
    formularios_ids: [],
    permissoes: [],
  });

  useEffect(() => {
  (async () => {
    setLoadingFrameworks(true);
    setFwError(null);
    try {
      const data = await listFrameworks();
      setFrameworks(data);
    } catch (e) {
      console.error(e);
      setFwError("Não foi possível carregar os frameworks.");
    } finally {
      setLoadingFrameworks(false);
    }
  })();
}, []);

  // garante que role atual sempre pertence ao allowedRoles
  useEffect(() => {
    setForm((f) => (allowedRoles.includes(f.role) ? f : { ...f, role: allowedRoles[0] }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowedRoles.join("|")]);

  // estados auxiliares
  const [errors, setErrors] = useState<{ empresa?: string; cliente?: string; gestor?: string }>({});
  const [saving, setSaving] = useState(false);
  const [clientOptions, setClientOptions] = useState<Array<Pick<UserListItem, "id" | "nome" | "email">>>([]);
  const [loadingClients, setLoadingClients] = useState(false);

  const isClientLogged = loggedRole === "cliente";
  const needsClientePai = form.role === "subcliente";
  const showEmpresa     = form.role === "cliente";
  const showPermissoes  = form.role === "analista";
  const showFormularios = form.role === "cliente" || form.role === "subcliente";
  const showGestorField = form.role === "analista";

  // se cliente logado e criando subcliente: vincula automaticamente
  useEffect(() => {
    if (isClientLogged && needsClientePai && user?.id) {
      setForm((f) => ({ ...f, cliente: user.id }));
    }
  }, [isClientLogged, needsClientePai, user?.id]);

  // para gestor/analista criando subcliente: carrega clientes
  useEffect(() => {
    if (!needsClientePai || isClientLogged) return;
    (async () => {
      setLoadingClients(true);
      try {
        const { results } = await listUsers({ page: 1, page_size: 1000, is_active: true });
        const opts = results
          .filter((u) => String(u.role).toLowerCase() === "cliente")
          .map((u) => ({ id: u.id, nome: u.nome, email: u.email }));
        setClientOptions(opts);
      } finally {
        setLoadingClients(false);
      }
    })();
  }, [needsClientePai, isClientLogged]);

  const inputCls =
    "w-full rounded-lg border border-border bg-card px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30 shadow-sm";

  const toggleFormId = (id: number) =>
    setForm((f) => ({
      ...f,
      formularios_ids: f.formularios_ids.includes(id)
        ? f.formularios_ids.filter((x) => x !== id)
        : [...f.formularios_ids, id],
    }));

  const togglePerm = (key: string) =>
    setForm((f) => ({
      ...f,
      permissoes: f.permissoes.includes(key)
        ? f.permissoes.filter((p) => p !== key)
        : [...f.permissoes, key],
    }));

  const validate = () => {
    const e: typeof errors = {};
    if (showEmpresa && !form.empresa?.trim()) e.empresa = "Informe a empresa.";
    if (needsClientePai && !form.cliente) e.cliente = "Selecione/defina o cliente pai.";
    if (showGestorField && !canCreateAnalyst) {
      e.gestor = "Você não tem permissão para criar analista.";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const onSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      await createUser(form);
      router.push("/users");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-screen-xl px-4 sm:px-6 lg:px-8 py-6">
        <form onSubmit={onSubmit} className="bg-card border border-border rounded-2xl shadow-sm p-6 md:p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-foreground">Novo usuário</h1>
            <p className="text-sm text-muted-foreground">As opções dependem do seu perfil.</p>
          </div>

          {/* PAPEL (segmented pelas regras) */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Papel</label>
            <div className="flex flex-wrap gap-2">
              {allowedRoles.map((role) => {
                const active = form.role === role;
                return (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, role }))}
                    className={`px-3 py-1.5 rounded-full text-sm border transition
                      ${active ? "bg-primary text-white border-transparent"
                               : "bg-card text-foreground border-border hover:bg-muted"}`}
                    aria-pressed={active}
                  >
                    {role}
                  </button>
                );
              })}
            </div>
            {form.role === "analista" && !canCreateAnalyst && (
              <p className="mt-2 text-xs text-red-600">
                Você não tem permissão para criar analista (requer <b>criar_analistas</b>).
              </p>
            )}
          </div>

          {/* GRID 2 colunas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Coluna esquerda */}
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium mb-1">Nome</label>
                <input className={inputCls} value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input type="email" className={inputCls} value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>

              {form.role === "cliente" && (
                <div>
                  <label className="block text-sm font-medium mb-1">Empresa</label>
                  <input className={inputCls} value={form.empresa || ""}
                    onChange={(e) => setForm({ ...form, empresa: e.target.value })}
                    placeholder="ex.: ACME S/A" />
                  {errors.empresa && <p className="mt-1 text-xs text-red-600">{errors.empresa}</p>}
                </div>
              )}

              {form.role === "subcliente" && (
                <div>
                  <label className="block text-sm font-medium mb-1">Cliente pai</label>
                  {isClientLogged ? (
                    <>
                      <input className={`${inputCls} opacity-60`} readOnly
                        value={`${user?.id ?? ""} — você mesmo`} />
                      <p className="mt-1 text-xs text-muted-foreground">
                        Como cliente logado, o subcliente será vinculado a você automaticamente.
                      </p>
                    </>
                  ) : (
                    <>
                      <select
                        className={inputCls}
                        value={form.cliente ?? ""}
                        onChange={(e) =>
                          setForm({ ...form, cliente: e.target.value ? Number(e.target.value) : null })
                        }
                      >
                        <option value="" disabled>
                          {loadingClients ? "Carregando clientes..." : "Selecione"}
                        </option>
                        {clientOptions.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.nome} — {c.email}
                          </option>
                        ))}
                      </select>
                      {errors.cliente && <p className="mt-1 text-xs text-red-600">{errors.cliente}</p>}
                    </>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-1">Senha (opcional)</label>
                <input type="password" className={inputCls} value={form.password ?? ""}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="definir agora ou depois" />
              </div>
            </div>

            {/* Coluna direita */}
            <div className="space-y-5">
              {/* Ativo */}
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <p className="text-sm font-medium">Ativo</p>
                  <p className="text-xs text-muted-foreground">Controle de ativação do usuário.</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={form.is_active ?? true}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  />
                  <div className="w-11 h-6 rounded-full bg-muted peer-checked:bg-emerald-500 transition-colors"></div>
                  <div className="absolute left-0.5 top-0.5 w-5 h-5 bg-card rounded-full shadow-sm transition-transform peer-checked:translate-x-5"></div>
                </label>
              </div>

              {/* Gestor referente (se analista) */}
              {form.role === "analista" && (
                <div className="rounded-lg border border-border p-4">
                  <label className="block text-sm font-medium mb-1">Gestor referente (ID)</label>
                  <input
                    type="number"
                    className={inputCls}
                    value={form.gestor_referente ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        gestor_referente: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    placeholder="ex.: 1"
                  />
                  {errors.gestor && <p className="mt-1 text-xs text-red-600">{errors.gestor}</p>}
                  <p className="mt-1 text-xs text-muted-foreground">
                    Informe o ID do gestor ao qual o analista estará vinculado.
                  </p>
                </div>
              )}

              {/* Permissões (apenas analista) */}
              {showPermissoes && (
                <fieldset className="rounded-lg border border-border p-4">
                  <legend className="px-2 text-sm font-medium">Permissões</legend>
                  <div className="mt-2 space-y-2">
                    {PERMISSOES_OPCOES.map((p) => (
                      <label key={p.key} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          checked={form.permissoes.includes(p.key)}
                          onChange={() => togglePerm(p.key)}
                        />
                        <span>{p.label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}

              {/* Formulários (cliente/subcliente) */}
           {showFormularios && (
  <fieldset className="rounded-lg border border-border p-4">
    <legend className="px-2 text-sm font-medium">Formulários permitidos (frameworks)</legend>

    {loadingFrameworks && <p className="mt-2 text-sm text-muted-foreground">Carregando frameworks…</p>}
    {fwError && <p className="mt-2 text-sm text-red-600">{fwError}</p>}

    {!loadingFrameworks && !fwError && (
      <div className="mt-2 space-y-2">
        {frameworks.map((fw) => (
          <label key={fw.id} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4"
              checked={form.formularios_ids.includes(fw.id)}
              onChange={() =>
                setForm((f) => ({
                  ...f,
                  formularios_ids: f.formularios_ids.includes(fw.id)
                    ? f.formularios_ids.filter((x) => x !== fw.id)
                    : [...f.formularios_ids, fw.id],
                }))
              }
            />
            <span>
              {fw.name} <span className="text-xs text-muted-foreground">({fw.version})</span>
            </span>
          </label>
        ))}

        {frameworks.length === 0 && (
          <p className="text-sm text-muted-foreground">Nenhum framework disponível.</p>
        )}
      </div>
    )}
  </fieldset>
)}

            </div>
          </div>

          {/* Ações */}
          <div className="mt-8 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => router.push("/users")}
              className="inline-flex items-center justify-center rounded-md border border-border bg-card px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-white text-sm font-medium hover:opacity-90 disabled:opacity-60"
            >
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </AppShell>
  );
}
