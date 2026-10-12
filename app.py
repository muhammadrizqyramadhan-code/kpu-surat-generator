"""
app.py
-------
Aplikasi Streamlit: Generator Surat Resmi Otomatis untuk KPU Provinsi Riau.

Jalankan dengan:
    streamlit run app.py

Sistem HYBRID, 3 alur tergantung jenis surat:
1. "Persetujuan Perjalanan Dinas" -> PURE template-fill, TANPA AI (isinya
   baku secara regulasi).
2. "Undangan Rapat" -> hybrid: AI cuma nyusun kalimat pembuka singkat,
   jadwal (Hari/Tanggal/Waktu/Tempat/Agenda) input terstruktur, dan ada
   toggle Internal (daftar penerima bernomor) / Eksternal (1 baris tujuan).
3. Jenis lain (Permohonan Data, Pemberitahuan, Surat Permohonan) -> AI
   nyusun seluruh isi dari poin-poin bebas. "Surat Permohonan" tambahan
   field Perihal & Kode Klasifikasi karena topiknya bebas/bervariasi.

Format dokumen (kop, tabel nomor, blok tanda tangan) sudah disesuaikan
mengikuti template resmi KPU Provinsi Riau -- lihat doc_generator.py.
"""

import base64
import os
import pandas as pd
import streamlit as st

from llm_service_local import generate_isi_surat  # model lokal via Ollama (default, tanpa data keluar)
# Alternatif lain (tinggal aktifkan salah satu, komentari yang atas):
# from llm_service_gemini import generate_isi_surat  # Gemini API, gratis, untuk testing awal
# from llm_service import generate_isi_surat          # Claude API, berbayar, untuk demo final

from doc_generator import (
    TEMPLATES, HARI_INDONESIA, BULAN_INDONESIA,
    buat_dokumen_surat, buat_dokumen_perjalanan_dinas,
)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo_kpu.jpg")


