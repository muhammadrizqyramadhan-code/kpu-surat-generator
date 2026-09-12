"""
doc_generator.py
------------------
Menyusun surat resmi berbentuk file .docx sesuai STANDAR TEMPLATE ASLI
KPU Provinsi Riau (dianalisis dari 3 contoh surat resmi yang diberikan:
2x Persetujuan Perjalanan Dinas + 1x Undangan Rakor).

Detail yang direplikasi dari template asli:
- Ukuran kertas F4/Folio (21 x 33 cm) -- bukan A4
- Font Arial 12pt untuk body text
- Kop surat: logo di kiri, nama lembaga + alamat di kanan, garis pemisah tebal
- Blok Nomor/Sifat/Lampiran/Perihal dalam bentuk tabel tanpa border,
  dengan tanggal sejajar baris Nomor (rata kanan)
- Format nomor surat: {urutan}/{kode klasifikasi}/14/1/{tahun}
  (kode "14/1" ditemukan konsisten di semua contoh -- kemungkinan kode
  satuan kerja tetap KPU Provinsi Riau. SESUAIKAN kalau ternyata berbeda.)
- Placeholder ${ttd_pengirim} di blok tanda tangan -- dipertahankan supaya
  kompatibel kalau ada proses lain di kantor yang mengisi tanda tangan
  otomatis ke placeholder ini.
"""

import os
import re
import json
from datetime import datetime

from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------------------------------------------------------------------------
# Ukuran kertas & margin sesuai template asli (diukur dari file contoh)
# ---------------------------------------------------------------------------
PAGE_WIDTH = Inches(8.26875)    # ~21 cm (F4/Folio)
PAGE_HEIGHT = Inches(12.99375)  # ~33 cm (F4/Folio)
MARGIN_TOP = Cm(0.5)            # Margin atas pepet ke atas (~0.5 cm)
MARGIN_SIDE = Inches(1.0)       # Margin samping 2.54 cm
MARGIN_BOTTOM = Inches(1.0)     # Margin bawah 2.54 cm

BASE_FONT = "Arial"
BASE_SIZE = Pt(12)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_PATH_PNG = os.path.join(ASSETS_DIR, "logo_kpu.png")
LOGO_PATH_JPG = os.path.join(ASSETS_DIR, "logo_kpu.jpg")
LOGO_PATH = LOGO_PATH_PNG if os.path.exists(LOGO_PATH_PNG) else LOGO_PATH_JPG

# Kode satuan kerja tetap yang ditemukan konsisten di semua contoh surat.
# TODO: konfirmasi ke pembimbing lapangan apakah ini selalu tetap "14/1"
# untuk semua jenis surat, atau berubah tergantung bagian/unit pengirim.
KODE_SATKER_TETAP = "14/1"

# ---------------------------------------------------------------------------
# Template per jenis surat -- bagian yang BAKU (bukan hasil AI)
# ---------------------------------------------------------------------------
TEMPLATES = {
    "Undangan Rapat": {
        "kode_klasifikasi": "PP.05-Und",
        "perihal": "Undangan Rapat",
        "penutup": "Demikian disampaikan, untuk dilaksanakan sebagaimana mestinya.",
    },
    "Persetujuan Perjalanan Dinas": {
        "kode_klasifikasi": "TU.01-SD",
        "perihal": "Persetujuan Izin Perjalanan Dinas",
        "penutup": "Demikian untuk menjadi perhatian dan dilaksanakan.",
    },
    "Permohonan Data": {
        "kode_klasifikasi": "TU.02-SD",
        "perihal": "Permohonan Data",
        "penutup": (
            "Demikian surat permohonan ini kami sampaikan. Atas perhatian "
            "dan kerja sama Bapak/Ibu, kami ucapkan terima kasih."
        ),
    },
    "Pemberitahuan": {
        "kode_klasifikasi": "PP.05-PB",
        "perihal": "Pemberitahuan",
        "penutup": "Demikian disampaikan, untuk dilaksanakan sebagaimana mestinya.",
    },
    "Surat Permohonan": {
        # kode_klasifikasi & perihal SENGAJA kosong -- topik permohonan
        # macam-macam (pinjam sarana, minta data, dll), masing-masing punya
        # kode arsip beda, jadi diisi manual oleh staf lewat form, bukan
        # ditebak/di-hardcode di sini.
        "kode_klasifikasi": None,
        "perihal": None,
        "penutup": (
            "Demikian disampaikan, atas perkenan dan kerjasamanya "
            "disampaikan terima kasih."
        ),
    },
}

