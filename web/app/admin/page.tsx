"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  Plus, Trash2, Edit3, X, Check, Shield, User, ChevronLeft,
  Eye, EyeOff, ToggleLeft, ToggleRight, Users
} from "lucide-react";

interface UserItem {
  id: number;
  username: string;
  nama_lengkap: string;
  jabatan: string;
  role: string;
  is_active: number;
  created_at: string;
}

const API = "http://127.0.0.1:8000";

function getAuthHeader() {
  const token = localStorage.getItem("kpu_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function AdminPage() {
  const router = useRouter();
  const [me, setMe] = useState<any>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState<UserItem | null>(null);
  const [form, setForm] = useState({ username: "", nama_lengkap: "", jabatan: "", password: "", role: "user" });
  const [showPass, setShowPass] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const fetchUsers = useCallback(async () => {
    const res = await fetch(`${API}/api/auth/users`, { headers: getAuthHeader() as HeadersInit });
    if (!res.ok) { router.replace("/login"); return; }
    const data = await res.json();
    setUsers(data.users);
  }, [router]);

  useEffect(() => {
    const token = localStorage.getItem("kpu_token");
    const userStr = localStorage.getItem("kpu_user");
    if (!token || !userStr) { router.replace("/login"); return; }
    const u = JSON.parse(userStr);
    if (u.role !== "admin") { router.replace("/"); return; }
    setMe(u);
    fetchUsers().finally(() => setLoading(false));
  }, [fetchUsers, router]);

  const openAddModal = () => {
    setEditUser(null);
    setForm({ username: "", nama_lengkap: "", jabatan: "", password: "", role: "user" });
    setShowModal(true);
    setMsg(null);
  };

  const openEditModal = (u: UserItem) => {
    setEditUser(u);
    setForm({ username: u.username, nama_lengkap: u.nama_lengkap, jabatan: u.jabatan, password: "", role: u.role });
    setShowModal(true);
    setMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg(null);
    try {
      if (editUser) {
        const body: any = { nama_lengkap: form.nama_lengkap, jabatan: form.jabatan, role: form.role };
        if (form.password) body.password = form.password;
        const res = await fetch(`${API}/api/auth/users/${editUser.id}`, {
          method: "PUT", headers: { "Content-Type": "application/json", ...getAuthHeader() as any },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) { setMsg({ type: "err", text: data.detail }); return; }
        setMsg({ type: "ok", text: "User berhasil diperbarui." });
      } else {
        const res = await fetch(`${API}/api/auth/users`, {
          method: "POST", headers: { "Content-Type": "application/json", ...getAuthHeader() as any },
          body: JSON.stringify(form),
        });
        const data = await res.json();
        if (!res.ok) { setMsg({ type: "err", text: data.detail }); return; }
        setMsg({ type: "ok", text: "User berhasil ditambahkan." });
      }
      await fetchUsers();
      setTimeout(() => { setShowModal(false); setMsg(null); }, 1200);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActive = async (u: UserItem) => {
    await fetch(`${API}/api/auth/users/${u.id}`, {
      method: "PUT", headers: { "Content-Type": "application/json", ...getAuthHeader() as any },
      body: JSON.stringify({ is_active: u.is_active === 0 }),
    });
    fetchUsers();
  };

  const handleDelete = async (u: UserItem) => {
    if (!confirm(`Hapus user "${u.nama_lengkap}" (${u.username})?`)) return;
    const res = await fetch(`${API}/api/auth/users/${u.id}`, {
      method: "DELETE", headers: getAuthHeader() as HeadersInit,
    });
    const data = await res.json();
    if (!res.ok) { alert(data.detail); return; }
    fetchUsers();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "linear-gradient(135deg,#1C0202,#700D0A)" }}>
        <div className="animate-spin w-10 h-10 border-4 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg,#1C0202,#700D0A,#4A0806,#140101)" }}>
      {/* Header */}
      <header className="w-full px-6 py-4 flex items-center gap-4 border-b border-white/10" style={{ background: "rgba(0,0,0,0.3)", backdropFilter: "blur(12px)" }}>
        <div className="relative w-9 h-9 flex-shrink-0">
          <Image src="/logo_kpu.png" alt="Logo KPU" fill className="object-contain" />
        </div>
        <div className="flex-1">
          <h1 className="text-white font-black text-base leading-tight">Manajemen Akun Pengguna</h1>
          <p className="text-white/50 text-xs">KPU Provinsi Riau — Panel Admin</p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-1.5 text-white/70 hover:text-white text-sm font-medium transition-colors px-3 py-1.5 rounded-lg hover:bg-white/10"
        >
          <ChevronLeft className="w-4 h-4" /> Kembali
        </button>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Stats + Tambah */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-lg">{users.length} Pengguna</div>
              <div className="text-white/50 text-xs">{users.filter(u => u.role === "admin").length} Admin · {users.filter(u => u.role !== "admin").length} User</div>
            </div>
          </div>
          <button
            onClick={openAddModal}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm text-white transition-all hover:scale-105 active:scale-95"
            style={{ background: "linear-gradient(135deg,#D4AF37,#b8942a)", boxShadow: "0 4px 16px rgba(212,175,55,0.3)" }}
          >
            <Plus className="w-4 h-4" /> Tambah User
          </button>
        </div>

        {/* Tabel */}
        <div className="rounded-2xl overflow-hidden shadow-2xl" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", backdropFilter: "blur(12px)" }}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.05)" }}>
                  {["No", "Nama Lengkap", "Username", "Jabatan", "Role", "Status", "Aksi"].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-white/60 text-xs font-bold uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={u.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 text-white/50 text-sm">{i + 1}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold text-white"
                          style={{ background: u.role === "admin" ? "linear-gradient(135deg,#D4AF37,#b8942a)" : "rgba(255,255,255,0.15)" }}>
                          {u.nama_lengkap.charAt(0)}
                        </div>
                        <span className="text-white font-semibold text-sm">{u.nama_lengkap}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-white/70 text-sm font-mono">{u.username}</td>
                    <td className="px-4 py-3 text-white/70 text-sm">{u.jabatan}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${u.role === "admin" ? "bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/30" : "bg-white/10 text-white/70 border border-white/10"}`}>
                        {u.role === "admin" ? <Shield className="w-3 h-3" /> : <User className="w-3 h-3" />}
                        {u.role === "admin" ? "Admin" : "User"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => toggleActive(u)} className="transition-colors">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-400"><ToggleRight className="w-5 h-5" /> Aktif</span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-red-400"><ToggleLeft className="w-5 h-5" /> Nonaktif</span>
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openEditModal(u)} className="p-1.5 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-all">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        {!(u.role === "admin" && users.filter(x => x.role === "admin").length <= 1) && (
                          <button onClick={() => handleDelete(u)} className="p-1.5 rounded-lg text-white/50 hover:text-red-400 hover:bg-red-500/10 transition-all">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal Tambah/Edit */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4" style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(6px)" }}>
          <div className="w-full max-w-md rounded-2xl p-6 shadow-2xl" style={{ background: "rgba(28,2,2,0.95)", border: "1px solid rgba(255,255,255,0.12)" }}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-white font-black text-lg">{editUser ? "Edit User" : "Tambah User Baru"}</h2>
              <button onClick={() => setShowModal(false)} className="text-white/50 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              {!editUser && (
                <div>
                  <label className="block text-white/70 text-xs font-bold uppercase tracking-wider mb-1">Username</label>
                  <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required
                    className="w-full px-3.5 py-2.5 rounded-xl text-white text-sm outline-none focus:ring-2 focus:ring-[#D4AF37]/50"
                    style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)" }}
                    placeholder="username_unik" />
                </div>
              )}
              <div>
                <label className="block text-white/70 text-xs font-bold uppercase tracking-wider mb-1">Nama Lengkap</label>
                <input value={form.nama_lengkap} onChange={e => setForm({ ...form, nama_lengkap: e.target.value })} required
                  className="w-full px-3.5 py-2.5 rounded-xl text-white text-sm outline-none focus:ring-2 focus:ring-[#D4AF37]/50"
                  style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)" }}
                  placeholder="Nama Lengkap" />
              </div>
              <div>
                <label className="block text-white/70 text-xs font-bold uppercase tracking-wider mb-1">Jabatan</label>
                <input value={form.jabatan} onChange={e => setForm({ ...form, jabatan: e.target.value })} required
                  className="w-full px-3.5 py-2.5 rounded-xl text-white text-sm outline-none focus:ring-2 focus:ring-[#D4AF37]/50"
                  style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)" }}
                  placeholder="Staf / Kasubag / dll" />
              </div>
              <div>
                <label className="block text-white/70 text-xs font-bold uppercase tracking-wider mb-1">
                  Password {editUser && <span className="text-white/40 normal-case font-normal">(kosongkan jika tidak diubah)</span>}
                </label>
                <div className="relative">
                  <input type={showPass ? "text" : "password"} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
                    required={!editUser}
                    className="w-full px-3.5 pr-10 py-2.5 rounded-xl text-white text-sm outline-none focus:ring-2 focus:ring-[#D4AF37]/50"
                    style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)" }}
                    placeholder={editUser ? "Biarkan kosong untuk tidak mengubah" : "Password baru"} />
                  <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/80">
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-white/70 text-xs font-bold uppercase tracking-wider mb-1">Role</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl text-white text-sm outline-none focus:ring-2 focus:ring-[#D4AF37]/50"
                  style={{ background: "rgba(28,2,2,0.9)", border: "1px solid rgba(255,255,255,0.15)" }}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {msg && (
                <div className={`rounded-xl px-4 py-3 text-sm font-medium ${msg.type === "ok" ? "bg-emerald-900/40 text-emerald-300 border border-emerald-500/30" : "bg-red-900/40 text-red-300 border border-red-500/30"}`}>
                  {msg.text}
                </div>
              )}

              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 rounded-xl text-white/70 font-semibold text-sm transition-all hover:bg-white/10"
                  style={{ border: "1px solid rgba(255,255,255,0.15)" }}>
                  Batal
                </button>
                <button type="submit" disabled={submitting}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-sm text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-60"
                  style={{ background: "linear-gradient(135deg,#700D0A,#9B1410)" }}>
                  {submitting ? <span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> : <Check className="w-4 h-4" />}
                  {submitting ? "Menyimpan..." : "Simpan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
