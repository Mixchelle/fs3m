"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { listUsers, setUserActive, UserListItem } from "@/services/users";
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";
import AppShell from "@/components/layout/AppShell";
import RowActions from "@/components/users/RowActions";
import { deleteUser, resendResetEmail } from "@/services/users";
export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"todos" | "ativo" | "inativo">("todos");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const is_active = status === "todos" ? null : status === "ativo";
      const { results, count } = await listUsers({ page, page_size: pageSize, search, is_active });
      setUsers(results);
      setTotal(count);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); /* eslint-disable-next-line */ }, [page, pageSize, status]);
  useEffect(() => {
    const t = setTimeout(() => { setPage(1); fetchData(); }, 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [search]);

  const toggleActive = async (u: UserListItem) => {
    await setUserActive(u.id, !u.is_active);
    fetchData();
  };

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-screen-2xl px-4 sm:px-6 lg:px-8 p-6">
        <div className="bg-card rounded-xl shadow-sm border border-border p-6">
          {/* Cabeçalho */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-semibold text-foreground">Cadastros</h1>
            <Link
              href="/users/new"
              className="px-4 py-2 rounded-md bg-primary text-white text-sm font-medium hover:opacity-90"
            >
              + NOVO CADASTRO
            </Link>
          </div>

          {/* Filtros */}
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <p className="text-sm text-muted-foreground">Total: {total}</p>

            {/* busca */}
            <div className="flex items-center gap-2 border border-border rounded-md px-3 py-2 bg-card">
              <svg
                className="h-4 w-4 text-muted-foreground"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.5 4.5a7.5 7.5 0 0012.15 12.15z" />
              </svg>
              <input
                className="bg-transparent outline-none text-sm placeholder:text-muted-foreground text-foreground"
                placeholder="Buscar por nome, e-mail..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {/* status */}
            <div className="ml-auto">
              <select
                className="text-sm border border-border rounded-md px-3 py-2 bg-card text-foreground"
                value={status}
                onChange={(e) => { setStatus(e.target.value as any); setPage(1); }}
              >
                <option value="todos">Todos os status</option>
                <option value="ativo">Ativo</option>
                <option value="inativo">Inativo</option>
              </select>
            </div>
          </div>

          {/* Tabela */}
 <div className="rounded-lg border border-border overflow-x-auto">
            {loading ? (
              <div className="p-6 text-sm text-muted-foreground">Carregando...</div>
            ) : (
     <table className="w-full min-w-[860px] text-sm">
                <thead className="bg-muted/60 text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">NOME</th>
                    <th className="px-4 py-3 text-left font-medium">EMAIL</th>
                    <th className="px-4 py-3 text-left font-medium">PAPEL</th>
                    <th className="px-4 py-3 text-left font-medium">STATUS</th>
                    <th className="px-4 py-3 text-center font-medium">AÇÕES</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="bg-card border-t border-border">
                      <td className="px-4 py-3 font-medium text-foreground">{u.nome}</td>
                      <td className="px-4 py-3 text-foreground/90">{u.email}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold text-white
                          ${String(u.role).toLowerCase()==="gestor" ? "bg-amber-500"
                          : String(u.role).toLowerCase()==="analista" ? "bg-blue-500"
                          : String(u.role).toLowerCase()==="subcliente" ? "bg-orange-500"
                          : "bg-emerald-500"}`}>
                          {String(u.role)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-medium px-2 py-1 rounded
                            ${u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                            {u.is_active ? "Ativo" : "Inativo"}
                          </span>
                          {/* switch dark-aware */}
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={u.is_active}
                              onChange={() => toggleActive(u)}
                            />
                            <div className="w-10 h-5 rounded-full transition-colors bg-muted peer-checked:bg-emerald-500"></div>
                            <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-card rounded-full shadow-sm transition-transform peer-checked:translate-x-5"></div>
                          </label>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                                   <RowActions
                            id={u.id}
                            email={u.email}
                            onDeleted={fetchData}
                            onResent={() => {/* opcional: toast */}}
                            deleteUserFn={deleteUser}
                            resendFn={(email) => resendResetEmail(email)}
                        />
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">
                        Nenhum usuário encontrado.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>

          {/* Paginação */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2 text-sm">
              <span>Exibir:</span>
              <select
                className="border border-border rounded-md px-2 py-1 bg-card text-foreground"
                value={pageSize}
                onChange={(e) => { setPage(1); setPageSize(Number(e.target.value)); }}
              >
                {[5, 10, 20, 50].map((n) => (<option key={n} value={n}>{n}</option>))}
              </select>
              <span>por página</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-2 py-1 border border-border rounded-md bg-card disabled:opacity-50"
                title="Página anterior"
              >
                <FiChevronLeft />
              </button>
              <span>Página {page} de {totalPages}</span>
              <button
                onClick={() => setPage((p) => (p < totalPages ? p + 1 : p))}
                disabled={page >= totalPages}
                className="px-2 py-1 border border-border rounded-md bg-card disabled:opacity-50"
                title="Próxima página"
              >
                <FiChevronRight />
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