BULAN_INDONESIA = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

HARI_INDONESIA = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

_COUNTER_FILE = os.path.join(os.path.dirname(__file__), "nomor_surat_counter.json")


def _tanggal_indonesia(dt: datetime) -> str:
    return f"{dt.day} {BULAN_INDONESIA[dt.month - 1]} {dt.year}"


def generate_nomor_surat(jenis_surat: str, kode_override: str = None) -> str:
    """Nomor surat otomatis & berurutan, reset tiap tahun.
    Format: {urutan}/{kode_klasifikasi}/14/1/{tahun}, mengikuti pola yang
    ditemukan di template asli. kode_override dipakai untuk jenis surat yang
    kode klasifikasinya diisi manual per surat (mis. Surat Permohonan).
    """
    now = datetime.now()
    data = {}
    if os.path.exists(_COUNTER_FILE):
        with open(_COUNTER_FILE) as f:
            data = json.load(f)

    key = str(now.year)
    seq = data.get(key, 0) + 1
    data[key] = seq

    with open(_COUNTER_FILE, "w") as f:
        json.dump(data, f)

    kode = kode_override or TEMPLATES.get(jenis_surat, TEMPLATES["Pemberitahuan"])["kode_klasifikasi"]
    return f"{seq}/{kode}/{KODE_SATKER_TETAP}/{now.year}"


def _set_font(run, bold=False, size=BASE_SIZE, name=BASE_FONT):
    run.font.name = name
    run.font.size = size
    run.bold = bold


def _tambah_garis_bawah(paragraph, weight="12", val="double"):
    """Border bawah paragraf -- dipakai sebagai garis pemisah kop surat.

    Default 'double' (garis ganda kembar) dengan ketebalan tipis (weight="12" / 1.5pt)
    sesuai format surat asli KPU (dua garis tipis sejajar).
    """
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), val)
    bottom.set(qn("w:sz"), weight)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _set_lebar_kolom_fixed(table, widths_cm):
    """Paksa lebar kolom tabel supaya FIXED dan dihormati oleh Microsoft Word
    (bukan cuma LibreOffice). Tanpa ini, Word bisa mengabaikan table.columns[i].width
    dan melakukan auto-fit sendiri kalau total lebar melebihi lebar halaman,
    yang bikin layout berantakan (kolom ke-wrap aneh, teks ke-stretch).
    """
    table.autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr

    layout_el = OxmlElement("w:tblLayout")
    layout_el.set(qn("w:type"), "fixed")
    tblPr.append(layout_el)

    total_dxa = sum(int(w * 566.929) for w in widths_cm)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(total_dxa))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)

    # PENTING: update juga tblGrid -- ini yang sebenarnya menentukan lebar
    # kolom saat dirender (LibreOffice & Word). Tanpa ini, kolom tetap
    # kebagi rata sesuai grid default meskipun tcW tiap sel sudah diubah.
    tblGrid = tbl.tblGrid
    for gridCol in list(tblGrid.findall(qn("w:gridCol"))):
        tblGrid.remove(gridCol)
    for w in widths_cm:
        gridCol = OxmlElement("w:gridCol")
        gridCol.set(qn("w:w"), str(int(w * 566.929)))
        tblGrid.append(gridCol)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx >= len(widths_cm):
                continue
            cell.width = Cm(widths_cm[idx])
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:w"), str(int(widths_cm[idx] * 566.929)))
            tcW.set(qn("w:type"), "dxa")
            tcPr.append(tcW)


def _perkecil_margin_sel(table, cm_value=0.05):
    """Perkecil margin dalam (padding) tiap sel tabel. Default margin Word
    (~0.2cm tiap sisi) memakan cukup banyak ruang untuk kolom sempit seperti
    kolom titik dua, sampai bisa bikin kontennya kepotong/hilang."""
    val = str(int(cm_value * 566.929))
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = OxmlElement("w:tcMar")
            for side in ("top", "left", "bottom", "right"):
                el = OxmlElement(f"w:{side}")
                el.set(qn("w:w"), val)
                el.set(qn("w:type"), "dxa")
                tcMar.append(el)
            tcPr.append(tcMar)


