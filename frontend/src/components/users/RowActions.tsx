"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { FiMail, FiEdit2, FiTrash2, FiEye } from "react-icons/fi";

type Props = {
  id: number;
  email: string;
  onDeleted: () => void;
  onResent?: (email: string) => void; // opcional p/ toast externo
  deleteUserFn: (id: number) => Promise<void>;
  resendFn: (email: string) => Promise<void>;
};

export default function RowActions({
  id,
  email,
  onDeleted,
  onResent,
  deleteUserFn,
  resendFn,
}: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // fecha ao clicar fora / Esc
  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, []);

  const handleDelete = async () => {
    if (!confirm(`Deletar o usuário ${email}?`)) return;
    await deleteUserFn(id);
    onDeleted();
    setOpen(false);
  };

  const handleResend = async () => {
    await resendFn(email);
    onResent?.(email);
    setOpen(false);
  };

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="h-8 w-8 inline-flex items-center justify-center rounded-md border border-border bg-card hover:bg-muted"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Ações"
      >
        {/* três pontinhos */}
        <span className="inline-block leading-none text-foreground">⋮</span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-2 w-52 rounded-md border border-border bg-card shadow-lg"
        >
          <button
            onClick={handleResend}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted text-foreground"
            role="menuitem"
          >
            <FiMail className="shrink-0" size={16} />
            Reenviar E-mail
          </button>

          <Link
            href={`/users/${id}`}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted text-foreground"
            role="menuitem"
          >
            <FiEye className="shrink-0" size={16} />
            Ver
          </Link>

          <Link
            href={`/users/${id}`}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted text-foreground"
            role="menuitem"
          >
            <FiEdit2 className="shrink-0" size={16} />
            Editar Cadastro
          </Link>

          <button
            onClick={handleDelete}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted text-red-600 dark:text-red-400"
            role="menuitem"
          >
            <FiTrash2 className="shrink-0" size={16} />
            Deletar Cadastro
          </button>
        </div>
      )}
    </div>
  );
}
