# PustakaKu — Perpustakaan Digital (Flask)

Flask + SQLite + HTML/CSS/JavaScript (dirender lewat Jinja2 dan fetch ke API Flask).

## Menjalankan
```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                      # isi 258 buku + sampul + akun demo
python app.py                       # buka http://127.0.0.1:5000
```
Opsional: `export SECRET_KEY="string-acak-panjang"` (Windows: `set SECRET_KEY=...`).
Jika sebelumnya memakai versi lama, cukup jalankan `python app.py`; kolom baru ditambahkan otomatis.
Atau hapus `perpustakaan.db` lalu jalankan `python seed.py` untuk mulai bersih.

## Memperbarui database yang sudah ada
Katalog terdiri dari 8 kategori dan 258 judul (kategori *Buku Pelajaran* sudah dihapus). Jika Anda sudah punya
`perpustakaan.db` dari versi sebelumnya, cukup jalankan:
```bash
python seed.py --add-more
```
Perintah ini menghapus kategori *Buku Pelajaran* beserta bukunya (termasuk ulasan, favorit, dan riwayat pinjam buku
itu), lalu menambah buku baru sehingga totalnya 258. Buku, user, dan pinjaman lain tidak disentuh. Aman dijalankan
berulang kali. Daftar buku ada di `catalog.py` dan `catalog_extra.py`. Cek tautan dengan `python verify_catalog.py`.

## Akun demo
| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin12345` |
| User | `budi` (ada pinjaman terlambat), `siti`, `rina` | `user12345` |

**Tidak bisa login admin?** Jalankan `python seed.py --reset-admin`. Akun admin dibuat/diperbaiki dan
password dikembalikan ke `admin12345` (data lain tidak disentuh).

## Admin: menambah buku dengan mudah
Menu **Admin > Buku > Tambah buku**:
1. **Mulai cepat dari link**: tempel link (Project Gutenberg, halaman buku, atau PDF langsung), klik *Ambil data*.
   Judul, penulis, deskripsi, tautan baca/unduh, dan sampul terisi otomatis.
2. **Foto sampul**: upload foto (klik atau seret), atau tempel URL gambar, atau klik *Cari sampul otomatis*
   (Open Library) lalu pilih gambar. Gambar dari URL disalin ke server agar tetap tampil.
3. **Upload PDF**: dipakai untuk Baca Online dan Unduh.
4. **Impor massal** (*Admin > Impor massal*): tempel banyak link, atau baris
   `Judul | Penulis | Kategori | Jenis | Link | URL cover | Stok`.

Admin juga bisa: CRUD kategori dan user (ubah role, blokir), kelola peminjaman (setujui, tolak, tandai kembali,
catat peminjaman manual), hapus ulasan, dan mengubah **Pengaturan** (nama perpustakaan, kontak, lama pinjam,
batas pinjaman, wajib persetujuan, perpanjangan, buka/tutup pendaftaran).

## Peminjaman
Pinjam buku fisik langsung aktif 7 hari (stok berkurang otomatis). Jika *Wajib persetujuan admin* diaktifkan di
Pengaturan, pinjaman menunggu disetujui. Anggota bisa memperpanjang 1x, mengembalikan buku, dan melihat riwayat.
Keterlambatan memunculkan lonceng di navbar, banner di dashboard, dan peringatan saat login.

## Sampul buku
- `static/img/covers/` berisi **258 sampul PNG, satu gambar unik per buku** (dibuat oleh `make_covers.py`).
  Ilustrasi disesuaikan dengan isi buku (misalnya kapal untuk *Moby Dick*, kastil untuk *Dracula*, candi untuk sastra
  klasik, terminal untuk buku pemrograman).
- Urutan tampilan: foto yang diupload admin, lalu sampul bawaan di atas, lalu URL cover. Jika admin memasang sampul
  baru pada sebuah buku, sampul bawaan buku itu otomatis diganti.
- Untuk membuat ulang semua sampul: `python make_covers.py` (butuh Pillow). Ilustrasi dan warna bisa diubah di file itu.
- `python seed.py --download-covers` hanya menyalin sampul dari URL (jika ada) ke server; tidak diperlukan untuk
  sampul bawaan.

## Keamanan
Hash password pbkdf2-sha256, CSRF di semua form dan fetch, ORM (anti SQL injection), autoescape dan `textContent`
(anti XSS), `@admin_required` pada seluruh `/admin/*`, upload dicek ekstensi/isi/ukuran dan diubah ke JPEG,
*Ambil data dari link* hanya mengizinkan http/https dan alamat publik (anti SSRF), redirect `next` hanya path
internal, logout via POST.

## Catatan legal
Buku digital memakai domain publik atau lisensi terbuka. Pastikan setiap buku yang
Anda tambahkan memiliki hak/lisensi yang sah. Verifikasi tautan sebelum rilis publik.
