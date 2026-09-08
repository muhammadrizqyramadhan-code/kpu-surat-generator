# Generator Surat Resmi Otomatis — KPU Provinsi Riau

Prototype sistem otomatisasi penyusunan surat resmi berbasis Natural Language
Processing (NLP), dengan pendekatan **hybrid** -- 3 alur berbeda tergantung
jenis surat yang dipilih:

1. **"Persetujuan Perjalanan Dinas"** → **PURE template-fill, TANPA AI**,
   karena isinya sudah baku secara regulasi (3 poin ketentuan Permenkeu dst
   selalu sama persis di semua contoh surat asli). Staf cukup isi data yang
   memang berubah: kabupaten/kota tujuan, nomor & tanggal surat rujukan, dan
   daftar pegawai yang dinas (tabel dinamis, bisa tambah baris). Hasilnya
   dokumen 2 halaman: halaman 1 surat persetujuan, halaman 2 daftar pegawai
   bentuk tabel bergaris.
2. **"Undangan Rapat"** → **hybrid**: AI cuma menyusun 1-2 kalimat pembuka
   dari poin singkat yang diketik staf, sedangkan jadwal (Hari/Tanggal/
   Waktu/Tempat/Agenda) diisi lewat **field terstruktur** (Agenda bisa tambah
   poin dinamis). Ada toggle **Internal** (daftar penerima bernomor, mis.
   "Anggota KPU Provinsi Riau", dst) vs **Eksternal** (1 baris tujuan, mis.
   "Sekretaris KPU Kabupaten/Kota Se Provinsi Riau").
3. **Jenis lain** (Permohonan Data, Pemberitahuan, **Surat Permohonan**) →
   AI menyusun seluruh isi dari poin-poin bebas, sama seperti sebelumnya.
   **"Surat Permohonan"** adalah jenis generik untuk topik permohonan yang
   variatif (pinjam sarana, dll) -- staf isi manual Perihal & Kode
   Klasifikasi Arsip karena tiap topik permohonan punya kode beda-beda dan
   tidak bisa ditebak semua dari awal.

## Format dokumen sudah disesuaikan dengan template resmi KPU Provinsi Riau

`doc_generator.py` disusun berdasarkan analisis beberapa contoh surat resmi
asli (Persetujuan Perjalanan Dinas dari 4 kabupaten berbeda, Undangan Rakor,
Undangan Rapat Rutin internal, dan Surat Permohonan). Detail yang direplikasi:

- Ukuran kertas **F4/Folio (21 x 33 cm)**, bukan A4
- Font **Arial 12pt**
- Kop surat: logo asli KPU (di `assets/logo_kpu.jpg`, diekstrak dari template
  asli) + nama lembaga + alamat, dengan **garis pemisah GANDA TIPIS** (`double` 1.5pt:
  dua garis tipis sejajar, sesuai format surat asli KPU)
- Blok Nomor/Sifat/Lampiran/Perihal dengan tanggal sejajar baris Nomor
- Format nomor surat: `{urutan}/{kode klasifikasi}/14/1/{tahun}`
- Placeholder `${ttd_pengirim}` di blok tanda tangan dipertahankan apa
  adanya (ditemukan di template asli -- kemungkinan dipakai proses lain di
  kantor untuk mengisi tanda tangan digital/scan secara otomatis)
- Untuk Persetujuan Perjalanan Dinas: kabupaten (mis. "Kampar") dan kota/
  ibukota (mis. "Bangkinang") adalah **dua field terpisah** -- jangan
  disamakan, karena di beberapa kabupaten namanya beda (Kab. Kepulauan
  Meranti -> ibukotanya Selatpanjang, bukan "Meranti")
- Untuk Undangan Rapat Internal: format "di -" pakai "tempat" huruf kecil
  (beda dari mode Eksternal yang pakai "Tempat" huruf besar), dan penerima
  dirender sebagai daftar bernomor dengan tanda baca otomatis (";" antar
  item, "; dan" di item kedua-terakhir, "." di item terakhir)

**Catatan teknis penting:** semua tabel di dokumen (kop, blok nomor, blok
tanda tangan, blok jadwal, tabel daftar pegawai) memakai *fixed column
width* yang di-set secara eksplisit di level `tblGrid` (bukan cuma lebar per
sel) -- ini perlu supaya Microsoft Word menghormati lebar kolom yang sudah
ditentukan. Kalau cuma di-set di level sel biasa, Word bisa melakukan
auto-fit sendiri dan bikin layout berantakan, meskipun tampilannya
normal-normal saja kalau dibuka di LibreOffice.

**Yang masih perlu diverifikasi ke pembimbing lapangan** (ditandai `TODO`
di `doc_generator.py`):
- Apakah kode `14/1` di nomor surat selalu tetap untuk semua jenis surat,
  atau berbeda tergantung bagian/unit pengirim
- Kode klasifikasi arsip (`TU.01-SD`, `PP.05-Und`, dst) untuk jenis surat
  yang belum ada contohnya (Permohonan Data, Pemberitahuan) -- saat ini
  masih tebakan berdasarkan pola yang ada, bukan dikonfirmasi
- Fungsi placeholder `${ttd_pengirim}` -- apakah memang ada sistem lain
  yang memprosesnya, supaya output kita tetap kompatibel
- Kalimat ketentuan Perjalanan Dinas mengandung typo asli ("bepedoman"
  bukan "berpedoman") -- dipertahankan demi konsistensi wording persis
  dengan template resmi, tapi bisa dikoreksi kalau memang typo

