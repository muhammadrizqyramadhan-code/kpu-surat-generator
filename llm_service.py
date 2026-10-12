"""
llm_service.py
----------------
Modul ini bertugas memanggil Claude API untuk menyusun BAGIAN ISI surat resmi
(bukan seluruh surat) berdasarkan poin-poin singkat yang diketik staf.

Struktur baku surat (kop, nomor, kepada, penutup, tanda tangan) TIDAK dibuat
oleh AI -- itu ditangani oleh doc_generator.py agar formatnya selalu konsisten.
AI hanya "menerjemahkan" poin kasar staf menjadi paragraf formal.
"""

import os
import anthropic

# Model yang dipakai: Claude Haiku 4.5 -- cepat & murah, cukup untuk tugas
# menyusun kalimat formal seperti ini. Kalau butuh kualitas bahasa yang lebih
# halus, bisa ganti ke "claude-sonnet-5".
MODEL = "claude-haiku-4-5-20251001"

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
    """Panggil Claude API untuk menyusun isi surat formal.

    Membutuhkan environment variable ANTHROPIC_API_KEY (dapatkan API key
    di https://console.anthropic.com).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY belum diatur. Set environment variable ini "
            "terlebih dahulu (lihat README.md bagian instalasi)."
        )

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""Jenis surat: {jenis_surat}
Ditujukan kepada: {tujuan}
Poin-poin isi (dari staf, bahasa bebas): {poin_isi}

Susun bagian isi surat resmi berdasarkan poin-poin di atas."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()
