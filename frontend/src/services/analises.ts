// services/analises.ts

import { api } from "@/lib/apiClient";

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


export interface Submission {
  id: number | string;
  public_title: string;
  name_internal: string;
  status: "draft" | "active" | "paused" | string;
  created_by?: string | null;
  created: string; // ISO
  // adicione outros campos se existirem no backend
}

export interface PagedResponse<T> {
  total: number;
  page: number;
  limit: number;
  items: T[];
}

const BASE_PATH = "/responses/submissions/";

export async function listAnalises(page = 1, limit = 10) {
  const { data } = await api.get<PagedResponse<Submission>>(BASE_PATH, {
    params: { page, limit },
  });
  return data;
}

export async function getAnalise(id: number | string) {
  const { data } = await api.get<Submission>(`${BASE_PATH}${id}/`);
  return data;
}

export async function createAnalise(payload: Partial<Submission>) {
  const { data } = await api.post<Submission>(BASE_PATH, payload);
  return data;
}

export async function updateAnalise(id: number | string, payload: Partial<Submission>) {
  const { data } = await api.patch<Submission>(`${BASE_PATH}${id}/`, payload);
  return data;
}

export async function deleteAnalise(id: number | string) {
  await api.delete(`${BASE_PATH}${id}/`);
}