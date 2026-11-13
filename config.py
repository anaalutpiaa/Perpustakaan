"""Konfigurasi aplikasi PustakaKu (Perpustakaan Digital)."""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY WAJIB diambil dari environment variable di produksi.
    # Nilai fallback di bawah hanya untuk pengembangan lokal.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-ganti-lewat-env-SECRET_KEY"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + os.path.join(BASE_DIR, "perpustakaan.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keamanan cookie sesi
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE") == "1"  # set 1 jika memakai HTTPS
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # CSRF (Flask-WTF)
    WTF_CSRF_TIME_LIMIT = None

    # Upload
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024      # batas total request 30 MB
    MAX_COVER_SIZE = 2 * 1024 * 1024           # cover maksimal 2 MB
    MAX_PDF_SIZE = 25 * 1024 * 1024            # PDF maksimal 25 MB
    ALLOWED_COVER_EXT = {"jpg", "jpeg", "png"}

    # Aturan perpustakaan
    LOAN_DAYS = 7              # batas waktu peminjaman (hari)
    MAX_ACTIVE_LOANS = 3       # maksimal pinjaman aktif per user
    PER_PAGE = 12              # pagination halaman publik
    ADMIN_PER_PAGE = 10        # pagination tabel admin
    COOKIE_CONSENT_DAYS = 365

    # Akun admin default (dibuat otomatis saat aplikasi pertama kali jalan)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin12345"
    DEFAULT_ADMIN_EMAIL = "admin@pustakaku.local"
