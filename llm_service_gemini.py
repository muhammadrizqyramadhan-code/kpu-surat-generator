"""
llm_service_gemini.py
-----------------------
Versi ALTERNATIF dari llm_service.py, memakai Google Gemini API (gratis,
tanpa kartu kredit) alih-alih Claude API. Cocok dipakai untuk testing/
development selama belum ada budget buat top-up Claude API.

Cara pakai: di app.py, ganti baris
    from llm_service import generate_isi_surat
menjadi
    from llm_service_gemini import generate_isi_surat

PENTING (privasi): free tier Gemini API bisa memakai data yang kamu kirim
untuk peningkatan produk Google. JANGAN kirim data surat asli/sensitif ke
sini selama masih pakai free tier -- cukup pakai data contoh/dummy untuk
development dan demo.
"""

import os
import google.generativeai as genai

# Model gratis di free tier (per Juli 2026). Kalau "gemini-2.5-flash" kena
# limit/berubah nama, cek daftar model terbaru di https://ai.google.dev/gemini-api/docs/models
MODEL = "gemini-2.5-flash"

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
"""


def generate_isi_surat(jenis_surat: str, tujuan: str, poin_isi: str) -> str:
    """Panggil Gemini API untuk menyusun isi surat formal.

    Membutuhkan environment variable GEMINI_API_KEY. Dapatkan API key gratis
    (tanpa kartu kredit) di https://aistudio.google.com/apikey
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum diatur. Set environment variable ini "
            "terlebih dahulu (lihat README.md bagian instalasi)."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL, system_instruction=SYSTEM_PROMPT)

    user_prompt = f"""Jenis surat: {jenis_surat}
Ditujukan kepada: {tujuan}
Poin-poin isi (dari staf, bahasa bebas): {poin_isi}

Susun bagian isi surat resmi berdasarkan poin-poin di atas."""

    response = model.generate_content(user_prompt)
    return response.text.strip()
