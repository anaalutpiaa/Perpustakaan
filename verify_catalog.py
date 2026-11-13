"""Cek tautan katalog (butuh internet):  python verify_catalog.py
- Buku Project Gutenberg: membandingkan judul di Gutenberg dengan judul di katalog.
- Tautan lain: memastikan alamat bisa dibuka.
Hasil yang bertanda [PERIKSA] sebaiknya diperbaiki lewat Admin > Buku (atau catalog_extra.py)."""
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from catalog import BOOKS

UA = {"User-Agent": "Mozilla/5.0 PustakaKu-verify"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(300_000).decode("utf-8", "ignore")


def check(b):
    url = b.get("read_url")
    if not url:
        return None
    try:
        m = re.search(r"gutenberg\.org/cache/epub/(\d+)/", url)
        if m:
            title = re.search(r"<title>(.*?)</title>", get(f"https://www.gutenberg.org/ebooks/{m.group(1)}"), re.S).group(1).lower()
            words = [w for w in re.findall(r"[a-z]{4,}", b["title"].lower())][:3]
            if words and not any(w in title for w in words):
                return f"[PERIKSA] ID {m.group(1)} terbaca '{title.strip()[:70]}' ≠ '{b['title']}'"
        else:
            get(url)
    except Exception as exc:
        return f"[PERIKSA] {b['title']}: {url} -> {exc.__class__.__name__} {exc}"
    return None


if __name__ == "__main__":
    with ThreadPoolExecutor(8) as ex:
        problems = [r for r in ex.map(check, BOOKS) if r]
    print("\n".join(problems) if problems else "Semua tautan terverifikasi.")
    print(f"{len(problems)} masalah dari {len(BOOKS)} buku.")
