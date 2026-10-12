"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import FormPerjalananDinas from "@/components/FormPerjalananDinas";
import FormUndanganRapat from "@/components/FormUndanganRapat";
import FormSuratVariatif from "@/components/FormSuratVariatif";

const JENIS_SURAT_OPTIONS = [
  "Persetujuan Perjalanan Dinas",
  "Undangan Rapat",
  "Permohonan Data",
  "Pemberitahuan",
  "Surat Permohonan",
];

export default function Home() {
  const router = useRouter();
  const [jenisSurat, setJenisSurat] = useState("Persetujuan Perjalanan Dinas");
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("kpu_token");
    if (!token) {
      router.replace("/login");
    } else {
      setAuthenticated(true);
    }
  }, [router]);

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "linear-gradient(135deg,#1C0202,#700D0A)" }}>
        <div className="animate-spin w-10 h-10 border-4 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  return (
    <main className="w-full min-h-screen flex flex-col">
      <Header />

      <div className="w-full flex-1 px-4 sm:px-10 lg:px-16 py-6">
        <div className="w-full bg-white rounded-3xl shadow-2xl shadow-black/70 border border-[#D4AF37]/30 p-6 sm:p-10">
          <div className="border-b border-slate-200 pb-6 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-800 tracking-tight">
                Generator Surat Resmi Otomatis
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1.5">
                Sistem Otomatisasi Penyusunan Surat Resmi Berbasis Natural Language Processing — Komisi Pemilihan Umum Provinsi Riau
              </p>
            </div>
          </div>

          <div className="mb-8 max-w-xl">
            <label className="block text-xs sm:text-sm font-bold text-[#700D0A] mb-2 uppercase tracking-widest">
              Pilih Jenis Surat
            </label>
            <select
              value={jenisSurat}
              onChange={(e) => setJenisSurat(e.target.value)}
              className="w-full px-4 py-3 border-2 border-slate-300 rounded-xl text-slate-800 font-bold text-base focus:ring-2 focus:ring-[#700D0A] focus:border-[#700D0A] bg-white shadow-sm transition-all outline-none"
            >
              {JENIS_SURAT_OPTIONS.map((opt) => (
                <option key={opt} value={opt} className="bg-white text-slate-800">
                  {opt}
                </option>
              ))}
            </select>
          </div>

          {jenisSurat === "Persetujuan Perjalanan Dinas" && <FormPerjalananDinas />}
          {jenisSurat === "Undangan Rapat" && <FormUndanganRapat />}
          {jenisSurat !== "Persetujuan Perjalanan Dinas" && jenisSurat !== "Undangan Rapat" && (
            <FormSuratVariatif jenisSurat={jenisSurat} />
          )}
        </div>
      </div>

      <footer className="w-full py-6 text-center text-xs text-slate-300 border-t border-[#D4AF37]/20 bg-[#140101]/80 backdrop-blur-md mt-auto">
        Format dokumen (kop surat ganda tipis, tabel nomor, blok tanda tangan) sesuai dengan template resmi KPU Provinsi Riau.
      </footer>
    </main>
  );
}
