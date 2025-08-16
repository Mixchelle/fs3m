"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

const PUBLIC_ROUTES = new Set<string>(["/login", "/auth/login", "/(auth)/login"]);

export function useProtectedRoute() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    const isPublic = [...PUBLIC_ROUTES].some((p) => pathname.endsWith(p) || pathname === p);
    if (!user && !isPublic) router.replace("/login");
  }, [user, loading, pathname, router]);

  return { user, loading };
}
