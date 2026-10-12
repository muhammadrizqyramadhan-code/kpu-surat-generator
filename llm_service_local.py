"""
llm_service_local.py
----------------------
Versi ALTERNATIF llm_service.py yang memakai model AI LOKAL (jalan di komputer
sendiri lewat Ollama). TIDAK ADA data yang dikirim ke internet sama sekali --
semua pemrosesan terjadi di perangkat sendiri. Ini opsi PALING AMAN untuk
data surat resmi asli, karena tidak ada isu data dipakai training pihak ketiga.

PERSIAPAN (sekali saja, sebelum menjalankan app.py):
1. Install Ollama: https://ollama.com/download (pilih versi Windows)
2. Buka terminal/PowerShell, jalankan:
       ollama pull qwen3:8b
   (download sekali ~5GB, tersimpan permanen di komputer)
3. Ollama otomatis jalan di background setelah install (server lokal di
   http://localhost:11434). Kalau belum jalan, buka terminal dan jalankan:
       ollama serve

Kenapa Qwen3 8B: dukungan bahasa Indonesia kuat, lisensi Apache 2.0 (bebas
dipakai instansi pemerintah tanpa masalah hukum), dan cukup ringan untuk
laptop dengan GPU 6GB+ VRAM (sesuai spek laptop gaming/RTX pada umumnya).

Catatan performa: percobaan PERTAMA setelah Ollama baru nyala biasanya lambat
(bisa >2 menit) karena model sedang dimuat dari disk ke memori/GPU.
Percobaan berikutnya jauh lebih cepat karena model sudah ada di memori.

Cara pakai: di app.py, ganti baris import jadi:
    from llm_service_local import generate_isi_surat
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

SYSTEM_PROMPT = """Kamu adalah asisten penyusun surat dinas resmi untuk Komisi Pemilihan Umum Provinsi Riau.

Tugasmu: mengubah poin-poin singkat yang diberikan staf menjadi paragraf ISI surat
yang formal, baku, dan sesuai kaidah bahasa Indonesia administrasi pemerintahan.

ATURAN PENTING:
1. Tulis HANYA bagian isi surat (paragraf pembuka penjelas + isi pokok).
2. JANGAN PERNAH menulis judul/header seperti "**Isi Surat**", "**Paragraf Pembuka**", atau judul sejenis.
3. JANGAN menulis nomor surat, kop surat, tanggal, "Kepada Yth", atau kalimat
   penutup baku ("Demikian...") -- semua itu sudah ditangani sistem template.
4. Jangan mengarang detail (tanggal, waktu, tempat, dsb) yang tidak disebutkan
   di poin-poin staf. Kalau ada detail yang kurang jelas, tulis apa adanya.
5. Gunakan bahasa formal, lugas, dan ringkas -- maksimal 2-3 paragraf pendek.
6. Jangan gunakan simbol markdown (tanpa **, tanpa bullet list) -- tulis dalam bentuk
   paragraf naratif seperti surat dinas pada umumnya.
7. Langsung jawab isi suratnya saja, tanpa menampilkan proses berpikir/reasoning.
"""


def generate_isi_surat(jenis_surat: str, tujuan: str, poin_isi: str) -> str:
    """Panggil model lokal (via Ollama) untuk menyusun isi surat formal.

    Tidak butuh API key -- yang dibutuhkan cuma Ollama sudah terinstall dan
    model 'qwen3:8b' sudah di-download (lihat instruksi di docstring atas).
    """
    user_prompt = f"""Jenis surat: {jenis_surat}
Ditujukan kepada: {tujuan}
Poin-poin isi (dari staf, bahasa bebas): {poin_isi}

Susun bagian isi surat resmi berdasarkan poin-poin di atas. /no_think"""
    # "/no_think" mematikan mode reasoning bawaan Qwen3 supaya output langsung
    # berupa isi surat, tanpa proses berpikir yang terekspos ke hasil akhir.

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=300,  # loading model pertama kali bisa lama, kasih ruang lebih
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Tidak bisa terhubung ke Ollama di localhost:11434. Pastikan "
            "Ollama sudah terinstall dan sedang berjalan. Kalau belum "
            "otomatis jalan, buka terminal terpisah lalu jalankan: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Model lokal terlalu lama merespons (>300 detik). Coba jalankan "
            "'ollama run qwen3:8b' langsung di terminal untuk tes apakah "
            "modelnya jalan normal, dan cek apakah GPU terdeteksi (lihat "
            "Task Manager > Performance > GPU saat generate)."
        )

    data = response.json()
    return data["message"]["content"].strip()
