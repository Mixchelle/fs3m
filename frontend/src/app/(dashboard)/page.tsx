"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useProtectedRoute } from "@/hooks/useProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

export default function DashboardLanding() {
  const router = useRouter();
  const { loading } = useProtectedRoute();
  const { user } = useAuth();

  useEffect(() => {
    if (loading) return;

    // sem user -> volta pro login
    if (!user) {
      router.replace("/login");
      return;
    }

    // aceita PT (padrão do seu AuthContext) e EN (fallback)
    const routeByRole: Record<string, string> = {
      cliente: "/client",
      subcliente: "/client", // ajuste se tiver uma área própria
      analista: "/analyst",
      gestor: "/manager",
      // fallbacks em EN, caso algo escape da normalização
      client: "/client",
      subclient: "/client",
      analyst: "/analyst",
      manager: "/manager",
      admin: "/manager",
      administrator: "/manager",
    };

    const key = (user.role || "").toLowerCase();
    const target = routeByRole[key] ?? "/client";
    router.replace(target);
  }, [loading, user, router]);

  return (
    <div className="min-h-[60vh] grid place-items-center">
      <p className="text-neutral-500">Carregando seu painel…</p>
    </div>
  );
}
