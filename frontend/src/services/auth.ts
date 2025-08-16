import { api } from "@/lib/apiClient";

export async function login(email: string, password: string) {
  const res = await api.post("/users/login/", { email, password });
  return res.data;
}

export async function me() {
  const res = await api.get("/users/me/");
  return res.data;
}