def _hilangkan_border_tabel(table):
    """Hilangkan semua border tabel -- dipakai untuk tabel 'invisible'
    (kop surat, blok nomor, blok tanda tangan) yang di template asli
    juga tidak bergaris."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)
    tblPr.append(borders)


def _buat_kop_surat(doc: Document, is_internal: bool = False):
    """Kop surat KPU Provinsi Riau.
    - Eksternal: Logo di kiri (tabel 2 kolom).
    - Internal: Logo di tengah (centered single column di atas judul).
    """
    if is_internal:
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(0)
        p_logo.paragraph_format.space_after = Pt(2)
        if os.path.exists(LOGO_PATH):
            p_logo.add_run().add_picture(LOGO_PATH, height=Cm(2.5))
        else:
            r = p_logo.add_run("[LOGO]")
            _set_font(r)

        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.line_spacing = 1.0
        r1 = p1.add_run("KOMISI PEMILIHAN UMUM")
        _set_font(r1, bold=True, size=Pt(16))

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.0
        r2 = p2.add_run("PROVINSI RIAU")
        _set_font(r2, bold=True, size=Pt(16))

        p3 = doc.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_before = Pt(1)
        p3.paragraph_format.space_after = Pt(0)
        p3.paragraph_format.line_spacing = 1.0
        r3 = p3.add_run("Alamat: Jl. Gadjah Mada No. 200 Pekanbaru")
        _set_font(r3, size=Pt(11))
    else:
        table = doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_lebar_kolom_fixed(table, [2.5, 13.3])
        _hilangkan_border_tabel(table)
        _perkecil_margin_sel(table, cm_value=0.0)

        cell_logo, cell_text = table.rows[0].cells

        p_logo = cell_logo.paragraphs[0]
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(0)
        p_logo.paragraph_format.space_after = Pt(0)
        if os.path.exists(LOGO_PATH):
            p_logo.add_run().add_picture(LOGO_PATH, height=Cm(2.5))
        else:
            r = p_logo.add_run("[LOGO]")
            _set_font(r)

        p1 = cell_text.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.line_spacing = 1.0
        r1 = p1.add_run("KOMISI PEMILIHAN UMUM")
        _set_font(r1, bold=True, size=Pt(16))

        p2 = cell_text.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.0
        r2 = p2.add_run("PROVINSI RIAU")
        _set_font(r2, bold=True, size=Pt(16))

        p3 = cell_text.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_before = Pt(1)
        p3.paragraph_format.space_after = Pt(0)
        p3.paragraph_format.line_spacing = 1.0
        r3 = p3.add_run("Alamat: Jl. Gadjah Mada No. 200 Pekanbaru")
        _set_font(r3, size=Pt(11))

    # baris kontak (telp kiri, email kanan) -- tabel 2 kolom terpisah
    kontak = doc.add_table(rows=1, cols=2)
    _set_lebar_kolom_fixed(kontak, [7.9, 7.9])
    _hilangkan_border_tabel(kontak)
    c_telp, c_email = kontak.rows[0].cells
    p_telp = c_telp.paragraphs[0]
    p_telp.paragraph_format.space_before = Pt(0)
    p_telp.paragraph_format.space_after = Pt(0)
    r_telp = p_telp.add_run("Telp. (0761) 858361")
    _set_font(r_telp, size=Pt(11))
    p_email = c_email.paragraphs[0]
    p_email.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_email.paragraph_format.space_before = Pt(0)
    p_email.paragraph_format.space_after = Pt(0)
    r_email = p_email.add_run("Email: prov_riau@kpu.go.id")
    _set_font(r_email, size=Pt(11))

    p_garis = doc.add_paragraph()
    p_garis.paragraph_format.space_before = Pt(0)
    p_garis.paragraph_format.space_after = Pt(6)
    _tambah_garis_bawah(p_garis, weight="12", val="double")


def _buat_blok_nomor(doc: Document, nomor, sifat, lampiran, perihal, tanggal):
    """Blok Nomor/Sifat/Lampiran/Perihal, dengan tanggal sejajar baris
    Nomor (rata kanan) -- tabel 4 kolom tanpa border (label, ':', value,
    tanggal), sesuai struktur asli template (bukan tab di dalam 1 sel)."""
    table = doc.add_table(rows=4, cols=4)
    _set_lebar_kolom_fixed(table, [2.0, 0.5, 7.6, 5.7])
    _hilangkan_border_tabel(table)
    _perkecil_margin_sel(table)

    baris = [
        ("Nomor", nomor, f"Pekanbaru, {tanggal}"),
        ("Sifat", sifat, ""),
        ("Lampiran", lampiran, ""),
        ("Perihal", perihal, ""),
    ]
    for i, (label, value, kanan) in enumerate(baris):
        c_label, c_titik, c_value, c_kanan = table.rows[i].cells

        r_label = c_label.paragraphs[0].add_run(label)
        _set_font(r_label)

        r_titik = c_titik.paragraphs[0].add_run(":")
        _set_font(r_titik)

        p_value = c_value.paragraphs[0]
        r_value = p_value.add_run(value)
        _set_font(r_value)

        if kanan:
            p_kanan = c_kanan.paragraphs[0]
            p_kanan.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r_kanan = p_kanan.add_run(kanan)
            _set_font(r_kanan)

    _spacer(doc)


def _spacer(doc: Document, pt=6):
    """Spacer vertikal kecil (bukan blank paragraph full-line) supaya nggak
    boros ruang halaman -- penting untuk surat Perjalanan Dinas yang
    kontennya lumayan padat dan aslinya muat dalam 1 halaman."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run("")
    r.font.size = Pt(pt)
    r.font.name = BASE_FONT
    return p