## Cara kerja (arsitektur singkat)

```
Staf isi form (Streamlit)
   -> llm_service_local.py memanggil model AI lokal (menyusun ISI surat saja)
   -> doc_generator.py menyisipkan isi tsb ke TEMPLATE tetap (kop, nomor, penutup)
   -> hasil file .docx siap diunduh
```

Prinsip pentingnya: **AI tidak menentukan format surat** — struktur (kop
surat, posisi nomor, kalimat penutup baku, blok tanda tangan) di-hardcode di
`doc_generator.py`. AI hanya menyusun kalimat formal untuk bagian isi,
berdasarkan poin-poin yang diketik staf. Ini memastikan format surat selalu
konsisten meskipun isinya dibuat oleh AI.

## Struktur file

| File | Fungsi |
|---|---|
| `app.py` | Aplikasi Streamlit (form AI untuk surat variatif + form khusus Perjalanan Dinas) |
| `llm_service_local.py` | Model AI **lokal** via Ollama (default, tanpa data keluar) |
| `llm_service_gemini.py` | Alternatif: Gemini API (gratis, untuk testing) |
| `llm_service.py` | Alternatif: Claude API (berbayar, kualitas terbaik) |
| `doc_generator.py` | `buat_dokumen_surat()` untuk surat berbasis AI, `buat_dokumen_perjalanan_dinas()` untuk surat pure template-fill 2 halaman |
| `assets/logo_kpu.jpg` | Logo KPU asli, diekstrak dari template resmi |
| `requirements.txt` | Daftar library Python yang dibutuhkan |

## Pilihan LLM: Model Lokal (default), Gemini API, atau Claude API

| File | Provider | Biaya | Data keluar? | Cocok untuk |
|---|---|---|---|---|
| `llm_service_local.py` | Qwen3 8B via **Ollama** (jalan di laptop sendiri) | Gratis (sekali download) | **Tidak, 100% lokal** | **Surat resmi asli / data sensitif (default)** |
| `llm_service_gemini.py` | Gemini API (Google) | **Gratis**, tanpa kartu kredit | Ya (dipakai training di free tier) | Development & testing awal |
| `llm_service.py` | Claude API (Anthropic) | Berbayar (pay-as-you-go, murah) | Ya (ke server Anthropic) | Demo final, kualitas bahasa terbaik |

**Catatan privasi untuk Gemini (free tier):** data yang dikirim bisa dipakai
Google untuk peningkatan produk mereka. Jangan kirim data surat asli/sensitif
selama masih pakai free tier — cukup pakai data contoh/dummy untuk testing.

## Instalasi

1. Install dependency:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Default: Model Lokal via Ollama** (tidak perlu API key sama sekali):
   - Download & install Ollama di [ollama.com/download](https://ollama.com/download)
   - Buka terminal/PowerShell, jalankan:
     ```bash
     ollama pull qwen3:8b
     ```
     (sekali download ~5GB, tersimpan permanen)
   - Ollama otomatis jalan di background setelah install. Kalau belum,
     jalankan `ollama serve` di terminal terpisah.
   - `app.py` secara default sudah pakai `from llm_service_local import generate_isi_surat`

   **Catatan performa:** percobaan generate PERTAMA setelah Ollama baru nyala
   biasanya lambat (model sedang dimuat ke memori/GPU) -- bisa >1-2 menit.
   Percobaan berikutnya jauh lebih cepat. Kalau lambat terus-menerus, cek GPU
   terdeteksi dengan benar (Task Manager > Performance > GPU saat generate).

   **Opsi lain (tinggal ganti baris import di `app.py`):**

   - **Gemini API (gratis, untuk testing awal):**
     - Buat API key gratis di [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
     - Set environment variable `GEMINI_API_KEY`
     - Di `app.py`: `from llm_service_gemini import generate_isi_surat`

   - **Claude API (berbayar, untuk demo final):**
     - Dapatkan API key di [console.anthropic.com](https://console.anthropic.com)
     - Set environment variable `ANTHROPIC_API_KEY`
     - Di `app.py`: `from llm_service import generate_isi_surat`

3. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

   Browser akan otomatis terbuka di `http://localhost:8501`.

## Yang perlu disesuaikan sebelum dipakai "serius" di kantor

- **Kode nomor surat**: verifikasi kode `14/1` dan kode klasifikasi arsip
  per jenis surat ke pembimbing lapangan (lihat catatan di atas)
- **Nama & jabatan penanda tangan**: sudah bisa diatur lewat form (expander
  "Pengaturan penandatangan"), defaultnya "Sekretaris" / "RUDINAL B"
- **Jenis surat lain**: tambah entri baru di dict `TEMPLATES` pada
  `doc_generator.py` untuk menambah jenis surat (mis. Surat Tugas, Surat
  Keterangan, dll)
- **Placeholder `${ttd_pengirim}`**: konfirmasi ke kantor apakah ada proses
  lain yang memprosesnya

## Menambah jenis surat baru

Tinggal tambahkan entri baru di `TEMPLATES` (dalam `doc_generator.py`):

```python
TEMPLATES = {
    ...
    "Surat Tugas": {
        "kode_klasifikasi": "TU.03-ST",  # sesuaikan dengan kode arsip yang benar
        "perihal": "Surat Tugas",
        "penutup": "Demikian surat tugas ini dibuat untuk dilaksanakan dengan penuh tanggung jawab.",
    },
}
```

Jenis surat baru otomatis muncul di dropdown aplikasi.
