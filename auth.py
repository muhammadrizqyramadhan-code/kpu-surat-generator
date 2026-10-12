"""
auth.py
-------
Modul autentikasi untuk Generator Surat KPU Provinsi Riau.
Mengelola database user (SQLite), password hashing (bcrypt), dan JWT token.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = "kpu_riau_surat_secret_key_2026_secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db():
    """Buat tabel users dan seed admin default jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nama_lengkap TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    existing = c.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not existing:
        now = datetime.now().isoformat()
        c.execute(
            "INSERT INTO users (username, nama_lengkap, jabatan, password_hash, role, is_active, created_at) VALUES (?,?,?,?,?,?,?)",
            ("admin", "Administrator", "Admin Sistem", pwd_context.hash("admin123"), "admin", 1, now),
        )
        conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, nama_lengkap, jabatan, role, is_active, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    result = [dict(zip(["id","username","nama_lengkap","jabatan","role","is_active","created_at"], r)) for r in rows]
    conn.close()
    return result


def get_user_by_username(username: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    result = dict(zip(["id","username","nama_lengkap","jabatan","password_hash","role","is_active","created_at"], row)) if row else None
    conn.close()
    return result


def create_user(username: str, nama_lengkap: str, jabatan: str, password: str, role: str = "user"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, nama_lengkap, jabatan, password_hash, role, is_active, created_at) VALUES (?,?,?,?,?,?,?)",
            (username, nama_lengkap, jabatan, pwd_context.hash(password), role, 1, datetime.now().isoformat()),
        )
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return {"ok": True, "id": user_id}
    except sqlite3.IntegrityError:
        conn.close()
        return {"ok": False, "error": f"Username '{username}' sudah digunakan."}


def update_user(user_id: int, nama_lengkap=None, jabatan=None, password=None, role=None, is_active=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fields, values = [], []
    if nama_lengkap is not None: fields.append("nama_lengkap = ?"); values.append(nama_lengkap)
    if jabatan is not None: fields.append("jabatan = ?"); values.append(jabatan)
    if password is not None: fields.append("password_hash = ?"); values.append(pwd_context.hash(password))
    if role is not None: fields.append("role = ?"); values.append(role)
    if is_active is not None: fields.append("is_active = ?"); values.append(1 if is_active else 0)
    if not fields:
        conn.close()
        return {"ok": False, "error": "Tidak ada data yang diubah."}
    values.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return {"ok": affected > 0}


def delete_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    admin_count = c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1").fetchone()[0]
    user_row = c.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if user_row and user_row[0] == "admin" and admin_count <= 1:
        conn.close()
        return {"ok": False, "error": "Tidak dapat menghapus admin terakhir."}
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return {"ok": affected > 0}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user or not user.get("is_active"):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


init_db()
