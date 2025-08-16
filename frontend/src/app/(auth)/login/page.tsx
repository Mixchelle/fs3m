"use client";

import { useState, useEffect, useId } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { User, Lock, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const { login, loading, user } = useAuth();
  const router = useRouter();

  const emailId = useId();
  const passId = useId();
  const errId = useId();
  const helpId = useId();

  const [email, setEmail] = useState("admin@fs3m.com");
  const [password, setPassword] = useState("fs3m@2222");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/");
  }, [loading, user, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.replace("/");
    } catch {
      setError("Credenciais inválidas.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main
      className="flex min-h-screen items-center justify-center bg-neutral-100 px-4"
      role="main"
    >
      {/* CARD CENTRAL */}
      <section
        className="flex w-full max-w-4xl overflow-hidden rounded-2xl shadow-lg bg-white"
        aria-label="Tela de login"
      >
        {/* Lado esquerdo: Login */}
        <div className="w-full md:w-1/2 p-8 flex flex-col justify-center">
          <div className="mb-6 flex flex-col items-center text-center">
            <Image
              src="/assets/f3smlogo.png"
              alt="Logo FS3M"
              width={76}
              height={76}
              priority
              className="mb-2"
            />
            <h1 className="text-2xl font-semibold leading-none" aria-label="FS3M">
              <span className="text-[#6b6b6b]">F</span>
              <span className="text-[#6b6b6b]">S</span>
              <span className="text-[#ffa800]">3</span>
              <span className="text-[#6b6b6b]">M</span>
            </h1>
            <p
              id={helpId}
              className="mt-1 text-xs text-neutral-600 max-w-xs"
            >
              Future Security Maturity Monitoring &amp; Management
            </p>
          </div>

          <form
            onSubmit={onSubmit}
            noValidate
            aria-describedby={helpId}
            aria-busy={busy}
            className="space-y-4"
          >
            {/* E-mail */}
            <div className="space-y-1">
              <label
                htmlFor={emailId}
                className="text-sm font-medium text-neutral-700"
              >
                E-mail
              </label>

              <div className="relative">
                <div
                  className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3"
                  aria-hidden="true"
                >
                  <User className="h-4 w-4 text-neutral-400" />
                </div>

                <input
                  id={emailId}
                  name="email"
                  type="email"
                  inputMode="email"
                  autoComplete="email"
                  required
                  className="block w-full rounded-lg border border-neutral-200 bg-white py-2.5 pr-3 pl-9
                             text-sm text-neutral-800 outline-none ring-0 placeholder:text-neutral-400
                             focus:border-[#ffa800] focus:ring-2 focus:ring-[#ffa800]/30"
                  placeholder="cliente@exemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-invalid={!!error}
                />
              </div>
            </div>

            {/* Senha com olhinho */}
            <div className="space-y-1">
              <label
                htmlFor={passId}
                className="text-sm font-medium text-neutral-700"
              >
                Senha
              </label>

              <div className="relative">
                <div
                  className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3"
                  aria-hidden="true"
                >
                  <Lock className="h-4 w-4 text-neutral-400" />
                </div>

                <input
                  id={passId}
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  minLength={4}
                  className="block w-full rounded-lg border border-neutral-200 bg-white py-2.5 pr-10 pl-9
                             text-sm text-neutral-800 outline-none ring-0 placeholder:text-neutral-400
                             focus:border-[#ffa800] focus:ring-2 focus:ring-[#ffa800]/30"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={!!error}
                  aria-describedby={error ? errId : undefined}
                />

                <button
                  type="button"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  aria-pressed={showPassword}
                  aria-controls={passId}
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#ffa800]"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-neutral-500" />
                  ) : (
                    <Eye className="h-4 w-4 text-neutral-500" />
                  )}
                </button>
              </div>
            </div>

            {/* Erro */}
            <p
              id={errId}
              role="alert"
              aria-live="assertive"
              className={`text-sm ${error ? "text-red-600" : "sr-only"}`}
            >
              {error ?? "ok"}
            </p>

            <div className="text-right">
              <Link
                href="/login/redefinir-senha"
                className="text-xs text-neutral-600 hover:text-neutral-800 underline focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#ffa800]"
              >
                Esqueceu a senha?
              </Link>
            </div>

            {/* Botão laranja */}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-[#ffa800] py-2.5 text-white text-sm font-medium shadow-sm
                         hover:bg-[#e08f00] focus:outline-none focus:ring-4 focus:ring-[#ffa800]/30
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {busy ? "Entrando..." : "Login"}
            </button>
          </form>
        </div>

        {/* Lado direito: Imagem */}
        <div className="hidden md:block w-1/2 relative" aria-hidden="true">
          <Image
            src="/assets/login_fundo.png"
            alt=""
            fill
            priority
            className="object-cover"
          />
        </div>
      </section>
    </main>
  );
}