def _tambah_paragraf_isi(doc: Document, text: str, indent_first_line=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent_first_line:
        p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    _set_font(r)
    return p


def _buat_blok_tanda_tangan(doc: Document, jabatan="Sekretaris", nama="RUDINAL B"):
    """Blok tanda tangan rata kanan -- tabel 2 kolom tanpa border, sesuai
    pola template asli (bukan alignment=RIGHT biasa, tapi kolom kanan
    sempit yang isinya di-center)."""
    table = doc.add_table(rows=3, cols=2)
    _set_lebar_kolom_fixed(table, [9.4, 6.4])
    _hilangkan_border_tabel(table)
    _perkecil_margin_sel(table)

    baris_kanan = [f"{jabatan},", "${ttd_pengirim}", nama]
    for i, teks in enumerate(baris_kanan):
        _, c_kanan = table.rows[i].cells
        p = c_kanan.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        bold = (i == 2)  # nama ditebalkan
        r = p.add_run(teks)
        _set_font(r, bold=bold)
        if i == 1:
            doc.add_paragraph()  # sedikit spasi ekstra untuk area ttd


def _tambah_border_tabel(table, sz="4", color="000000"):
    """Kebalikan dari _hilangkan_border_tabel -- dipakai untuk tabel Daftar
    Perjalanan Dinas di halaman 2, yang di template asli memang bergaris."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def _tambah_butir_bernomor(doc: Document, nomor_label: str, text: str, indent_cm=1.3):
    """Paragraf dengan hanging indent (nomor nempel kiri, teks lanjutan
    sejajar) -- dipakai untuk daftar ketentuan & daftar tembusan."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(indent_cm)
    pf.first_line_indent = Cm(-indent_cm)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_after = Pt(4)
    pf.tab_stops.add_tab_stop(Cm(indent_cm))
    r = p.add_run(f"{nomor_label}\t{text}")
    _set_font(r)
    return p


def _buat_tabel_pegawai(doc: Document, pegawai_list):
    """Tabel Daftar Perjalanan Dinas di halaman 2 -- bergaris, kolom TUJUAN
    selalu 'KPU Provinsi Riau' (fixed, tidak diinput per baris)."""
    n = max(len(pegawai_list), 1)
    table = doc.add_table(rows=1 + n, cols=6)
    _set_lebar_kolom_fixed(table, [1.0, 2.6, 3.0, 2.2, 2.0, 5.0])
    _tambah_border_tabel(table)

    headers = ["NO", "NAMA", "JABATAN", "TUJUAN", "TANGGAL", "DALAM RANGKA"]
    for j, h in enumerate(headers):
        p = table.rows[0].cells[j].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        _set_font(r, bold=True)

    if not pegawai_list:
        for j in range(6):
            table.rows[1].cells[j].paragraphs[0].add_run("-")
    else:
        for i, peg in enumerate(pegawai_list):
            row = table.rows[i + 1]
            nilai = [
                f"{i + 1}.",
                peg.get("nama", ""),
                peg.get("jabatan", ""),
                "KPU Provinsi Riau",
                peg.get("tanggal", ""),
                peg.get("dalam_rangka", ""),
            ]
            for j, v in enumerate(nilai):
                p = row.cells[j].paragraphs[0]
                if j == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(v)
                _set_font(r)
    return table


# ---------------------------------------------------------------------------
# Ketentuan baku (Permenkeu dll) untuk surat Persetujuan Perjalanan Dinas --
# teks ini SAMA PERSIS di semua contoh yang dianalisis, jadi di-hardcode.
# Termasuk kata "bepedoman" (bukan "berpedoman") yang memang typo di
# dokumen asli -- dipertahankan demi konsistensi wording persis dengan
# template resmi. Beri tahu kalau ternyata mau dikoreksi.
# ---------------------------------------------------------------------------
_KETENTUAN_PERJALANAN_DINAS = [
    "Perjalanan Dinas dilaksanakan dengan memperhatikan prinsip yaitu "
    "efisiensi, efektivitas, kewajaran dan akuntabilitas serta "
    "ketersediaan dana.",
    "Penganggaran, pelaksanaan, penatausahaan dan pelaporan atas belanja "
    "perjalanan dinas agar mempedomani besaran satuan biaya yang berlaku "
    "dalam APBN sebagaimana diatur dalam Peraturan Menteri Keuangan Nomor "
    "32 Tahun 2025 tentang Standar Biaya Masukan Tahun Anggaran 2026, dan "
    "pertanggungjawabannya bepedoman pada Peraturan Menteri Keuangan "
    "Nomor 119 Tahun 2023 tentang Perubahan atas Peraturan Menteri "
    "Keuangan Nomor 113/PMK.05/2012 tentang Perjalanan Dinas Dalam Negeri "
    "bagi Pejabat Negara, Pegawai Negeri, dan Pegawai Tidak Tetap. "
    "Peraturan Direktur Jenderal Perbendaharaan Nomor PER-14/PB/2025 "
    "tentang Petunjuk Teknis Pelaksanaan Sistem Elektronik Perjalanan "
    "Dinas bagi Pejabat Negara, Pegawai Negeri, dan Pegawai Tidak Tetap.",
    "Segala pengeluaran Perjalanan Dinas menjadi tanggungjawab Kuasa "
    "Pengguna Anggaran masing-masing.",
]


def buat_dokumen_perjalanan_dinas(kabupaten: str, kota: str,
                                   nomor_rujukan: str, tanggal_rujukan: str,
                                   pegawai_list, sifat: str = "Segera",
                                   lampiran: str = "1 (satu) lembar",
                                   nomor_surat: str = None,
                                   jabatan_penandatangan: str = "Sekretaris",
                                   nama_penandatangan: str = "RUDINAL B",
                                   output_dir: str = "output"):
    """Susun surat Persetujuan Izin Perjalanan Dinas -- PURE template-fill,
    TANPA AI, karena seluruh isi suratnya baku secara regulasi. Hanya
    beberapa variabel yang berubah: kabupaten/kota tujuan, nomor & tanggal
    surat rujukan, dan daftar pegawai (halaman 2).

    kabupaten: nama kabupaten, mis. "Kampar" -> dipakai di "Yth. Sekretaris
        KPU Kabupaten Kampar", judul tabel halaman 2, dan Tembusan.
    kota: nama kota/ibukota kabupaten, mis. "Bangkinang" -> dipakai di
        bawah "di -" (BEDA dari nama kabupaten, sesuai pola template asli:
        Kabupaten Kepulauan Meranti -> kotanya "Selatpanjang", dst).
    pegawai_list: list of dict {"nama","jabatan","tanggal","dalam_rangka"}.
        Kolom TUJUAN otomatis "KPU Provinsi Riau" untuk semua baris.
    """
    os.makedirs(output_dir, exist_ok=True)
    template = TEMPLATES["Persetujuan Perjalanan Dinas"]
    nomor = nomor_surat or generate_nomor_surat("Persetujuan Perjalanan Dinas")
    tanggal = _tanggal_indonesia(datetime.now())

    doc = Document()
    section = doc.sections[0]
    section.page_width = PAGE_WIDTH
    section.page_height = PAGE_HEIGHT
    section.top_margin = MARGIN_TOP
    section.bottom_margin = MARGIN_BOTTOM
    section.left_margin = MARGIN_SIDE
    section.right_margin = MARGIN_SIDE

    normal_style = doc.styles["Normal"]
    normal_style.font.name = BASE_FONT
    normal_style.font.size = BASE_SIZE
    normal_style.paragraph_format.space_after = Pt(0)
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.line_spacing = 1.0

    # ============================== HALAMAN 1 ==============================
    _buat_kop_surat(doc)
    _buat_blok_nomor(doc, nomor, sifat, lampiran, template["perihal"], tanggal)

    p_yth = doc.add_paragraph()
    _set_font(p_yth.add_run(f"Yth. Sekretaris KPU Kabupaten {kabupaten}"))

    p_di = doc.add_paragraph()
    _set_font(p_di.add_run("di -"))
    p_kota = doc.add_paragraph()
    p_kota.paragraph_format.left_indent = Cm(1.25)
    r_kota = p_kota.add_run(kota)
    _set_font(r_kota)
    r_kota.underline = True

    _spacer(doc)

    # paragraf pembuka (baku, cuma nomor & tanggal rujukan yang variabel)
    teks_pembuka = (
        f"Berdasarkan surat Saudara Nomor: {nomor_rujukan} tanggal "
        f"{tanggal_rujukan} perihal Permohonan Izin Perjalanan Dinas, "
        "dengan hormat disampaikan bahwa kami menyetujui perjalanan dinas "
        "luar kota bagi pejabat/pegawai sebagaimana tercantum dalam "
        "daftar terlampir."
    )
    _tambah_paragraf_isi(doc, teks_pembuka)

    _tambah_paragraf_isi(
        doc,
        "Sehubungan hal tersebut, persetujuan ini diberikan dengan "
        "ketentuan sebagai berikut :",
    )

    for i, ketentuan in enumerate(_KETENTUAN_PERJALANAN_DINAS, start=1):
        _tambah_butir_bernomor(doc, f"{i}.", ketentuan)

    _spacer(doc)
    _tambah_paragraf_isi(doc, template["penutup"], indent_first_line=False)
    _spacer(doc)

    _buat_blok_tanda_tangan(doc, jabatan_penandatangan, nama_penandatangan)

    _spacer(doc, pt=10)
    p_tembusan_judul = doc.add_paragraph()
    r_tembusan_judul = p_tembusan_judul.add_run("Tembusan disampaikan Yth :")
    _set_font(r_tembusan_judul, bold=True)
    r_tembusan_judul.underline = True

    tembusan = [
        "Ketua KPU Provinsi Riau;",
        f"Ketua KPU Kabupaten {kabupaten};",
        "Pertinggal.",
    ]
    for i, t in enumerate(tembusan, start=1):
        _tambah_butir_bernomor(doc, f"{i}.", t, indent_cm=1.3)

    # ============================== HALAMAN 2 ==============================
    doc.add_page_break()

    p_judul1 = doc.add_paragraph()
    p_judul1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(p_judul1.add_run("DAFTAR PERJALANAN DINAS"), bold=True)

    p_judul2 = doc.add_paragraph()
    p_judul2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(p_judul2.add_run(f"KPU KABUPATEN {kabupaten.upper()}"), bold=True)

    doc.add_paragraph()
    _buat_tabel_pegawai(doc, pegawai_list)

    doc.add_paragraph()
    doc.add_paragraph()
    _buat_blok_tanda_tangan(doc, jabatan_penandatangan, nama_penandatangan)

    # --- SIMPAN --------------------------------------------------------------
    seq_part = nomor.split("/")[0]
    filename = f"surat_persetujuan_perjalanan_dinas_{seq_part}.docx"
    path = os.path.join(output_dir, filename)
    doc.save(path)
    return path, nomor


def _buat_blok_jadwal(doc: Document, jadwal: dict):
    """Blok jadwal terstruktur (Hari/Tanggal/Waktu/Tempat/Agenda Rapat) --
    dipakai untuk Undangan Rapat. Ditemukan sebagai pola umum di kedua
    contoh (Rakor & Rapat Rutin), meski label field-nya beda dikit."""
    baris_label = [
        ("Hari", jadwal.get("hari", "")),
        ("Tanggal", jadwal.get("tanggal", "")),
        ("Waktu", jadwal.get("waktu", "")),
    ]
    if jadwal.get("tempat"):
        baris_label.append(("Tempat", jadwal["tempat"]))
    if jadwal.get("link_zoom"):
        baris_label.append(("Link Zoom", jadwal["link_zoom"]))

    agenda = jadwal.get("agenda") or []
    n_rows = len(baris_label) + (1 if agenda else 0)

    table = doc.add_table(rows=n_rows, cols=3)
    _set_lebar_kolom_fixed(table, [3.0, 0.5, 12.3])
    _hilangkan_border_tabel(table)
    _perkecil_margin_sel(table)

    for i, (label, val) in enumerate(baris_label):
        c_label, c_titik, c_val = table.rows[i].cells
        _set_font(c_label.paragraphs[0].add_run(label))
        _set_font(c_titik.paragraphs[0].add_run(":"))
        _set_font(c_val.paragraphs[0].add_run(val))

    if agenda:
        c_label, c_titik, c_val = table.rows[len(baris_label)].cells
        _set_font(c_label.paragraphs[0].add_run("Agenda Rapat"))
        _set_font(c_titik.paragraphs[0].add_run(":"))
        for i, item in enumerate(agenda):
            item_clean = re.sub(r'^(?:\d+[\.\)]\s*)+', '', str(item)).strip()
            p = c_val.paragraphs[0] if i == 0 else c_val.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.7)
            p.paragraph_format.first_line_indent = Cm(-0.7)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(0.7))
            _set_font(p.add_run(f"{i + 1}.\t{item_clean}"))


    _spacer(doc)
    return table


