"use client";

import { useState } from "react";
import { Sparkles, FileDown, Loader2 } from "lucide-react";

interface FormSuratVariatifProps {
  jenisSurat: string;
}

export default function FormSuratVariatif({ jenisSurat }: FormSuratVariatifProps) {
  const isPermohonanGenerik = jenisSurat === "Surat Permohonan";

  const [perihalCustom, setPerihalCustom] = useState("");
  const [kodeCustom, setKodeCustom] = useState("");
  const [tujuan, setTujuan] = useState("");
  const [kotaTujuan, setKotaTujuan] = useState("");
  const [sifat, setSifat] = useState("Segera");
  const [lampiran, setLampiran] = useState("-");

  const [poinIsi, setPoinIsi] = useState("");
  const [aiIsi, setAiIsi] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const [penutupCustom, setPenutupCustom] = useState(
    jenisSurat === "Permohonan Data"
      ? "Demikian surat permohonan ini kami sampaikan. Atas perhatian dan kerja sama Bapak/Ibu, kami ucapkan terima kasih."
      : jenisSurat === "Surat Permohonan"
      ? "Demikian disampaikan, atas perkenan dan kerjasamanya disampaikan terima kasih."
      : "Demikian disampaikan, untuk dilaksanakan sebagaimana mestinya."
  );

  const [jabatanTtd, setJabatanTtd] = useState("Sekretaris");
  const [namaTtd, setNamaTtd] = useState("RUDINAL B");

  const [docLoading, setDocLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleGenerateAI = async () => {
    if (!tujuan.trim() || !poinIsi.trim()) {
      setStatusMsg({ type: "error", text: "Mohon isi 'Ditujukan Kepada' dan 'Poin Isi Surat' terlebih dahulu." });
      return;
    }

    if (isPermohonanGenerik && (!perihalCustom.trim() || !kodeCustom.trim())) {
      setStatusMsg({ type: "error", text: "Mohon isi Perihal dan Kode Klasifikasi untuk Surat Permohonan." });
      return;
    }

    setAiLoading(true);
    setStatusMsg(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jenis_surat: jenisSurat,
          tujuan,
          poin_isi: poinIsi,
        }),
      });

      if (!res.ok) throw new Error("Gagal menyusun isi surat dengan AI.");
      const data = await res.json();
      setAiIsi(data.isi);
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Gagal menyusun surat via AI." });
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmitDocx = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiIsi.trim()) {
      setStatusMsg({ type: "error", text: "Mohon susun isi surat AI terlebih dahulu." });
      return;
    }

    setDocLoading(true);
    setStatusMsg(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/generate-docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jenis_surat: jenisSurat,
          tujuan,
          kota_tujuan: kotaTujuan,
          sifat,
          lampiran,
          isi: aiIsi,
          perihal_custom: isPermohonanGenerik ? perihalCustom : null,
          kode_custom: isPermohonanGenerik ? kodeCustom : null,
          penutup_custom: penutupCustom,
          jabatan_ttd: jabatanTtd,
          nama_ttd: namaTtd,
        }),
      });

      if (!response.ok) throw new Error("Gagal membuat dokumen Word.");

      const nomorSurat = response.headers.get("X-Nomor-Surat") || "Surat";
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `surat_${jenisSurat.replace(/ /g, "_").toLowerCase()}_${nomorSurat.split("/")[0]}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setStatusMsg({ type: "success", text: `Surat berhasil dibuat dengan nomor: ${nomorSurat}` });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Terjadi kesalahan sistem." });
    } finally {
      setDocLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmitDocx} className="space-y-6 text-slate-800">
      {isPermohonanGenerik && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-amber-50 p-4 rounded-xl border border-amber-200 mb-4 shadow-sm">
          <div>
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">Perihal Surat</label>
            <input
              type="text"
              placeholder="Contoh: Permohonan Peminjaman Bus Kegiatan Capacity Building"
              value={perihalCustom}
              onChange={(e) => setPerihalCustom(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">Kode Klasifikasi Arsip</label>
            <input
              type="text"
              placeholder="Contoh: RT.03.3-SD"
              value={kodeCustom}
              onChange={(e) => setKodeCustom(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Ditujukan Kepada (Yth.)</label>
          <input
            type="text"
            placeholder="Sekretaris KPU Kabupaten Bengkalis"
            value={tujuan}
            onChange={(e) => setTujuan(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kota Tujuan (Opsional)</label>
          <input
            type="text"
            placeholder="Bengkalis (Kosongkan jika 'di Tempat')"
            value={kotaTujuan}
            onChange={(e) => setKotaTujuan(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Sifat</label>
          <select
            value={sifat}
            onChange={(e) => setSifat(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
          >
            <option value="Segera">Segera</option>
            <option value="Penting">Penting</option>
            <option value="Biasa">Biasa</option>
            <option value="-">-</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Lampiran</label>
          <input
            type="text"
            value={lampiran}
            onChange={(e) => setLampiran(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Poin-poin Isi Surat (Bahasa Bebas / Santai)</label>
        <textarea
          rows={4}
          placeholder="Contoh: Rapat tanggal 20 Juli 2026, jam 09.00 WIB di ruang rapat utama membahas tahapan Pilkada."
          value={poinIsi}
          onChange={(e) => setPoinIsi(e.target.value)}
          className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 text-sm focus:border-[#700D0A] outline-none"
        />
        <button
          type="button"
          onClick={handleGenerateAI}
          disabled={aiLoading}
          className="mt-2 bg-amber-600 hover:bg-amber-700 text-white font-bold py-2.5 px-4 rounded-xl text-sm flex items-center gap-2 transition-all shadow-md disabled:opacity-50"
        >
          {aiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {aiLoading ? "AI sedang menyusun isi surat..." : "Susun Isi Surat via AI"}
        </button>
      </div>

      {aiIsi && (
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Hasil Susunan AI (Bisa Diedit Manual)</label>
          <textarea
            rows={6}
            value={aiIsi}
            onChange={(e) => setAiIsi(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none font-sans"
          />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-200 pt-6">
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kalimat Penutup</label>
          <input
            type="text"
            value={penutupCustom}
            onChange={(e) => setPenutupCustom(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Nama Penandatangan</label>
          <input
            type="text"
            value={namaTtd}
            onChange={(e) => setNamaTtd(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
          />
        </div>
      </div>

      {statusMsg && (
        <div
          className={`p-3.5 rounded-xl text-sm font-medium border ${
            statusMsg.type === "success"
              ? "bg-green-50 text-green-800 border-green-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          {statusMsg.text}
        </div>
      )}

      <button
        type="submit"
        disabled={docLoading || !aiIsi}
        className="w-full bg-[#700D0A] hover:bg-[#590A08] text-white font-extrabold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
      >
        {docLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileDown className="w-5 h-5" />}
        {docLoading ? "Memproses Dokumen..." : "Buat File Word (.docx)"}
      </button>
    </form>
  );
}
