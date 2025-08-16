import { api } from "@/lib/apiClient";

export async function listRecommendationsBySubmission(submissionId: number) {
  const res = await api.get(`/recommendations/?submission=${submissionId}`);
  return res.data;
}
