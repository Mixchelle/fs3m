"use client";

import { useState, useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import logo from "../../../public/assets/f3smlogo.png";
import { MoreVertical, UserRound, KeyRound } from "lucide-react";
import "@/styles/base/Header.css";
import "@/styles/base/ThemeSwitch.css"; // <-- seu CSS do switch

interface HeaderProps {
  className?: string;
}

type ThemeMode = "light" | "dark";

const Header: React.FC<HeaderProps> = ({ className }) => {
  const [pageTitle, setPageTitle] = useState("Home");
  const [timeLeft, setTimeLeft] = useState(45 * 60);
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>("light");

  const router = useRouter();
  const pathname = usePathname();
  const menuRef = useRef<HTMLDivElement | null>(null);

  // título pela rota
  useEffect(() => {
    const pathSegments = pathname.split("/").filter(Boolean);
    const last = pathSegments.length ? pathSegments[pathSegments.length - 1] : "Home";
    setPageTitle(last.charAt(0).toUpperCase() + last.slice(1));
  }, [pathname]);

  // timer sessão
  const resetTimer = () => setTimeLeft(15 * 60);
  useEffect(() => {
    const handle = () => resetTimer();
    window.addEventListener("mousemove", handle);
    window.addEventListener("keydown", handle);
    window.addEventListener("click", handle);
    return () => {
      window.removeEventListener("mousemove", handle);
      window.removeEventListener("keydown", handle);
      window.removeEventListener("click", handle);
    };
  }, []);
  useEffect(() => {
    if (timeLeft <= 0) {
      localStorage.clear();
      router.push("/login");
      return;
    }
    const t = setInterval(() => setTimeLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [timeLeft, router]);

  // tema
  useEffect(() => {
    const stored = localStorage.getItem("theme") as ThemeMode | null;
    const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
    const initial: ThemeMode = stored ?? (prefersDark ? "dark" : "light");
    setTheme(initial);
    applyTheme(initial);
  }, []);
  const applyTheme = (mode: ThemeMode) => {
    const root = document.documentElement;
    if (mode === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    localStorage.setItem("theme", mode);
  };
  const toggleTheme = () => {
    const next: ThemeMode = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  };

  // fechar menu ao clicar fora
  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  // navegação
  const goToEditProfile = () => {
    setMenuOpen(false);
    router.push("/account/profile");
  };
  const goToChangePassword = () => {
    setMenuOpen(false);
    router.push("/account/change-password");
  };

  return (
    <header className={`header ${className || ""}`} role="banner" data-testid="header">
      <div className="header-content">
        {/* logo */}
    <div className="logo-container">
  <Image src={logo} alt="Logo FS3M" width={50} height={50} />
  <div>
    <div className="system-name">
      <span className="logo-letter">F</span>
      <span className="logo-letter">S</span>
      <span className="logo-three">3</span>{/* sempre laranja */}
      <span className="logo-letter">M</span>
    </div>
    <span className="system-subname">
      Future Security Maturity Monitoring & Management
    </span>
  </div>
</div>


        <div className="header-spacer" />

        {/* ações à direita: switch + kebab */}
        <div className="header-actions" ref={menuRef}>
          {/* SWITCH DE TEMA — fora do menu */}
          <label className="switch" aria-label="Alternar tema">
            <input
              id="input"               // usa seu CSS existente
              type="checkbox"
              checked={theme === "dark"}
              onChange={toggleTheme}
            />
            <div className="slider round">
              <div className="sun-moon">
                <svg id="moon-dot-1" className="moon-dot" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="moon-dot-2" className="moon-dot" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="moon-dot-3" className="moon-dot" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="light-ray-1" className="light-ray" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="light-ray-2" className="light-ray" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="light-ray-3" className="light-ray" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>

                <svg id="cloud-1" className="cloud-dark" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="cloud-2" className="cloud-dark" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="cloud-3" className="cloud-dark" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="cloud-4" className="cloud-light" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="cloud-5" className="cloud-light" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
                <svg id="cloud-6" className="cloud-light" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="50"></circle>
                </svg>
              </div>

              <div className="stars">
                <svg id="star-1" className="star" viewBox="0 0 20 20">
                  <path d="M 0 10 C 10 10,10 10 ,0 10 C 10 10 , 10 10 , 10 20 C 10 10 , 10 10 , 20 10 C 10 10 , 10 10 , 10 0 C 10 10,10 10 ,0 10 Z"></path>
                </svg>
                <svg id="star-2" className="star" viewBox="0 0 20 20">
                  <path d="M 0 10 C 10 10,10 10 ,0 10 C 10 10 , 10 10 , 10 20 C 10 10 , 10 10 , 20 10 C 10 10 , 10 10 , 10 0 C 10 10,10 10 ,0 10 Z"></path>
                </svg>
                <svg id="star-3" className="star" viewBox="0 0 20 20">
                  <path d="M 0 10 C 10 10,10 10 ,0 10 C 10 10 , 10 10 , 10 20 C 10 10 , 10 10 , 20 10 C 10 10 , 10 10 , 10 0 C 10 10,10 10 ,0 10 Z"></path>
                </svg>
                <svg id="star-4" className="star" viewBox="0 0 20 20">
                  <path d="M 0 10 C 10 10,10 10 ,0 10 C 10 10 , 10 10 , 10 20 C 10 10 , 10 10 , 20 10 C 10 10 , 10 10 , 10 0 C 10 10,10 10 ,0 10 Z"></path>
                </svg>
              </div>
            </div>
          </label>

          {/* botão ⋮ */}
          <button
            className="kebab-btn"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Menu"
            style={{ marginLeft: 8 }}
          >
            <MoreVertical size={22} />
          </button>

          {/* dropdown */}
          {menuOpen && (
            <div className="dropdown">
              <button className="dropdown-item" onClick={goToEditProfile}>
                <UserRound size={16} /> <span>Editar cadastro</span>
              </button>
              <button className="dropdown-item" onClick={goToChangePassword}>
                <KeyRound size={16} /> <span>Mudar senha</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
