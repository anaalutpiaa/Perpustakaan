"""Fungsi bantu: decorator admin, upload aman, validasi, cookie consent."""
import os
import re
import uuid
from functools import wraps
from urllib.parse import parse_qs, urlparse

from flask import abort, current_app, request
from flask_login import current_user

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")

# "Magic bytes" untuk memastikan isi file benar-benar sesuai ekstensinya
SIGNATURES = {
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "pdf": (b"%PDF",),
}


def admin_required(view):
    """Hanya admin yang boleh lewat. Belum login -> ke halaman login, bukan admin -> 403."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def valid_email(value):
    return bool(EMAIL_RE.match(value or ""))


def valid_url(value):
    """Hanya izinkan http/https (mencegah javascript: URL)."""
    try:
        p = urlparse(value)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except ValueError:
        return False


def is_safe_next(target):
    """Cegah open-redirect: hanya path internal yang diizinkan."""
    return bool(target) and target.startswith("/") and not target.startswith("//")


def like_escape(text):
    """Escape karakter wildcard LIKE agar input user diperlakukan sebagai teks biasa."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def upload_dir(kind):
    return os.path.join(current_app.static_folder, "uploads", "covers" if kind == "cover" else "books")


def save_upload(file, kind):
    """Simpan upload dengan validasi ekstensi, magic bytes, dan ukuran.
    Mengembalikan (nama_file, pesan_error). Jika tidak ada file: (None, None)."""
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = current_app.config["ALLOWED_COVER_EXT"] if kind == "cover" else {"pdf"}
    if ext not in allowed:
        return None, "Format file tidak diizinkan. Cover: JPG/PNG, buku: PDF."
    head = file.stream.read(8)
    file.stream.seek(0)
    if not any(head.startswith(sig) for sig in SIGNATURES[ext]):
        return None, "Isi file tidak sesuai dengan ekstensinya."
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    limit = current_app.config["MAX_COVER_SIZE" if kind == "cover" else "MAX_PDF_SIZE"]
    if size > limit:
        return None, f"Ukuran file terlalu besar (maksimal {limit // (1024 * 1024)} MB)."
    folder = upload_dir(kind)
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"  # nama acak: aman dari path traversal & bentrok
    file.save(os.path.join(folder, name))
    return name, None


def delete_upload(kind, filename):
    if not filename:
        return
    path = os.path.join(upload_dir(kind), os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)


# ---------- Cookie consent ----------
# Format cookie: "n=1&a=0&m=0"  (n=diperlukan, a=analitik, m=pemasaran)
def parse_consent(raw):
    """Baca & validasi cookie_consent di sisi server. None = belum memilih / tidak valid."""
    if not raw or len(raw) > 40:
        return None
    try:
        data = parse_qs(raw, strict_parsing=True)
    except ValueError:
        return None
    if data.get("n") != ["1"]:
        return None
    flag = lambda key: data.get(key, ["0"])[0] == "1"
    return {"necessary": True, "analytics": flag("a"), "marketing": flag("m")}


def build_consent(analytics, marketing):
    return f"n=1&a={int(bool(analytics))}&m={int(bool(marketing))}"


# ======================================================================
# Pengaturan situs (disimpan di tabel Setting, bisa diubah di Admin > Pengaturan)
# ======================================================================
DEFAULT_SETTINGS = {
    "site_name": "PustakaKu",
    "tagline": "Perpustakaan digital: baca gratis, pinjam buku cetak.",
    "address": "Jl. Pustaka Raya No. 17, Jakarta",
    "contact_email": "pustakaku@example.com",
    "open_hours": "Senin–Sabtu, 08.00–17.00 WIB",
    "loan_days": "7",
    "max_active_loans": "3",
    "require_approval": "0",   # 0 = pinjam langsung aktif, 1 = menunggu persetujuan admin
    "allow_register": "1",
    "allow_extend": "1",
}


def all_settings():
    """Semua pengaturan (default + nilai tersimpan). Di-cache per request lewat flask.g."""
    from flask import g
    if "site_settings" not in g:
        from models import Setting
        data = dict(DEFAULT_SETTINGS)
        try:
            data.update({s.key: (s.value or "") for s in Setting.query.all()})
        except Exception:  # tabel belum dibuat
            pass
        g.site_settings = data
    return g.site_settings


def get_setting(key):
    return all_settings().get(key, DEFAULT_SETTINGS.get(key, ""))


def get_int(key, default=1):
    try:
        return int(get_setting(key))
    except (TypeError, ValueError):
        return default


def get_bool(key):
    return get_setting(key) == "1"


def save_settings(values):
    from flask import g
    from extensions import db
    from models import Setting
    for key, value in values.items():
        row = db.session.get(Setting, key)
        if row:
            row.value = str(value)
        else:
            db.session.add(Setting(key=key, value=str(value)))
    db.session.commit()
    g.pop("site_settings", None)


# ======================================================================
# Ambil data dari link (admin): metadata halaman, gambar cover, pencarian cover
# Dilengkapi proteksi SSRF: hanya http/https dan hanya alamat IP publik.
# ======================================================================
import io
import ipaddress
import json
import socket
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; PustakaKu/1.0; +library-bot)"
GUTENBERG_RE = re.compile(r"gutenberg\.org/(?:ebooks|cache/epub|files)/(\d+)")


def check_public_url(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("URL harus diawali http:// atau https://")
    try:
        infos = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    except socket.gaierror:
        raise ValueError("Alamat situs tidak ditemukan.")
    for info in infos:
        if not ipaddress.ip_address(info[4][0].split("%")[0]).is_global:
            raise ValueError("Alamat internal/privat tidak diizinkan.")


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_public_url(newurl)  # validasi ulang setiap redirect
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirect)


