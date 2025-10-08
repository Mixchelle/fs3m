"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { FiSearch, FiMoreVertical, FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight } from "react-icons/fi";
import { listAnalyses, type Analysis } from "@/services/analises";
import { useProtectedRoute } from "@/hooks/useProtectedRoute";
import AppShell from "@/components/layout/AppShell";

const fetcher = (_: string, params: any) => listAnalyses(params);

export default function AnalysesPage() {
  useProtectedRoute(["analyst", "analista", "manager", "gestor"]); // ajusta como preferir


  // estado de filtros/ordenação/paginação
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"todos" | "Finalizado" | "Em progresso" | "Aprovado">("todos");
  const [ordering, setOrdering] = useState<string>("nome_formulario"); // ou "-data_finalizado"
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(10);

  const { data, isLoading, mutate } = useSWR(["/analyses", { page, limit, search, status: status === "todos" ? undefined : status, ordering }], fetcher, {
    keepPreviousData: true,
  });

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / limit));

  useEffect(() => {
    // reset de página quando filtros mudam
    setPage(1);
  }, [search, status, ordering, limit]);

  const onOrderBy = (key: string) => {
    setOrdering((prev) => (prev === key ? `-${key}` : key));
  };

  const formatDate = (d?: string | Date | null) => {
    if (!d) return "-";
    const date = d instanceof Date ? d : new Date(d);
    if (isNaN(date.getTime())) return String(d);
    return date.toLocaleDateString();
  };

  const statusBadge = (rel: Analysis) => {
    if (rel.aprovado) return <span className="tag tag-approved">Aprovado Supervisor</span>;
    if (rel.finalizado) return <span className="tag tag-finished">Finalizado Análise</span>;
    return <span className="tag tag-progress">Em Progresso</span>;
  };

  return (
     <AppShell>
    <div className="analises-wrapper">
      <div className="analises-header">
        <h1>Análises</h1>
        <div className="summary">
          <div className="card">
            <p>Total em análise</p>
            <h2>{total}</h2>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="filters">
        <div className="search-box">
          <FiSearch />
          <input
            placeholder="Buscar por formulário ou cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="right-tools">
          <select value={status} onChange={(e) => setStatus(e.target.value as "todos" | "Finalizado" | "Em progresso" | "Aprovado")}>
            <option value="todos">Todos os status</option>
            <option value="Em progresso">Em progresso</option>
            <option value="Finalizado">Finalizado</option>
            <option value="Aprovado">Aprovado</option>
          </select>

          <select value={ordering} onChange={(e) => setOrdering(e.target.value)}>
            <option value="nome_formulario">Ordenar: Nome</option>
            <option value="nome_cliente">Ordenar: Empresa</option>
            <option value="data_finalizado">Ordenar: Data Finalização</option>
            <option value="data_aprovado">Ordenar: Data Aprovação</option>
            <option value="-data_finalizado">Ordenar: Data Finalização (desc)</option>
            <option value="-data_aprovado">Ordenar: Data Aprovação (desc)</option>
          </select>

          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            <option value={5}>5 / pág</option>
            <option value={10}>10 / pág</option>
            <option value={30}>30 / pág</option>
            <option value={50}>50 / pág</option>
          </select>
        </div>
      </div>

      {/* Tabela */}
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th onClick={() => onOrderBy("nome_formulario")}>Nome</th>
              <th onClick={() => onOrderBy("nome_cliente")}>Empresa</th>
              <th>Status</th>
              <th onClick={() => onOrderBy("data_finalizado")}>Data Finalização</th>
              <th onClick={() => onOrderBy("data_aprovado")}>Data Aprovação</th>
              <th onClick={() => onOrderBy("analista_responsavel")}>Analista</th>
              <th style={{ width: 120 }}>Ações</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7}>Carregando…</td></tr>
            ) : items.length ? (
              items.map((rel) => (
                <tr key={rel.id}>
                  <td><strong>{rel.nome_formulario}</strong></td>
                  <td>{rel.nome_cliente}</td>
                  <td>{statusBadge(rel)}</td>
                  <td>{formatDate(rel.data_finalizado)}</td>
                  <td>{formatDate(rel.data_aprovado)}</td>
                  <td>{rel.analista_responsavel ?? "-"}</td>
                  <td>
                    <div className="actions">
                      <Link className="btn btn-view" href={`/analyst/analises/${rel.id}`}>Ver</Link>
                      <div className="menu">
                        <button className="btn btn-more" title="Mais opções"><FiMoreVertical /></button>
                        {/* aqui depois você pode abrir dropdown com Aprovar / Importar Word / Exportar Word */}
                      </div>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={7}>Nenhum resultado encontrado.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      <div className="pagination">
        <button disabled={page === 1} onClick={() => setPage(1)} title="Primeira"><FiChevronsLeft /></button>
        <button disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))} title="Anterior"><FiChevronLeft /></button>

        <span>Página {page} de {totalPages}</span>

        <button disabled={page === totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} title="Próxima"><FiChevronRight /></button>
        <button disabled={page === totalPages} onClick={() => setPage(totalPages)} title="Última"><FiChevronsRight /></button>
      </div>
    </div>
    </AppShell>
  );
}
