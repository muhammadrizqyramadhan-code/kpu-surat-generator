"""
api_server.py
-------------
Backend API berbasis FastAPI untuk Generator Surat Resmi KPU Provinsi Riau.
Menyediakan endpoint untuk penyusunan isi surat berbasis AI dan pembuatan
dokumen .docx.
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from doc_generator import (
    TEMPLATES, HARI_INDONESIA, BULAN_INDONESIA,
    buat_dokumen_surat, buat_dokumen_perjalanan_dinas,
)
from llm_service_local import generate_isi_surat
import auth as auth_module

app = FastAPI(
    title="KPU Surat Generator API",
    description="API untuk pembuatan dokumen surat resmi KPU Provinsi Riau",
    version="1.0.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateAIRequest(BaseModel):
    jenis_surat: str
    tujuan: str
    poin_isi: str


class PegawaiItem(BaseModel):
    nama: str
    jabatan: str
    tanggal: str
    dalam_rangka: str


class PerjalananDinasRequest(BaseModel):
    kabupaten: str
    kota: str
    nomor_rujukan: str
    tanggal_rujukan: str
    sifat: str = "Segera"
    lampiran: str = "1 (satu) lembar"
    jabatan_ttd: str = "Sekretaris"
    nama_ttd: str = "RUDINAL B"
    pegawai_list: List[PegawaiItem]


class SuratRequest(BaseModel):
    jenis_surat: str
    tujuan: Optional[str] = ""
    kota_tujuan: Optional[str] = ""
    sifat: str = "Segera"
    lampiran: str = "-"
    isi: str
    perihal_custom: Optional[str] = None
    kode_custom: Optional[str] = None
    penutup_custom: Optional[str] = None
    jabatan_ttd: str = "Sekretaris"
    nama_ttd: str = "RUDINAL B"
    penerima_list: Optional[List[str]] = None
    jadwal: Optional[Dict[str, Any]] = None
    is_internal: Optional[bool] = False


@app.get("/api/templates")
def get_templates():
    return {
        "templates": TEMPLATES,
        "hari": HARI_INDONESIA,
        "bulan": BULAN_INDONESIA,
    }


@app.post("/api/generate-ai")
def api_generate_ai(req: GenerateAIRequest):
    try:
        isi = generate_isi_surat(req.jenis_surat, req.tujuan, req.poin_isi)
        return {"isi": isi}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-perjalanan-dinas")
def api_generate_perjalanan_dinas(req: PerjalananDinasRequest):
    try:
        pegawai_dicts = [p.dict() for p in req.pegawai_list]
        path, nomor = buat_dokumen_perjalanan_dinas(
            kabupaten=req.kabupaten.strip(),
            kota=req.kota.strip(),
            nomor_rujukan=req.nomor_rujukan.strip(),
            tanggal_rujukan=req.tanggal_rujukan.strip(),
            pegawai_list=pegawai_dicts,
            sifat=req.sifat,
            lampiran=req.lampiran,
            jabatan_penandatangan=req.jabatan_ttd,
            nama_penandatangan=req.nama_ttd,
        )
        filename = os.path.basename(path)
        return FileResponse(
            path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"X-Nomor-Surat": nomor, "Access-Control-Expose-Headers": "Content-Disposition, X-Nomor-Surat"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-docx")
def api_generate_docx(req: SuratRequest):
    try:
        path, nomor = buat_dokumen_surat(
            jenis_surat=req.jenis_surat,
            tujuan=req.tujuan or "",
            isi=req.isi,
            kota_tujuan=req.kota_tujuan or "",
            sifat=req.sifat,
            lampiran=req.lampiran,
            jabatan_penandatangan=req.jabatan_ttd,
            nama_penandatangan=req.nama_ttd,
            perihal_override=req.perihal_custom or None,
            kode_klasifikasi_override=req.kode_custom or None,
            penutup_override=req.penutup_custom or None,
            penerima_list=req.penerima_list or None,
            jadwal=req.jadwal or None,
            is_internal=req.is_internal or False,
        )
        filename = os.path.basename(path)
        return FileResponse(
            path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"X-Nomor-Surat": nomor, "Access-Control-Expose-Headers": "Content-Disposition, X-Nomor-Surat"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# AUTH ENDPOINTS
# ===========================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    nama_lengkap: str
    jabatan: str
    password: str
    role: str = "user"


class UpdateUserRequest(BaseModel):
    nama_lengkap: Optional[str] = None
    jabatan: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


def _get_current_user(authorization: Optional[str] = None):
    """Parse Bearer token dari header Authorization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token tidak ditemukan.")
    token = authorization.split(" ", 1)[1]
    payload = auth_module.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kadaluarsa.")
    user = auth_module.get_user_by_username(payload.get("sub", ""))
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Akun tidak ditemukan atau dinonaktifkan.")
    return user


def _require_admin(authorization: Optional[str] = None):
    user = _get_current_user(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya admin yang dapat melakukan ini.")
    return user


@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    user = auth_module.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Username atau password salah.")
    token = auth_module.create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "nama_lengkap": user["nama_lengkap"],
            "jabatan": user["jabatan"],
            "role": user["role"],
        },
    }


@app.get("/api/auth/me")
def api_me(authorization: Optional[str] = Header(default=None)):
    user = _get_current_user(authorization)
    return {
        "id": user["id"],
        "username": user["username"],
        "nama_lengkap": user["nama_lengkap"],
        "jabatan": user["jabatan"],
        "role": user["role"],
    }


@app.get("/api/auth/users")
def api_get_users(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return {"users": auth_module.get_all_users()}


@app.post("/api/auth/users")
def api_create_user(req: CreateUserRequest, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    result = auth_module.create_user(
        username=req.username,
        nama_lengkap=req.nama_lengkap,
        jabatan=req.jabatan,
        password=req.password,
        role=req.role,
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Gagal membuat user."))
    return {"ok": True, "id": result["id"]}


@app.put("/api/auth/users/{user_id}")
def api_update_user(user_id: int, req: UpdateUserRequest, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    result = auth_module.update_user(
        user_id,
        nama_lengkap=req.nama_lengkap,
        jabatan=req.jabatan,
        password=req.password,
        role=req.role,
        is_active=req.is_active,
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Gagal mengupdate user."))
    return {"ok": True}


@app.delete("/api/auth/users/{user_id}")
def api_delete_user(user_id: int, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    result = auth_module.delete_user(user_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Gagal menghapus user."))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
