"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Users, LogOut, Shield, User } from "lucide-react";

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState<{
    id: number;
    username: string;
    nama_lengkap: string;
    jabatan: string;
    role: string;
  } | null>(null);

  useEffect(() => {
    const userStr = localStorage.getItem("kpu_user");
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (e) {
        console.error("Failed to parse user profile", e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("kpu_token");
    localStorage.removeItem("kpu_user");
    router.replace("/login");
  };

  return (
    <header className="w-full bg-gradient-to-r from-[#590A08] via-[#700D0A] to-[#4D0806] text-white py-3.5 px-6 sm:px-12 border-b-2 border-[#D4AF37]/50 shadow-2xl shadow-red-950/70 flex items-center justify-between gap-5 backdrop-blur-md">
      <div className="flex items-center gap-5">
        <div className="relative h-12 w-12 flex-shrink-0 drop-shadow-[0_2px_8px_rgba(212,175,55,0.4)]">
          <Image
            src="/logo_kpu.png"
            alt="Logo KPU"
            fill
            className="object-contain"
            priority
          />
        </div>
        <div className="w-[2px] h-10 bg-gradient-to-b from-[#F3E5AB] via-[#D4AF37] to-[#B8860B] rounded-full shadow-[0_0_10px_rgba(212,175,55,0.7)]"></div>
        <div className="flex flex-col justify-center">
          <span className="text-2xl sm:text-3xl font-black tracking-wider leading-none text-white drop-shadow-md">
            KPU
          </span>
          <span className="text-xs sm:text-sm font-bold tracking-[0.2em] text-[#D4AF37] mt-1 drop-shadow">
            PROVINSI RIAU
          </span>
        </div>
      </div>

      {user && (
        <div className="flex items-center gap-3">
          <div className="hidden md:flex flex-col text-right">
            <span className="text-sm font-bold text-white leading-tight flex items-center justify-end gap-1.5">
              {user.nama_lengkap}
              {user.role === "admin" && (
                <span className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/40 text-[10px] font-extrabold px-1.5 py-0.2 rounded-full uppercase tracking-wider">
                  Admin
                </span>
              )}
            </span>
            <span className="text-xs text-white/70">{user.jabatan}</span>
          </div>

          <div className="flex items-center gap-2">
            {user.role === "admin" && (
              <button
                onClick={() => router.push("/admin")}
                className="flex items-center gap-1.5 bg-[#D4AF37]/20 hover:bg-[#D4AF37]/30 border border-[#D4AF37]/50 text-[#F3E5AB] hover:text-white px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95"
                title="Kelola Pengguna"
              >
                <Users className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Kelola User</span>
              </button>
            )}

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 bg-black/30 hover:bg-red-950/80 border border-white/20 text-white/80 hover:text-white px-3 py-1.5 rounded-xl text-xs font-bold transition-all active:scale-95"
              title="Keluar dari Aplikasi"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Keluar</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
