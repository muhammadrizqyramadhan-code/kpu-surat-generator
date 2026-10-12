"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, LogIn, Lock, User } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem("kpu_token");
    if (token) router.replace("/");
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Username dan password harus diisi.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Login gagal.");
        return;
      }
      localStorage.setItem("kpu_token", data.access_token);
      localStorage.setItem("kpu_user", JSON.stringify(data.user));
      router.replace("/");
    } catch {
      setError("Tidak dapat terhubung ke server. Pastikan server berjalan.");
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) return null;

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden">
      {/* Background foto gedung KPU */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/kpu_gedung.png"
          alt="Gedung KPU Provinsi Riau"
          fill
          className="object-cover object-center"
          priority
        />
        {/* Overlay lebih gelap untuk kenyamanan visual & kontras kartu login */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/85 via-black/70 to-[#2A0403]/85" />
      </div>

      {/* Kartu Login */}
      <div className="relative z-10 w-full max-w-md mx-4">
        <div
          className="rounded-3xl p-8 shadow-2xl"
          style={{
            background: "rgba(255,255,255,0.07)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.18)",
          }}
        >
          {/* Logo + Judul */}
          <div className="flex flex-col items-center mb-8">
            <div className="relative w-20 h-20 mb-4 drop-shadow-2xl">
              <Image src="/logo_kpu.png" alt="Logo KPU" fill className="object-contain" />
            </div>
            <h1 className="text-white text-2xl font-black tracking-tight text-center">
              Generator Surat Resmi
            </h1>
            <p className="text-white/70 text-sm text-center mt-1">
              Komisi Pemilihan Umum Provinsi Riau
            </p>
            <div className="w-16 h-0.5 bg-gradient-to-r from-[#D4AF37] to-[#f0c040] rounded-full mt-3" />
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-white/80 text-xs font-bold uppercase tracking-widest mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  id="login-username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Masukkan username"
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-white placeholder-white/30 text-sm font-medium outline-none transition-all focus:ring-2 focus:ring-[#D4AF37]/60"
                  style={{
                    background: "rgba(255,255,255,0.10)",
                    border: "1px solid rgba(255,255,255,0.18)",
                  }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-white/80 text-xs font-bold uppercase tracking-widest mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  id="login-password"
                  type={showPass ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Masukkan password"
                  className="w-full pl-10 pr-11 py-3 rounded-xl text-white placeholder-white/30 text-sm font-medium outline-none transition-all focus:ring-2 focus:ring-[#D4AF37]/60"
                  style={{
                    background: "rgba(255,255,255,0.10)",
                    border: "1px solid rgba(255,255,255,0.18)",
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/80 transition-colors"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-xl px-4 py-3 text-sm font-medium text-red-200 bg-red-900/40 border border-red-500/30">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm tracking-wide transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                background: loading
                  ? "rgba(112,13,10,0.5)"
                  : "linear-gradient(135deg, #700D0A, #9B1410)",
                color: "white",
                boxShadow: "0 4px 20px rgba(112,13,10,0.5)",
              }}
            >
              {loading ? (
                <span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full inline-block" />
              ) : (
                <LogIn className="w-4 h-4" />
              )}
              {loading ? "Memverifikasi..." : "Masuk"}
            </button>
          </form>

          {/* Footer kartu */}
          <p className="text-center text-white/30 text-xs mt-6">
            © 2026 KPU Provinsi Riau — Sistem Internal
          </p>
        </div>
      </div>
    </div>
  );
}
