import { api } from "@/lib/apiClient";

export async function listActionPlans(submissionId?: number) {
  const url = submissionId ? `/actionplans/?submission=${submissionId}` : "/actionplans/";
  const res = await api.get(url);
  return res.data;
}
