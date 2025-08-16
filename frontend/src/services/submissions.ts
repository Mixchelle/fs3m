import { api } from "@/lib/apiClient";
import { AnswerItem, SubmissionItem, SubmissionRead, UpsertAnswerPayload } from "@/types/submissions.types";

/** ===== Tipos ===== */


/** ===== Submissions (dashboard/workflow) ===== */

export async function ensureClientSubmission(clientId: number, templateSlug: string) {
  const { data } = await api.get(`/responses/dashboard/${clientId}/`, {
    params: { ensure: "1", template: templateSlug },
  });
  return data as {
    client_id: number;
    submission: SubmissionItem | null; // já hidratada pelo backend
    retrieved_at: string;
  };
}

export async function submitSubmission(submissionId: number) {
  const { data } = await api.post(`/responses/submissions/${submissionId}/submit/`);
  const hydrated = await hydrateSubmissions([data]);
  return hydrated[0];
}

export async function startReviewSubmission(submissionId: number) {
  // tenta action dedicada; se não existir, faz PATCH no status
  try {
    const { data } = await api.post(`/responses/submissions/${submissionId}/start_review/`, {});
    const hydrated = await hydrateSubmissions([data]);
    return hydrated[0];
  } catch {
    const { data } = await api.patch(`/responses/submissions/${submissionId}/`, { status: "in_review" });
    const hydrated = await hydrateSubmissions([data]);
    return hydrated[0];
  }
}

export async function listClientSubmissions(clientId: number) {
  const { data } = await api.get(`/responses/submissions/`, { params: { customer: clientId } });
  const raw: SubmissionRead[] = Array.isArray(data) ? data : (data?.results ?? []);
  const hydrated = await hydrateSubmissions(raw);
  return hydrated;
}

// Apenas busca os templates e usa o framework aninhado no template
async function hydrateSubmissions(items: SubmissionRead[]): Promise<SubmissionItem[]> {
  if (items.length === 0) return [];

  const templateIds = [...new Set(items.map((i) => i.template).filter(Boolean))] as number[];

  const templatesArr = await Promise.all(
    templateIds.map((id) => api.get(`/frameworks/templates/${id}/`).then((r) => r.data))
  );
  const templatesMap = new Map<number, any>(templatesArr.map((t: any) => [t.id, t]));

  return items.map((i) => {
    const tpl = templatesMap.get(i.template);

    const template = tpl
      ? { id: tpl.id, name: tpl.name, slug: tpl.slug, version: tpl.version }
      : { id: i.template, name: `Template #${i.template}`, slug: `template-${i.template}`, version: "" };

    const fw = tpl?.framework;
    const framework = fw
      ? { id: fw.id, name: fw.name, slug: fw.slug, version: fw.version }
      : { id: i.framework, name: `Framework #${i.framework}`, slug: `framework-${i.framework}`, version: "" };

    return {
      id: i.id,
      status: i.status,
      progress: i.progress,
      version: i.version,
      created_at: i.created_at,
      updated_at: i.updated_at,
      template,
      framework,
    };
  });
}

/** ===== Answers (CRUD/Upload) ===== */

export async function getSubmissionAnswers(submissionId: number) {
  const { data } = await api.get("/responses/answers/", {
    params: { submission: submissionId },
  });
  return (Array.isArray(data) ? data : data?.results || []) as AnswerItem[];
}

export async function upsertAnswer(payload: UpsertAnswerPayload) {
  // 1) tenta endpoint de upsert
  try {
    const { data } = await api.post<AnswerItem>("/responses/answers/upsert/", payload);
    return data;
  } catch {
    // 2) tenta criar normal
    try {
      const { data } = await api.post<AnswerItem>("/responses/answers/", payload);
      return data;
    } catch (err) {
      // 3) fallback: busca existente e patch
      const { data: existingList } = await api.get("/responses/answers/", {
        params: { submission: payload.submission, question: payload.question },
      });
      const list = (Array.isArray(existingList) ? existingList : existingList?.results) as AnswerItem[] | undefined;
      const existing = list?.[0];
      if (!existing) throw err;
      const { data } = await api.patch<AnswerItem>(`/responses/answers/${existing.id}/`, payload);
      return data;
    }
  }
}

export async function patchAnswerAttachment(answerId: number, file: File) {
  const form = new FormData();
  // ajuste o nome do campo se seu serializer usar outro (ex.: "file")
  form.append("attachment", file);

  const { data } = await api.patch<AnswerItem>(`/responses/answers/${answerId}/`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