def _render_header():
    logo_base64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

    logo_img = (
        f'<img src="data:image/jpeg;base64,{logo_base64}" style="height: 52px; width: auto; object-fit: contain;">'
        if logo_base64 else ""
    )

    header_html = f"""
    <div style="
        background-color: #4A000A;
        padding: 14px 24px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.18);
    ">
        {logo_img}
        <div style="
            width: 2px;
            height: 40px;
            background-color: #D4AF37;
            border-radius: 1px;
        "></div>
        <div style="display: flex; flex-direction: column; justify-content: center; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;">
            <span style="color: #FFFFFF; font-size: 26px; font-weight: 800; line-height: 1.1; letter-spacing: 0.8px;">KPU</span>
            <span style="color: #D4AF37; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin-top: 2px;">PROVINSI RIAU</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


st.set_page_config(
    page_title="Generator Surat Resmi - KPU Provinsi Riau",
    layout="wide",
)

_render_header()

st.subheader("Generator Surat Resmi Otomatis")
st.caption(
    "Sistem Otomatisasi Penyusunan Surat Resmi Berbasis Natural Language "
    "Processing — Komisi Pemilihan Umum Provinsi Riau"
)

jenis_surat = st.selectbox("Jenis surat", list(TEMPLATES.keys()))


def _tanggal_indonesia_str(d) -> str:
    return f"{d.day} {BULAN_INDONESIA[d.month - 1]} {d.year}"


def _pengaturan_penandatangan(key_prefix="", default_jabatan="Sekretaris", default_nama="RUDINAL B"):
    with st.expander("Pengaturan penandatangan (opsional)"):
        jabatan = st.text_input("Jabatan penandatangan", value=default_jabatan, key=f"{key_prefix}jabatan_ttd")
        nama = st.text_input("Nama penandatangan", value=default_nama, key=f"{key_prefix}nama_ttd")
    return jabatan, nama


# ============================================================================
# ALUR 1 — Persetujuan Perjalanan Dinas: PURE FORM-FILL, TANPA AI
# ============================================================================
if jenis_surat == "Persetujuan Perjalanan Dinas":
    st.info(
        "Jenis surat ini isinya sudah baku secara regulasi, jadi **tidak "
        "memakai AI** — sistem langsung mengisi template berdasarkan data "
        "yang kamu masukkan di bawah.",
        icon="ℹ️",
    )

    st.subheader("Data Surat")
    col1, col2 = st.columns(2)
    with col1:
        kabupaten = st.text_input(
            "Kabupaten tujuan",
            placeholder="Kampar",
            help="Dipakai di 'Yth. Sekretaris KPU Kabupaten ...', judul tabel "
                 "halaman 2, dan Tembusan.",
        )
    with col2:
        kota = st.text_input(
            "Kota/ibukota kabupaten",
            placeholder="Bangkinang",
            help="Dipakai di bawah 'di -' (BEDA dari nama kabupaten -- "
                 "misal Kab. Kepulauan Meranti ibukotanya Selatpanjang).",
        )

    col3, col4 = st.columns(2)
    with col3:
        nomor_rujukan = st.text_input(
            "Nomor surat rujukan (dari pemohon)",
            placeholder="55/RT.02.1-SD/1410/2026",
        )
    with col4:
        tanggal_rujukan = st.text_input(
            "Tanggal surat rujukan",
            placeholder="1 Agustus 2026",
        )

    col5, col6 = st.columns(2)
    with col5:
        sifat = st.selectbox("Sifat", ["Segera", "Penting", "Biasa", "-"])
    with col6:
        lampiran = st.text_input("Lampiran", value="1 (satu) lembar")

    st.subheader("Daftar Pegawai yang Melaksanakan Perjalanan Dinas")
    st.caption(
        "Kolom Tujuan otomatis diisi 'KPU Provinsi Riau' untuk semua baris. "
        "Klik tanda '+' di baris terakhir tabel untuk menambah pegawai."
    )
    default_df = pd.DataFrame(
        [{"Nama": "", "Jabatan": "", "Tanggal": "", "Dalam Rangka": ""}]
    )
    pegawai_df = st.data_editor(
        default_df,
        num_rows="dynamic",
        use_container_width=True,
        key="pegawai_editor",
        column_config={
            "Nama": st.column_config.TextColumn(width="medium"),
            "Jabatan": st.column_config.TextColumn(width="medium"),
            "Tanggal": st.column_config.TextColumn(
                width="small", help="Contoh: 12 s.d 14 Mei 2026"
            ),
            "Dalam Rangka": st.column_config.TextColumn(width="large"),
        },
    )

    jabatan_ttd, nama_ttd = _pengaturan_penandatangan("pd_")

    if st.button("Buat Surat Persetujuan Perjalanan Dinas", type="primary", use_container_width=True):
        if not kabupaten.strip() or not kota.strip() or not nomor_rujukan.strip() or not tanggal_rujukan.strip():
            st.warning("Mohon lengkapi semua data surat (kabupaten, kota, nomor & tanggal rujukan).")
        else:
            pegawai_list = [
                {
                    "nama": row["Nama"],
                    "jabatan": row["Jabatan"],
                    "tanggal": row["Tanggal"],
                    "dalam_rangka": row["Dalam Rangka"],
                }
                for _, row in pegawai_df.iterrows()
                if str(row["Nama"]).strip()
            ]
            if not pegawai_list:
                st.warning("Mohon isi minimal 1 pegawai di tabel daftar perjalanan dinas.")
            else:
                path, nomor = buat_dokumen_perjalanan_dinas(
                    kabupaten=kabupaten.strip(),
                    kota=kota.strip(),
                    nomor_rujukan=nomor_rujukan.strip(),
                    tanggal_rujukan=tanggal_rujukan.strip(),
                    pegawai_list=pegawai_list,
                    sifat=sifat,
                    lampiran=lampiran,
                    jabatan_penandatangan=jabatan_ttd,
                    nama_penandatangan=nama_ttd,
                )
                st.success(f"Surat berhasil dibuat dengan nomor: **{nomor}** (2 halaman)")
                with open(path, "rb") as f:
                    st.download_button(
                        "⬇️ Unduh surat.docx",
                        f,
                        file_name=path.split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

# ============================================================================
# ALUR 2 — Undangan Rapat: hybrid (AI untuk pembuka, jadwal terstruktur)
# ============================================================================
elif jenis_surat == "Undangan Rapat":
    st.subheader("Buat Undangan Rapat")

    tipe_undangan = st.radio(
        "Tipe undangan",
        ["Eksternal (ke Kabupaten/Kota)", "Internal (ke pejabat/pegawai internal)"],
        horizontal=True,
    )
    is_internal = tipe_undangan.startswith("Internal")

    col_input, col_preview = st.columns(2, gap="large")

    with col_input:
        penerima_list = []
        tujuan, kota_tujuan = "", ""
        if is_internal:
            st.caption("Daftar penerima (bisa tambah/hapus baris):")
            default_penerima = pd.DataFrame({
                "Penerima": [
                    "Anggota KPU Provinsi Riau",
                    "Sekretaris KPU Provinsi Riau",
                    "Pejabat Struktural di Lingkungan KPU Provinsi Riau",
                ]
            })
            penerima_df = st.data_editor(
                default_penerima, num_rows="dynamic", use_container_width=True,
                key="penerima_editor",
            )
            penerima_list = [p.strip() for p in penerima_df["Penerima"] if str(p).strip()]
        else:
            tujuan = st.text_input(
                "Ditujukan kepada (Yth.)",
                placeholder="Sekretaris KPU Kabupaten/Kota Se Provinsi Riau",
            )
            kota_tujuan = st.text_input(
                "Kota tujuan (opsional -- kosongkan untuk 'di Tempat')",
                placeholder="",
            )

        col_sifat, col_lampiran = st.columns(2)
        with col_sifat:
            sifat = st.selectbox("Sifat", ["Segera", "Penting", "Biasa", "-"])
        with col_lampiran:
            lampiran = st.text_input("Lampiran", value="1 (satu) Rangkap" if not is_internal else "-")

        poin_isi = st.text_area(
            "Poin singkat tujuan/latar belakang rapat (untuk kalimat pembuka -- AI yang susun)",
            height=90,
            placeholder="Contoh: rapat koordinasi evaluasi tugas jagsa & kebersihan kantor se-Riau",
        )

        st.markdown("**Jadwal Rapat**")
        col_hari, col_waktu = st.columns(2)
        with col_hari:
            tanggal_rapat = st.date_input("Tanggal rapat")
        with col_waktu:
            waktu_rapat = st.text_input("Waktu", placeholder="Pukul 09.00 WIB s.d selesai")
        tempat_rapat = st.text_input("Tempat", placeholder="Ruangan Rapat Lt.2 KPU Provinsi Riau")
        link_zoom = st.text_input("Link Zoom (opsional, kosongkan kalau tatap muka)", placeholder="")

        st.caption("Agenda rapat (bisa tambah/hapus baris):")
        default_agenda = pd.DataFrame({"Agenda": [""]})
        agenda_df = st.data_editor(
            default_agenda, num_rows="dynamic", use_container_width=True, key="agenda_editor",
        )
        agenda_list = [a.strip() for a in agenda_df["Agenda"] if str(a).strip()]

        penutup_default = (
            "Demikian disampaikan, atas kehadirannya diucapkan terima kasih."
            if is_internal else TEMPLATES["Undangan Rapat"]["penutup"]
        )
        penutup_custom = st.text_input("Kalimat penutup", value=penutup_default)

        default_jabatan_und = "Ketua Komisi Pemilihan Umum Provinsi Riau" if is_internal else "Sekretaris"
        default_nama_und = "RUSIDI RUSDAN" if is_internal else "RUDINAL B"
        jabatan_ttd, nama_ttd = _pengaturan_penandatangan("und_", default_jabatan=default_jabatan_und, default_nama=default_nama_und)

        generate_clicked = st.button("Susun Surat", type="primary", use_container_width=True)

        if generate_clicked:
            if not poin_isi.strip() or (is_internal and not penerima_list) or (not is_internal and not tujuan.strip()):
                st.warning("Mohon lengkapi field yang wajib (penerima & poin tujuan rapat).")
            else:
                with st.spinner("AI sedang menyusun kalimat pembuka..."):
                    try:
                        isi = generate_isi_surat(jenis_surat, tujuan or "internal KPU Provinsi Riau", poin_isi)
                        st.session_state["und_isi"] = isi
                        st.session_state["und_jadwal"] = {
                            "hari": HARI_INDONESIA[tanggal_rapat.weekday()],
                            "tanggal": _tanggal_indonesia_str(tanggal_rapat),
                            "waktu": waktu_rapat,
                            "tempat": tempat_rapat,
                            "link_zoom": link_zoom,
                            "agenda": agenda_list,
                        }
                        st.session_state["und_tujuan"] = tujuan
                        st.session_state["und_kota"] = kota_tujuan
                        st.session_state["und_penerima"] = penerima_list
                        st.session_state["und_sifat"] = sifat
                        st.session_state["und_lampiran"] = lampiran
                        st.session_state["und_penutup"] = penutup_custom
                        st.session_state["und_jabatan_ttd"] = jabatan_ttd
                        st.session_state["und_nama_ttd"] = nama_ttd
                        st.session_state.pop("und_saved_path", None)
                    except Exception as e:
                        st.error(f"Gagal menyusun surat: {e}")

    with col_preview:
        st.subheader("Pratinjau Surat")
        if "und_isi" not in st.session_state:
            st.info("Isi form di sebelah kiri, lalu klik **Susun Surat** untuk melihat hasilnya di sini.")
        else:
            edited_isi = st.text_area(
                "Kalimat pembuka hasil AI (bisa diedit)",
                value=st.session_state["und_isi"],
                height=120,
            )
            st.session_state["und_isi"] = edited_isi
            st.json(st.session_state["und_jadwal"], expanded=False)

            if st.button("Buat File Word (.docx)", use_container_width=True):
                path, nomor = buat_dokumen_surat(
                    jenis_surat="Undangan Rapat",
                    tujuan=st.session_state["und_tujuan"],
                    isi=st.session_state["und_isi"],
                    kota_tujuan=st.session_state["und_kota"],
                    sifat=st.session_state["und_sifat"],
                    lampiran=st.session_state["und_lampiran"],
                    jabatan_penandatangan=st.session_state["und_jabatan_ttd"],
                    nama_penandatangan=st.session_state["und_nama_ttd"],
                    penerima_list=st.session_state["und_penerima"] or None,
                    jadwal=st.session_state["und_jadwal"],
                    penutup_override=st.session_state["und_penutup"],
                )
                st.session_state["und_saved_path"] = path
                st.session_state["und_saved_nomor"] = nomor

            if "und_saved_path" in st.session_state:
                st.success(f"Surat berhasil dibuat dengan nomor: **{st.session_state['und_saved_nomor']}**")
                with open(st.session_state["und_saved_path"], "rb") as f:
                    st.download_button(
                        "⬇️ Unduh surat.docx",
                        f,
                        file_name=st.session_state["und_saved_path"].split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

# ============================================================================
# ALUR 3 — Jenis surat lain (Permohonan Data, Pemberitahuan, Surat Permohonan)
# ============================================================================
else:
    is_permohonan_generik = jenis_surat == "Surat Permohonan"

    col_input, col_preview = st.columns(2, gap="large")

    with col_input:
        st.subheader("Buat Surat Baru")

        perihal_custom, kode_custom = None, None
        if is_permohonan_generik:
            perihal_custom = st.text_input(
                "Perihal surat",
                placeholder="Permohonan Peminjaman Bus dan Tenda Kegiatan Capacity Building",
            )
            kode_custom = st.text_input(
                "Kode klasifikasi arsip",
                placeholder="RT.03.3-SD",
                help="Tanyakan ke pembimbing lapangan kalau belum tahu kodenya.",
            )

        tujuan = st.text_input(
            "Ditujukan kepada (Yth.)",
            placeholder="Sekretaris KPU Kabupaten Bengkalis",
        )
        kota_tujuan = st.text_input(
            "Kota tujuan (opsional -- kosongkan kalau surat ditujukan ke "
            "banyak pihak/tidak spesifik satu kota, nanti otomatis jadi "
            "'di Tempat')",
            placeholder="Bengkalis",
        )

        col_sifat, col_lampiran = st.columns(2)
        with col_sifat:
            sifat = st.selectbox("Sifat", ["Segera", "Penting", "Biasa", "-"])
        with col_lampiran:
            lampiran = st.text_input("Lampiran", value="-")

        poin_isi = st.text_area(
            "Poin-poin isi surat (boleh bahasa bebas/santai)",
            height=140,
            placeholder=(
                "Contoh: Rapat tanggal 20 Juli 2026, jam 09.00 WIB, di ruang "
                "rapat utama, membahas jadwal tahapan Pilkada 2027"
            ),
        )

        penutup_custom = st.text_input(
            "Kalimat penutup (bisa diedit)",
            value=TEMPLATES[jenis_surat]["penutup"] or "",
        )

        jabatan_ttd, nama_ttd = _pengaturan_penandatangan("gen_")

        generate_clicked = st.button("Susun Surat", type="primary", use_container_width=True)

        if generate_clicked:
            if not tujuan.strip() or not poin_isi.strip():
                st.warning("Mohon isi 'Ditujukan kepada' dan 'Poin isi surat' terlebih dahulu.")
            elif is_permohonan_generik and (not perihal_custom.strip() or not kode_custom.strip()):
                st.warning("Mohon isi Perihal dan Kode klasifikasi arsip untuk Surat Permohonan.")
            else:
                with st.spinner("AI sedang menyusun isi surat... (percobaan pertama bisa lambat karena model sedang dimuat)"):
                    try:
                        isi = generate_isi_surat(jenis_surat, tujuan, poin_isi)
                        st.session_state["isi"] = isi
                        st.session_state["jenis_surat"] = jenis_surat
                        st.session_state["tujuan"] = tujuan
                        st.session_state["kota_tujuan"] = kota_tujuan
                        st.session_state["sifat"] = sifat
                        st.session_state["lampiran"] = lampiran
                        st.session_state["jabatan_ttd"] = jabatan_ttd
                        st.session_state["nama_ttd"] = nama_ttd
                        st.session_state["perihal_custom"] = perihal_custom
                        st.session_state["kode_custom"] = kode_custom
                        st.session_state["penutup_custom"] = penutup_custom
                        st.session_state.pop("last_saved_path", None)
                    except Exception as e:
                        st.error(f"Gagal menyusun surat: {e}")

    with col_preview:
        st.subheader("Pratinjau Surat")

        if "isi" not in st.session_state or st.session_state.get("jenis_surat") != jenis_surat:
            st.info("Isi form di sebelah kiri, lalu klik **Susun Surat** untuk melihat hasilnya di sini.")
        else:
            edited_isi = st.text_area(
                "Hasil susunan AI (bisa diedit dulu sebelum diunduh)",
                value=st.session_state["isi"],
                height=200,
            )
            st.session_state["isi"] = edited_isi

            if st.button("Buat File Word (.docx)", use_container_width=True):
                path, nomor = buat_dokumen_surat(
                    jenis_surat=st.session_state["jenis_surat"],
                    tujuan=st.session_state["tujuan"],
                    isi=st.session_state["isi"],
                    kota_tujuan=st.session_state["kota_tujuan"],
                    sifat=st.session_state["sifat"],
                    lampiran=st.session_state["lampiran"],
                    jabatan_penandatangan=st.session_state["jabatan_ttd"],
                    nama_penandatangan=st.session_state["nama_ttd"],
                    perihal_override=st.session_state.get("perihal_custom") or None,
                    kode_klasifikasi_override=st.session_state.get("kode_custom") or None,
                    penutup_override=st.session_state.get("penutup_custom") or None,
                )
                st.session_state["last_saved_path"] = path
                st.session_state["last_saved_nomor"] = nomor

            if "last_saved_path" in st.session_state:
                st.success(f"Surat berhasil dibuat dengan nomor: **{st.session_state['last_saved_nomor']}**")
                with open(st.session_state["last_saved_path"], "rb") as f:
                    st.download_button(
                        "⬇️ Unduh surat.docx",
                        f,
                        file_name=st.session_state["last_saved_path"].split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )

st.divider()
st.caption(
    "Format dokumen (kop, tabel nomor, blok tanda tangan) sudah disesuaikan "
    "dengan template resmi KPU Provinsi Riau. Kode klasifikasi arsip & kode "
    "satuan kerja di nomor surat masih perlu diverifikasi ke pembimbing "
    "lapangan -- lihat catatan di doc_generator.py."
)