def http_get(url, max_bytes=1_500_000, accept="*/*", timeout=8):
    """Unduh URL dengan batas ukuran. Mengembalikan (bytes, content_type, final_url)."""
    check_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with _opener.open(req, timeout=timeout) as resp:
            data = resp.read(max_bytes + 1)
            ctype = resp.headers.get_content_type()
            final = resp.geturl()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Gagal membuka link ({exc.__class__.__name__}). Periksa koneksi internet atau alamatnya.")
    if len(data) > max_bytes:
        raise ValueError("Berkas terlalu besar.")
    return data, ctype, final


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.title, self._in_title = {}, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"].strip())
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def _clean(text, limit):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def fetch_page_meta(url):
    """Baca link buku/halaman/PDF dan kembalikan data untuk mengisi form buku otomatis."""
    url = url.strip()
    out = {"title": "", "author": "", "description": "", "cover_url": "", "read_url": "", "download_url": "",
           "source": "", "publisher": "", "language": "", "year": "", "book_type": "digital", "notes": []}
    m = GUTENBERG_RE.search(url)
    if m:  # Project Gutenberg: semua tautan bisa disusun dari nomor buku
        gid = m.group(1)
        out.update(read_url=f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}-images.html",
                   download_url=f"https://www.gutenberg.org/ebooks/{gid}.epub.images",
                   cover_url=f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.cover.medium.jpg",
                   source=f"Project Gutenberg #{gid} — Domain Publik", publisher="Project Gutenberg", language="Inggris")
        try:
            data, _, _ = http_get(f"https://www.gutenberg.org/ebooks/{gid}", accept="text/html")
            p = _MetaParser()
            p.feed(data.decode("utf-8", "ignore"))
            title = p.title.split("|")[0].strip()
            if " by " in title:
                title, author = title.rsplit(" by ", 1)
                out["author"] = _clean(author, 150)
            out["title"] = _clean(title, 200)
        except ValueError as exc:
            out["notes"].append("Judul/penulis tidak bisa diambil otomatis: " + str(exc))
        return out

    data, ctype, final = http_get(url, accept="text/html,application/pdf,image/*;q=0.8")
    host = urlparse(final).netloc
    if ctype == "application/pdf":
        name = urllib.parse.unquote(os.path.basename(urlparse(final).path)).rsplit(".", 1)[0]
        out.update(title=_clean(re.sub(r"[-_]+", " ", name).title(), 200), read_url=final, download_url=final, source="Tautan PDF: " + host)
        out["notes"].append("Link PDF terdeteksi. Lengkapi judul dan penulis, lalu cari cover otomatis.")
        return out
    if ctype.startswith("image/"):
        out.update(cover_url=final)
        out["notes"].append("Link gambar terdeteksi: dipakai sebagai cover.")
        return out
    p = _MetaParser()
    p.feed(data.decode("utf-8", "ignore"))
    meta = p.meta
    title = meta.get("og:title") or meta.get("twitter:title") or meta.get("citation_title") or p.title
    out["title"] = _clean(title.split(" | ")[0], 200)
    out["author"] = _clean(meta.get("author") or meta.get("book:author") or meta.get("citation_author") or meta.get("article:author") or "", 150)
    out["description"] = _clean(meta.get("og:description") or meta.get("description") or "", 1500)
    img = meta.get("og:image") or meta.get("twitter:image") or ""
    out["cover_url"] = urllib.parse.urljoin(final, img) if img else ""
    date = meta.get("citation_publication_date") or meta.get("book:release_date") or meta.get("article:published_time") or ""
    ym = re.match(r"(\d{4})", date)
    out["year"] = ym.group(1) if ym else ""
    out.update(read_url=final, source="Tautan: " + host, publisher=_clean(meta.get("og:site_name") or host, 150))
    out["notes"].append("Data diambil dari halaman. Periksa kembali sebelum disimpan dan pastikan sumbernya legal.")
    return out


def search_covers(title, author=""):
    """Cari sampul buku di Open Library (gratis). Mengembalikan daftar kandidat."""
    q = {"title": title, "limit": "8", "fields": "title,author_name,cover_i,first_publish_year"}
    if author:
        q["author"] = author
    data, _, _ = http_get("https://openlibrary.org/search.json?" + urllib.parse.urlencode(q), max_bytes=800_000, accept="application/json")
    items = []
    for d in json.loads(data.decode("utf-8", "ignore")).get("docs", []):
        if d.get("cover_i"):
            items.append({"title": d.get("title", ""), "author": ", ".join(d.get("author_name", [])[:2]),
                          "year": d.get("first_publish_year") or "",
                          "cover_url": f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg",
                          "thumb": f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg"})
    return items


def download_cover(url):
    """Unduh gambar dari URL, validasi, ubah ke JPEG, simpan ke uploads/covers. -> (nama_file, error)"""
    try:
        data, ctype, _ = http_get(url, max_bytes=current_app.config["MAX_COVER_SIZE"] * 2, accept="image/*")
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.load()
    except ValueError as exc:
        return None, str(exc)
    except Exception:
        return None, "Berkas dari link itu bukan gambar yang valid."
    img = img.convert("RGB")
    if img.width < 60 or img.height < 80:
        return None, "Gambar terlalu kecil untuk dijadikan cover."
    img.thumbnail((700, 1050))
    folder = upload_dir("cover")
    os.makedirs(folder, exist_ok=True)
    name = uuid.uuid4().hex + ".jpg"
    img.save(os.path.join(folder, name), "JPEG", quality=88, optimize=True)
    return name, None