def buat_dokumen_surat(jenis_surat: str, tujuan: str, isi: str,
                        kota_tujuan: str = "", sifat: str = "Segera",
                        lampiran: str = "-", nomor_surat: str = None,
                        jabatan_penandatangan: str = "Sekretaris",
                        nama_penandatangan: str = "RUDINAL B",
                        perihal_override: str = None,
                        kode_klasifikasi_override: str = None,
                        penutup_override: str = None,
                        penerima_list=None,
                        jadwal: dict = None,
                        is_internal: bool = False,
                        output_dir: str = "output"):
    """Susun file .docx surat resmi sesuai standar template KPU Provinsi Riau.

    perihal_override / kode_klasifikasi_override: dipakai untuk "Surat
        Permohonan" (topiknya macam-macam, jadi diisi manual per surat).
    penerima_list: kalau diisi (list of str), "Yth." dirender sebagai daftar
        bernomor (penerima internal) alih-alih 1 baris "Yth. {tujuan}"
        (penerima eksternal/default). Kalau ini diisi, kota_tujuan diabaikan
        dan otomatis pakai "di -" / "tempat" (huruf kecil, tanpa kota).
    jadwal: dict opsional {"hari","tanggal","waktu","tempat","link_zoom",
        "agenda":[...]} -- kalau diisi, dirender sebagai blok terstruktur
        setelah paragraf isi (dipakai untuk Undangan Rapat).

    Mengembalikan (path_file, nomor_surat)."""
    os.makedirs(output_dir, exist_ok=True)
    template = TEMPLATES.get(jenis_surat, TEMPLATES["Pemberitahuan"])
    perihal = perihal_override or template["perihal"]
    penutup = penutup_override or template["penutup"]
    nomor = nomor_surat or generate_nomor_surat(jenis_surat, kode_klasifikasi_override)
    tanggal = _tanggal_indonesia(datetime.now())

    doc = Document()
    section = doc.sections[0]
    section.page_width = PAGE_WIDTH
    section.page_height = PAGE_HEIGHT
    section.top_margin = MARGIN_TOP
    section.bottom_margin = MARGIN_BOTTOM
    section.left_margin = MARGIN_SIDE
    section.right_margin = MARGIN_SIDE

    # set default style font supaya semua teks baru ikut Arial 12pt
    normal_style = doc.styles["Normal"]
    normal_style.font.name = BASE_FONT
    normal_style.font.size = BASE_SIZE
    normal_style.paragraph_format.space_after = Pt(0)
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.line_spacing = 1.0

    # Kop surat ditentukan oleh jabatan penandatangan:
    # - Ketua → logo di tengah (format internal)
    # - Sekretaris / lainnya → logo di kiri (format eksternal)
    is_kop_internal = "ketua" in jabatan_penandatangan.lower()
    _buat_kop_surat(doc, is_internal=is_kop_internal)
    _buat_blok_nomor(doc, nomor, sifat, lampiran, perihal, tanggal)

    # --- Yth / di / kota tujuan ---------------------------------------------
    if penerima_list:
        p_yth = doc.add_paragraph()
        _set_font(p_yth.add_run("Yth."))
        n = len(penerima_list)
        for i, penerima in enumerate(penerima_list):
            if i == n - 1:
                akhiran = "."
            elif i == n - 2:
                akhiran = "; dan"
            else:
                akhiran = ";"
            _tambah_butir_bernomor(doc, f"{i + 1}.", f"{penerima}{akhiran}", indent_cm=1.3)

        p_di = doc.add_paragraph()
        _set_font(p_di.add_run("di -"))
        p_tempat = doc.add_paragraph()
        p_tempat.paragraph_format.left_indent = Cm(1.25)
        _set_font(p_tempat.add_run("tempat"))
    else:
        p_yth = doc.add_paragraph()
        r_yth = p_yth.add_run(f"Yth. {tujuan}")
        _set_font(r_yth)

        p_di = doc.add_paragraph()
        if kota_tujuan.strip():
            r_di = p_di.add_run("di -")
            _set_font(r_di)
            p_kota = doc.add_paragraph()
            p_kota.paragraph_format.left_indent = Cm(1.25)
            r_kota = p_kota.add_run(kota_tujuan.strip())
            _set_font(r_kota, name=BASE_FONT)
            r_kota.underline = True
        else:
            r_di = p_di.add_run("di")
            _set_font(r_di)
            p_tempat = doc.add_paragraph()
            p_tempat.paragraph_format.left_indent = Cm(1.25)
            r_tempat = p_tempat.add_run("Tempat")
            _set_font(r_tempat)

    _spacer(doc)

    # --- ISI SURAT (hasil AI, dibersihkan dari header markdown seperti **Isi Surat**) ---
    clean_paragraphs = []
    for para in isi.split("\n\n"):
        para_s = para.strip()
        if not para_s:
            continue
        # Skip baris header seperti **Isi Surat**, **Paragraf Pembuka**, dsb.
        if re.match(r'^(?:\#+\s*|\*\*)?(?:Isi\s*Surat|Paragraf\s*Pembuka|Pendahuluan|Isi)\s*\*\*?:?$', para_s, re.IGNORECASE):
            continue
        # Hapus prefix header jika ada di awal paragraf
        para_s = re.sub(r'^(?:\#+\s*|\*\*)?(?:Isi\s*Surat|Paragraf\s*Pembuka|Pendahuluan|Isi)\s*\*\*?:?\s*', '', para_s, flags=re.IGNORECASE)
        # Hapus sisa tanda markdown bold **
        para_s = para_s.replace('**', '').strip()
        if para_s:
            clean_paragraphs.append(para_s)

    for para in clean_paragraphs:
        _tambah_paragraf_isi(doc, para)

    # --- BLOK JADWAL TERSTRUKTUR (opsional, dipakai Undangan Rapat) --------
    if jadwal:
        _spacer(doc)
        _buat_blok_jadwal(doc, jadwal)

    doc.add_paragraph()
    _tambah_paragraf_isi(doc, penutup, indent_first_line=False)
    doc.add_paragraph()

    _buat_blok_tanda_tangan(doc, jabatan_penandatangan, nama_penandatangan)

    # --- SIMPAN --------------------------------------------------------------
    slug = jenis_surat.replace(" ", "_").lower()
    seq_part = nomor.split("/")[0]
    filename = f"surat_{slug}_{seq_part}.docx"
    path = os.path.join(output_dir, filename)
    doc.save(path)
    return path, nomor
