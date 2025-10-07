// services/analises.ts
import apiClient from "@/lib/apiClient";

export type Analysis = {
  id: string | number;
  nome_formulario: string;
  nome_cliente: string;
  status?: "Em progresso" | "Finalizado" | "Aprovado"; // ajuste conforme API
  aprovado?: boolean;
  finalizado?: boolean;
  data_finalizado?: string | Date | null;
  data_aprovado?: string | Date | null;
  analista_responsavel?: string | null;
};

export type ListAnalysesResponse = {
  total: number;
  page: number;
  limit: number;
  items: Analysis[];
};

export type ListAnalysesParams = {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;    // "todos" | "Finalizado" | "Em progresso" | "Aprovado"
  ordering?: string;  // ex: "nome_formulario" ou "-data_finalizado"
};

export async function listAnalyses(params: ListAnalysesParams = {}) {
  const res = await apiClient.get<ListAnalysesResponse>("/analyses", { params });
  return res.data;
}
