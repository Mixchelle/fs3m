// src/services/frameworks.ts
import { api } from "@/lib/apiClient";
import type { Framework, TemplateDetail, DomainItem } from "@/types/frameworks.types";

/** Frameworks */
export async function listFrameworks() {
  const { data } = await api.get<Framework[]>("/frameworks/frameworks/");
    console.log('listFrameworks:', data)

  return data;
}

/** Templates */
export async function getTemplateDetail(id: number) {
  const { data } = await api.get<TemplateDetail>(`/frameworks/templates/${id}/`);
    console.log('getTemplateDetail:', 'id:', id, data)

  return data;
}

/** Domínios (por framework) */
export async function listDomainsByFramework(frameworkId: number) {
  // DRF pode (ou não) suportar ?framework=; garantimos no cliente
  const { data } = await api.get<DomainItem[]>("/frameworks/domains/");
  console.log('listDomainsByFramework:', data)
  return data.filter((d) => d.framework === frameworkId);
}
