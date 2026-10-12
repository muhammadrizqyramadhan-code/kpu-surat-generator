"use client";

import { useState } from "react";
import { Plus, Trash2, FileDown, Loader2 } from "lucide-react";

interface Pegawai {
  nama: string;
  jabatan: string;
  tanggal: string;
  dalam_rangka: string;
}

export default function FormPerjalananDinas() {
  const [kabupaten, setKabupaten] = useState("");
  const [kota, setKota] = useState("");
  const [nomorRujukan, setNomorRujukan] = useState("");
  const [tanggalRujukan, setTanggalRujukan] = useState("");
  const [sifat, setSifat] = useState("Segera");
  const [lampiran, setLampiran] = useState("1 (satu) lembar");
  const [jabatanTtd, setJabatanTtd] = useState("Sekretaris");
  const [namaTtd, setNamaTtd] = useState("RUDINAL B");

  const [pegawaiList, setPegawaiList] = useState<Pegawai[]>([
    { nama: "", jabatan: "", tanggal: "", dalam_rangka: "" },
  ]);

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleAddPegawai = () => {
    setPegawaiList([...pegawaiList, { nama: "", jabatan: "", tanggal: "", dalam_rangka: "" }]);
  };

  const handleRemovePegawai = (index: number) => {
    if (pegawaiList.length === 1) return;
    setPegawaiList(pegawaiList.filter((_, i) => i !== index));
  };

  const handlePegawaiChange = (index: number, field: keyof Pegawai, value: string) => {
    const updated = [...pegawaiList];
    updated[index][field] = value;
    setPegawaiList(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!kabupaten.trim() || !kota.trim() || !nomorRujukan.trim() || !tanggalRujukan.trim()) {
      setStatusMsg({ type: "error", text: "Mohon lengkapi data surat (Kabupaten, Kota, Nomor & Tanggal rujukan)." });
      return;
    }

    const filteredPegawai = pegawaiList.filter((p) => p.nama.trim());
    if (filteredPegawai.length === 0) {
      setStatusMsg({ type: "error", text: "Mohon isi minimal 1 pegawai di tabel daftar perjalanan dinas." });
      return;
    }

    setLoading(true);
    setStatusMsg(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/generate-perjalanan-dinas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kabupaten,
          kota,
          nomor_rujukan: nomorRujukan,
          tanggal_rujukan: tanggalRujukan,
          sifat,
          lampiran,
          jabatan_ttd: jabatanTtd,
          nama_ttd: namaTtd,
          pegawai_list: filteredPegawai,
        }),
      });

      if (!response.ok) {
        throw new Error("Gagal membuat dokumen perjalanan dinas.");
      }

      const nomorSurat = response.headers.get("X-Nomor-Surat") || "Surat";
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `surat_persetujuan_perjalanan_dinas_${nomorSurat.split("/")[0]}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setStatusMsg({ type: "success", text: `Surat berhasil dibuat dengan nomor: ${nomorSurat}` });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Terjadi kesalahan sistem." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 text-slate-800">
      <div className="bg-[#700D0A]/10 border border-[#700D0A]/20 rounded-xl p-4 text-xs sm:text-sm text-[#700D0A]">
        Jenis surat ini isinya sudah baku secara regulasi, jadi <strong className="font-bold">tidak memakai AI</strong> — sistem langsung mengisi template berdasarkan data yang Anda masukkan.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kabupaten Tujuan</label>
          <input
            type="text"
            placeholder="Contoh: Kampar"
            value={kabupaten}
            onChange={(e) => setKabupaten(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Kota / Ibukota Kabupaten</label>
          <input
            type="text"
            placeholder="Contoh: Bangkinang"
            value={kota}
            onChange={(e) => setKota(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Nomor Surat Rujukan Pemohon</label>
          <input
            type="text"
            placeholder="Contoh: 55/RT.02.1-SD/1410/2026"
            value={nomorRujukan}
            onChange={(e) => setNomorRujukan(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Tanggal Surat Rujukan</label>
          <input
            type="text"
            placeholder="Contoh: 1 Agustus 2026"
            value={tanggalRujukan}
            onChange={(e) => setTanggalRujukan(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Sifat</label>
          <select
            value={sifat}
            onChange={(e) => setSifat(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
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
            className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:border-[#700D0A] focus:ring-1 focus:ring-[#700D0A] outline-none transition-all"
          />
        </div>
      </div>

      <div className="border-t border-slate-200 pt-6">
        <h3 className="text-base font-extrabold text-slate-800 mb-1">
          Daftar Pegawai Perjalanan Dinas (Halaman 2)
        </h3>
        <p className="text-xs text-slate-500 mb-4">Kolom Tujuan otomatis diisi &apos;KPU Provinsi Riau&apos; untuk semua baris.</p>

        <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white shadow-sm">
          <table className="w-full text-xs sm:text-sm text-left">
            <thead className="bg-[#700D0A] text-white font-bold border-b border-[#700D0A]">
              <tr>
                <th className="p-3 w-12 text-center">No</th>
                <th className="p-3 min-w-[150px]">Nama</th>
                <th className="p-3 min-w-[150px]">Jabatan</th>
                <th className="p-3 min-w-[140px]">Tanggal</th>
                <th className="p-3 min-w-[200px]">Dalam Rangka</th>
                <th className="p-3 w-12 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {pegawaiList.map((p, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 text-center font-bold text-slate-600">{idx + 1}</td>
                  <td className="p-2">
                    <input
                      type="text"
                      placeholder="Nama Pegawai"
                      value={p.nama}
                      onChange={(e) => handlePegawaiChange(idx, "nama", e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-slate-900 text-xs sm:text-sm focus:border-[#700D0A] outline-none"
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      placeholder="Jabatan"
                      value={p.jabatan}
                      onChange={(e) => handlePegawaiChange(idx, "jabatan", e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-slate-900 text-xs sm:text-sm focus:border-[#700D0A] outline-none"
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      placeholder="12 s.d 14 Mei 2026"
                      value={p.tanggal}
                      onChange={(e) => handlePegawaiChange(idx, "tanggal", e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-slate-900 text-xs sm:text-sm focus:border-[#700D0A] outline-none"
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      placeholder="Maksud perjalanan dinas..."
                      value={p.dalam_rangka}
                      onChange={(e) => handlePegawaiChange(idx, "dalam_rangka", e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-slate-900 text-xs sm:text-sm focus:border-[#700D0A] outline-none"
                    />
                  </td>
                  <td className="p-2 text-center">
                    <button
                      type="button"
                      onClick={() => handleRemovePegawai(idx)}
                      disabled={pegawaiList.length === 1}
                      className="p-1.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors disabled:opacity-20"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button
          type="button"
          onClick={handleAddPegawai}
          className="mt-3 flex items-center gap-1.5 text-xs font-bold text-[#700D0A] hover:text-[#590A08] transition-colors"
        >
          <Plus className="w-4 h-4" /> Tambah Baris Pegawai
        </button>
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
        disabled={loading}
        className="w-full bg-[#700D0A] hover:bg-[#590A08] text-white font-extrabold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
      >
        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileDown className="w-5 h-5" />}
        {loading ? "Memproses Dokumen..." : "Buat Surat Persetujuan Perjalanan Dinas (.docx)"}
      </button>
    </form>
  );
}
