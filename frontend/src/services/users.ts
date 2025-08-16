// src/services/users.ts
import { api } from "@/lib/apiClient";

export type Role = "gestor" | "analista" | "cliente" | "subcliente";

export type UserListItem = {
  id: number;
  nome: string;
  email: string;
  role: Role | string;
  is_active: boolean;

  // Compat: backend atual usa "empresas" (TextField). Em alguns lugares antigos pode vir "empresa".
  empresas?: string | null;
  empresa?: string | null;       // compat legado: se vier, normalizamos em list/get

  // campos relacionais opcionais (se o serializer expuser):
  cliente?: number | null;
  gestor_referente?: number | null;
  formularios_ids?: number[];
};

export type ListUsersParams = {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean | null; // null = todos
};

export type ListUsersResponse = { results: UserListItem[]; count: number };

export async function listUsers(params: ListUsersParams = {}): Promise<ListUsersResponse> {
  const q = new URLSearchParams();
  if (params.page) q.set("page", String(params.page));
  if (params.page_size) q.set("page_size", String(params.page_size));
  if (params.search) q.set("search", params.search);
  if (typeof params.is_active === "boolean") q.set("is_active", String(params.is_active));

  const { data } = await api.get("/users/", { params: q });

  const arr: any[] = Array.isArray(data) ? data : data?.results ?? [];
  const results: UserListItem[] = arr.map((u) => ({
    ...u,
    // Normalização: garante "empresas" mesmo que o backend envie "empresa"
    empresas: u.empresas ?? u.empresa ?? null,
  }));

  const count =
    Array.isArray(data) ? arr.length : data?.count ?? results.length;

  return { results, count };
}

export async function setUserActive(id: number, is_active: boolean) {
  const { data } = await api.post<{ id: number; is_active: boolean }>(
    `/users/${id}/set_active/`,
    { is_active }
  );
  return data;
}

export async function deleteUser(id: number) {
  await api.delete(`/users/${id}/`);
}

// ---------- CRUD extra (get/create/update) ----------

export async function getUser(id: number): Promise<UserListItem> {
  const { data } = await api.get(`/users/${id}/`);
  // normaliza "empresas"
  return { ...data, empresas: data.empresas ?? data.empresa ?? null };
}

export type UserCreatePayload = {
  nome: string;
  email: string;
  role: Role;
  password?: string;                 // opcional conforme seu serializer
  cliente?: number | null;           // subcliente: id do cliente-pai (ou omitido se o backend força pelo ator)
  gestor_referente?: number | null;  // analista: opcional
  is_active?: boolean;               // se o serializer aceitar
  formularios_ids?: number[];        // ids de formulários
  empresas?: string | null;          // TextField (ex: "ACME S/A, Outras Ltda")
};

export async function createUser(payload: UserCreatePayload): Promise<UserListItem> {
  const { data } = await api.post("/users/", payload);
  return { ...data, empresas: data.empresas ?? data.empresa ?? null };
}

export type UserUpdatePayload = Partial<UserCreatePayload> & {
  password?: string; // alteração de senha opcional
};

export async function updateUser(id: number, payload: UserUpdatePayload): Promise<UserListItem> {
  const { data } = await api.patch(`/users/${id}/`, payload);
  return { ...data, empresas: data.empresas ?? data.empresa ?? null };
}

// ---------- extra ----------

export async function resendResetEmail(email: string, siteUrl?: string) {
  await api.post(`/auth/reenviar-email-token/`, {
    email,
    site_url:
      siteUrl || (typeof window !== "undefined" ? window.location.origin : ""),
  });
}
