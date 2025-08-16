export type Role = "client" | "analyst" | "manager" | "guest";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
};
