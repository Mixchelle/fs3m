"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getUser,
  updateUser,
  setUserActive,
  UserListItem,
  Role,
} from "@/services/users";
import AppShell from "@/components/layout/AppShell";

export default function EditUserPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [user, setUser] = useState<UserListItem | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchUser = async () => {
    const data = await getUser(id);
    setUser(data);
  };

  useEffect(() => {
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSaving(true);
    try {
      const payload = {
        nome: user.nome,
        email: user.email,
        role: user.role as Role,
        cliente: user.cliente ?? null,
        gestor_referente: user.gestor_referente ?? null,
      };
      await updateUser(id, payload);
      router.push("/(dashboard)/users");
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async () => {
    if (!user) return;
    await setUserActive(user.id, !user.is_active);
    await fetchUser();
  };

  if (!user) return <div className="p-4">Carregando...</div>;

  return (
          <AppShell>
    <div className="p-4 max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Editar usuário</h1>
        <button onClick={toggleActive} className="px-3 py-2 border rounded">
          {user.is_active ? "Desativar" : "Ativar"}
        </button>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium">Nome</label>
          <input
            className="border rounded w-full px-3 py-2"
            value={user.nome}
            onChange={(e) => setUser({ ...user, nome: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            className="border rounded w-full px-3 py-2"
            value={user.email}
            onChange={(e) => setUser({ ...user, email: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Papel</label>
          <select
            className="border rounded w-full px-3 py-2"
            value={user.role}
            onChange={(e) => setUser({ ...user, role: e.target.value as Role })}
          >
            <option value="gestor">gestor</option>
            <option value="analista">analista</option>
            <option value="cliente">cliente</option>
            <option value="subcliente">subcliente</option>
          </select>
        </div>

        {user.role === "analista" && (
          <div>
            <label className="block text-sm font-medium">
              Gestor referente (ID)
            </label>
            <input
              type="number"
              className="border rounded w-full px-3 py-2"
              value={user.gestor_referente ?? ""}
              onChange={(e) =>
                setUser({
                  ...user,
                  gestor_referente: e.target.value
                    ? Number(e.target.value)
                    : null,
                })
              }
            />
          </div>
        )}

        {user.role === "subcliente" && (
          <div>
            <label className="block text-sm font-medium">
              Cliente pai (ID)
            </label>
            <input
              type="number"
              className="border rounded w-full px-3 py-2"
              value={user.cliente ?? ""}
              onChange={(e) =>
                setUser({
                  ...user,
                  cliente: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
          </div>
        )}

        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 border rounded"
        >
          {saving ? "Salvando..." : "Salvar alterações"}
        </button>
      </form>
    </div>
    </AppShell>
  );
}
