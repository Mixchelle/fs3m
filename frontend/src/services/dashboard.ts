import apiClient from "@/lib/apiClient";

export type DashboardSubmission = {
  id: number;
  status: string;
  progress: number;
  version: number;
  created_at: string;
  updated_at: string;
  template: { id: number; name: string; slug: string; version: string };
  framework: { id: number; slug: string; name: string; version: string };
};

export async function getClientDashboardEnsure(clientId: number, templateSlug = "nist-csf-2-0") {
  const { data } = await apiClient.get(
    `/responses/dashboard/${clientId}/`,
    { params: { ensure: "1", template: templateSlug } }
  );
  return data as {
    client_id: number;
    submission: DashboardSubmission | null;
    retrieved_at: string;
  };
}
