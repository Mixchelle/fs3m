"use client";

import Link from "next/link";
import { FiUser } from "react-icons/fi";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  FiLogOut,
  FiHome,
  FiBarChart2,
  FiFileText,
  FiUsers,
  FiMenu,
} from "react-icons/fi";
import "@/styles/base/sideBar.css";
import { useAuth } from "@/contexts/AuthContext";

type Role = "client" | "analyst" | "manager" | "guest" | "cliente" | "analista" | "gestor" | "subcliente";

export default function Sidebar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname() || "/";

  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    try {
      const saved = localStorage.getItem("sidebarCollapsed");
      return saved ? JSON.parse(saved) : false;
    } catch {
      return false;
    }
  });

  const [isMobile, setIsMobile] = useState<boolean>(false);
  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= 768);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // persiste e sincroniza com o <body> (CSS vars)
  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", JSON.stringify(isCollapsed));
    if (typeof document !== "undefined") {
      document.body.classList.toggle("sidebar-collapsed", isCollapsed);
    }
  }, [isCollapsed]);

  const menuItems = useMemo(() => {
    const r = (user?.role || "guest").toString().toLowerCase();
    if (r === "cliente" || r === "client" || r === "subcliente") {
      return [
        { name: "Home", icon: <FiHome size={20} />, path: "/client" },
        { name: "Formulário", icon: <FiFileText size={20} />, path: "/client/formulario" },
        { name: "Relatórios", icon: <FiFileText size={20} />, path: "/client/relatorios" },
      ];
    }
    if (r === "analista" || r === "analyst") {
      return [
        { name: "Home", icon: <FiHome size={20} />, path: "/analyst" },
        { name: "Análises", icon: <FiBarChart2 size={20} />, path: "/analyst/analises" },
        { name: "Relatórios", icon: <FiFileText size={20} />, path: "/analyst/relatorios" },
        { name: "Cadastros", icon: <FiUsers size={20} />, path: "/analyst/cadastros" },
      ];
    }
    if (r === "gestor" || r === "manager") {
      return [
        { name: "Home", icon: <FiHome size={20} />, path: "/manager" },
        { name: "Análises", icon: <FiBarChart2 size={20} />, path: "/manager/analises" },
        { name: "Relatórios", icon: <FiFileText size={20} />, path: "/manager/relatorios" },
        { name: "Cadastros", icon: <FiUsers size={20} />, path: "/manager/cadastros" },
        { name: "Usuários", icon: <FiUsers size={20} />, path: "/users" }

      ];
    }
    return [];
  }, [user?.role]);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  // MOBILE: footer nav
  if (isMobile) {
    const active = (to: string) => pathname === to || pathname.startsWith(to + "/");
    return (
      <nav className="mobile-footer-nav" role="navigation" aria-label="Menu inferior">
        {menuItems.map((item, idx) => (
          <Link
            key={idx}
            href={item.path}
            className={`footer-icon ${active(item.path) ? "active" : ""}`}
            aria-label={item.name}
          >
            {item.icon}
          </Link>
        ))}
        <button onClick={handleLogout} className="footer-icon logout" aria-label="Sair">
          <FiLogOut size={22} />
        </button>
      </nav>
    );
  }

  // DESKTOP
  const activeMatch = (to: string) => pathname === to || pathname.startsWith(to + "/");

  return (
    <aside
      id="sidebar"
      className={`sidebar ${isCollapsed ? "collapsed" : ""}`}
      role="navigation"
      aria-label="Menu lateral"
    >
      {/* Topo / botão */}
      <div className="sidebar-header">
        {/* <button
          className="menu-button"
          onClick={() => setIsCollapsed((c) => !c)}
          aria-pressed={isCollapsed}
          aria-label={isCollapsed ? "Expandir menu" : "Recolher menu"}
          title={isCollapsed ? "Expandir" : "Recolher"}
        >
          <FiMenu />
        </button> */}
      </div>

      {/* Usuário */}
      {!isCollapsed && (
        <div className="user-section">
          <div className="user-avatar flex items-center justify-center" aria-hidden="true">
            <FiUser size={32} color="#FF7900" />
          </div>
          <p className="user-name">{user?.name || (user as any)?.nome || "Usuário"}</p>
          <p className="user-type">
            {(() => {
              const r = (user?.role || "").toString().toLowerCase();
              if (r === "cliente" || r === "client") return "Cliente";
              if (r === "subcliente") return "Subcliente";
              if (r === "analista" || r === "analyst") return "Analista";
              if (r === "gestor" || r === "manager") return "Gestor";
              return "—";
            })()}
          </p>
        </div>
      )}

      {/* Links */}
      <nav className="menu-items">
        {menuItems.map((item, index) => (
          <Link
            key={index}
            href={item.path}
            className={`menu-link ${activeMatch(item.path) ? "active" : ""}`}
            aria-current={activeMatch(item.path) ? "page" : undefined}
          >
            {item.icon}
            {!isCollapsed && <span>{item.name}</span>}
          </Link>
        ))}
      </nav>

      {/* Logout */}
      <div className="logout-section">
        <button className="logout-button" onClick={handleLogout} aria-label="Sair da conta">
          <FiLogOut size={20} aria-hidden="true" />
          {!isCollapsed && <span>Sair</span>}
        </button>
      </div>
    </aside>
  );
}
