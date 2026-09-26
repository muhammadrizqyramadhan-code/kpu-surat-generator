"use client";

import { useState } from "react";
import Image from "next/image";
import { Plus, Trash2, Sparkles, FileDown, Loader2 } from "lucide-react";

export default function FormUndanganRapat() {
  const [isInternal, setIsInternal] = useState(false);
  const [tujuan, setTujuan] = useState("");
  const [kotaTujuan, setKotaTujuan] = useState("");
  const [penerimaList, setPenerimaList] = useState<string[]>([
    "Anggota KPU Provinsi Riau",
    "Sekretaris KPU Provinsi Riau",
    "Pejabat Struktural di Lingkungan KPU Provinsi Riau",
  ]);

  const [sifat, setSifat] = useState("Segera");
  const [lampiran, setLampiran] = useState("1 (satu) Rangkap");
  const [poinIsi, setPoinIsi] = useState("");
  const [aiIsi, setAiIsi] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const [tanggalRapat, setTanggalRapat] = useState("");
  const [waktuRapat, setWaktuRapat] = useState("Pukul 09.00 WIB s.d selesai");
  const [tempatRapat, setTempatRapat] = useState("Ruangan Rapat Lt.2 KPU Provinsi Riau");
  const [linkZoom, setLinkZoom] = useState("");
  const [agendaList, setAgendaList] = useState<string[]>([""]);

  const [penutupCustom, setPenutupCustom] = useState(
    "Demikian disampaikan, untuk dilaksanakan sebagaimana mestinya."
  );
  const [jabatanTtd, setJabatanTtd] = useState("Sekretaris");
  const [namaTtd, setNamaTtd] = useState("RUDINAL B");

  const [docLoading, setDocLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleAddPenerima = () => setPenerimaList([...penerimaList, ""]);
  const handleRemovePenerima = (idx: number) => setPenerimaList(penerimaList.filter((_, i) => i !== idx));
  const handlePenerimaChange = (idx: number, val: string) => {
    const updated = [...penerimaList];
    updated[idx] = val;
    setPenerimaList(updated);
  };

  const handleAddAgenda = () => setAgendaList([...agendaList, ""]);
  const handleRemoveAgenda = (idx: number) => setAgendaList(agendaList.filter((_, i) => i !== idx));
  const handleAgendaChange = (idx: number, val: string) => {
    const updated = [...agendaList];
    updated[idx] = val;
    setAgendaList(updated);
  };

  const handleGenerateAI = async () => {
    if (!poinIsi.trim()) {
      setStatusMsg({ type: "error", text: "Mohon isi poin tujuan/latar belakang rapat terlebih dahulu." });
      return;
    }

    const targetTujuan = isInternal ? "internal KPU Provinsi Riau" : tujuan;
    if (!isInternal && !targetTujuan.trim()) {
      setStatusMsg({ type: "error", text: "Mohon isi tujuan penerima rapat (Ditujukan kepada)." });
      return;
    }

    setAiLoading(true);
    setStatusMsg(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jenis_surat: "Undangan Rapat",
          tujuan: targetTujuan,
          poin_isi: poinIsi,
        }),
      });

      if (!res.ok) throw new Error("Gagal menyusun kalimat pembuka rapat.");
      const data = await res.json();
      setAiIsi(data.isi);
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Gagal menghubungi layanan AI." });
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmitDocx = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiIsi.trim()) {
      setStatusMsg({ type: "error", text: "Mohon susun kalimat pembuka (AI) terlebih dahulu." });
      return;
    }

    setDocLoading(true);
    setStatusMsg(null);

    const filteredAgenda = agendaList.filter((a) => a.trim());
    const filteredPenerima = isInternal ? penerimaList.filter((p) => p.trim()) : null;

    let hariStr = "";
    let tglFormatted = "";
    if (tanggalRapat) {
      const d = new Date(tanggalRapat);
      const hariArr = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
      const bulanArr = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
      ];
      hariStr = hariArr[d.getDay()];
      tglFormatted = `${d.getDate()} ${bulanArr[d.getMonth()]} ${d.getFullYear()}`;
    }

    const jadwalPayload = {
      hari: hariStr,
      tanggal: tglFormatted,
      waktu: waktuRapat,
      tempat: tempatRapat,
      link_zoom: linkZoom,
      agenda: filteredAgenda,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/api/generate-docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jenis_surat: "Undangan Rapat",
          tujuan: isInternal ? "" : tujuan,
          kota_tujuan: isInternal ? "" : kotaTujuan,
          sifat,
          lampiran: isInternal ? "-" : lampiran,
          isi: aiIsi,
          penerima_list: filteredPenerima,
          jadwal: jadwalPayload,
          penutup_custom: penutupCustom,
          jabatan_ttd: jabatanTtd,
          nama_ttd: namaTtd,
          is_internal: isInternal,
        }),
      });

      if (!response.ok) throw new Error("Gagal membuat file Undangan Rapat.");

      const nomorSurat = response.headers.get("X-Nomor-Surat") || "Surat";
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `surat_undangan_rapat_${nomorSurat.split("/")[0]}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setStatusMsg({ type: "success", text: `Undangan Rapat berhasil dibuat dengan nomor: ${nomorSurat}` });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Terjadi kesalahan sistem." });
    } finally {
      setDocLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmitDocx} className="space-y-6 text-slate-800">
      <div>
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Tipe Undangan Rapat</label>
        <div className="flex gap-6">
          <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-800 font-medium">
            <input
              type="radio"
              name="tipe_undangan"
              checked={!isInternal}
              onChange={() => {
                setIsInternal(false);
                setPenutupCustom("Demikian disampaikan, untuk dilaksanakan sebagaimana mestinya.");
                setJabatanTtd("Sekretaris");
                setNamaTtd("RUDINAL B");
              }}
              className="accent-[#700D0A]"
            />
            Eksternal (ke Kabupaten/Kota)
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-800 font-medium">
            <input
              type="radio"
              name="tipe_undangan"
              checked={isInternal}
              onChange={() => {
                setIsInternal(true);
                setPenutupCustom("Demikian disampaikan, atas kehadirannya diucapkan terima kasih.");
                setJabatanTtd("Ketua Komisi Pemilihan Umum Provinsi Riau");
                setNamaTtd("RUSIDI RUSDAN");
              }}
              className="accent-[#700D0A]"
            />
            Internal (ke Pejabat/Pegawai Internal)
          </label>
        </div>
      </div>

      {!isInternal ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Ditujukan Kepada (Yth.)</label>
            <input
              type="text"
              placeholder="Sekretaris KPU Kabupaten/Kota Se Provinsi Riau"
              value={tujuan}
              onChange={(e) => setTujuan(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kota Tujuan (Opsional)</label>
            <input
              type="text"
              placeholder="Kosongkan untuk 'di Tempat'"
              value={kotaTujuan}
              onChange={(e) => setKotaTujuan(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">Daftar Penerima Internal</label>
          {penerimaList.map((p, idx) => (
            <div key={idx} className="flex gap-2">
              <input
                type="text"
                value={p}
                onChange={(e) => handlePenerimaChange(idx, e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
              />
              <button
                type="button"
                onClick={() => handleRemovePenerima(idx)}
                disabled={penerimaList.length === 1}
                className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded border border-slate-200 disabled:opacity-20"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={handleAddPenerima}
            className="flex items-center gap-1 text-xs font-bold text-[#700D0A]"
          >
            <Plus className="w-3.5 h-3.5" /> Tambah Penerima
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Poin Singkat Tujuan Rapat (Disusun AI)</label>
        <textarea
          rows={3}
          placeholder="Contoh: Rapat koordinasi evaluasi tugas dan kebersihan kantor se-Riau"
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
          {aiLoading ? "AI sedang menyusun..." : "Susun Kalimat Pembuka AI"}
        </button>
      </div>

      {aiIsi && (
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kalimat Pembuka (Bisa Diedit)</label>
          <textarea
            rows={4}
            value={aiIsi}
            onChange={(e) => setAiIsi(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
          />
        </div>
      )}

      <div className="border-t border-slate-200 pt-6 space-y-4">
        <h3 className="text-base font-extrabold text-slate-800">Jadwal &amp; Agenda Rapat</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Tanggal Rapat</label>
            <input
              type="date"
              value={tanggalRapat}
              onChange={(e) => setTanggalRapat(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Waktu</label>
            <input
              type="text"
              placeholder="Pukul 09.00 WIB s.d selesai"
              value={waktuRapat}
              onChange={(e) => setWaktuRapat(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Tempat</label>
            <input
              type="text"
              placeholder="Ruangan Rapat Lt.2 KPU Provinsi Riau"
              value={tempatRapat}
              onChange={(e) => setTempatRapat(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Link Zoom (Opsional)</label>
            <input
              type="text"
              placeholder="Kosongkan jika tatap muka"
              value={linkZoom}
              onChange={(e) => setLinkZoom(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Agenda Rapat</label>
          {agendaList.map((agenda, idx) => (
            <div key={idx} className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder={`Agenda ke-${idx + 1}`}
                value={agenda}
                onChange={(e) => handleAgendaChange(idx, e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 text-sm focus:border-[#700D0A] outline-none"
              />
              <button
                type="button"
                onClick={() => handleRemoveAgenda(idx)}
                disabled={agendaList.length === 1}
                className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded border border-slate-200 disabled:opacity-20"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={handleAddAgenda}
            className="flex items-center gap-1 text-xs font-bold text-[#700D0A]"
          >
            <Plus className="w-3.5 h-3.5" /> Tambah Agenda
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-200 pt-6">
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Jabatan Penandatangan</label>
          <input
            type="text"
            value={jabatanTtd}
            onChange={(e) => setJabatanTtd(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Nama Penandatangan</label>
          <input
            type="text"
            value={namaTtd}
            onChange={(e) => setNamaTtd(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] outline-none"
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
        {docLoading ? "Memproses Dokumen..." : "Buat File Undangan Rapat (.docx)"}
      </button>
    </form>
  );
}
