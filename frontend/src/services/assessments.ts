import { api } from "@/lib/apiClient";

export async function runAssessment(submissionId: number, type = "maturity-1-5") {
  const res = await api.post(`/assessments/run/${submissionId}/?type=${type}`);
  return res.data;
}

export async function getAssessment(assessmentId: number) {
  const res = await api.get(`/assessments/${assessmentId}/`);
  return res.data;
}
