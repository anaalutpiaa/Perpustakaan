"""Seed data: kategori, 258 buku (sumber legal + sampul), akun demo, contoh pinjaman & ulasan.

  python seed.py                 isi data awal (dilewati jika buku sudah ada)
  python seed.py --add-more      SINKRONKAN database yang sudah ada dengan catalog.py: menghapus kategori 'Buku Pelajaran'
                                 beserta bukunya, lalu menambah buku baru (buku, user, dan pinjaman lain tidak disentuh)
  python seed.py --reset         hapus SEMUA data lalu isi ulang
  python seed.py --reset-admin   kembalikan akun admin ke  admin / admin12345  (data lain tidak disentuh)
  python seed.py --download-covers   salin sampul asli (URL) ke server agar tetap tampil tanpa internet

Data buku ada di catalog.py. Sampul lokal dibuat oleh make_covers.py (sudah disertakan di static/img/covers)."""
import random
import sys
from datetime import datetime, timedelta

from app import app, ensure_default_admin
from catalog import BOOKS, CATEGORIES
from extensions import db
from models import Book, Category, Favorite, Loan, Review, User

DEMO_USERS = [
    ("Budi Santoso", "budi", "budi@example.com"),
    ("Siti Rahmawati", "siti", "siti@example.com"),
    ("Rina Kusuma", "rina", "rina@example.com"),
]
COMMENTS = ["Bacaan yang sangat bagus, direkomendasikan!", "Ceritanya menarik dan mudah dipahami.",
            "Cocok untuk pemula, penjelasannya runtut.", "Klasik yang layak dibaca ulang.",
            "Bahasanya agak berat tetapi isinya berbobot.", "Sangat membantu untuk belajar."]


def download_covers():
    """Unduh sampul asli dari URL (Gutenberg dll.) ke static/uploads/covers. Butuh internet."""
    from utils import download_cover
    with app.app_context(), app.test_request_context():
        done = 0
        for b in Book.query.filter(Book.cover_url.isnot(None), Book.cover_file.is_(None)).all():
            name, err = download_cover(b.cover_url)
            if name:
                b.cover_file, b.cover_url = name, None
                done += 1
            else:
                print(f"  lewati {b.title}: {err}")
        db.session.commit()
        print(f"{done} sampul disalin ke server.")


def remove_textbooks():
    """Hapus kategori 'Buku Pelajaran' beserta seluruh bukunya (kategori ini sudah tidak dipakai).
    Ulasan, favorit, dan riwayat pinjam buku-buku itu ikut terhapus."""
    from utils import delete_upload
    cat = Category.query.filter_by(name="Buku Pelajaran").first()
    if not cat:
        return 0
    n = 0
    for b in Book.query.filter_by(category_id=cat.id).all():
        delete_upload("cover", b.cover_file)
        delete_upload("book", b.pdf_file)
        db.session.delete(b)
        n += 1
    db.session.delete(cat)
    db.session.commit()
    return n


def add_more():
    """Hapus 'Buku Pelajaran', lalu tambahkan buku dari catalog.py yang belum ada (cek berdasarkan judul)."""
    import random
    from catalog import CATEGORIES
    with app.app_context():
        removed = remove_textbooks()
        if removed:
            print(f"{removed} buku pelajaran dihapus beserta kategorinya.")
        random.seed(7)
        cats = {c.name: c for c in Category.query.all()}
        for name, desc, icon in CATEGORIES:
            if name not in cats:
                cats[name] = Category(name=name, description=desc, icon=icon)
                db.session.add(cats[name])
        db.session.flush()
        have = {t.lower() for (t,) in db.session.query(Book.title).all()}
        now, added = datetime.now(), 0
        for data in BOOKS:
            if data["title"].lower() in have:
                continue
            data = dict(data)
            cat = cats[data.pop("cat")]
            db.session.add(Book(category_id=cat.id, views=random.randint(5, 400), created_at=now, **data))
            added += 1
        db.session.commit()
        print(f"{added} buku baru ditambahkan. Total sekarang: {Book.query.count()} buku.")


def run(reset=False):
    with app.app_context():
        if reset:
            db.drop_all()
            db.create_all()
            ensure_default_admin(app)
            print("Database direset.")
        if Book.query.count():
            print("Data buku sudah ada. Untuk menambah buku baru tanpa menghapus data: python seed.py --add-more")
            return
        random.seed(42)
        cats = {}
        for name, desc, icon in CATEGORIES:
            c = Category(name=name, description=desc, icon=icon)
            db.session.add(c)
            cats[name] = c
        db.session.flush()

        now = datetime.now()
        books = []
        for i, data in enumerate(BOOKS):
            data = dict(data)
            cat = cats[data.pop("cat")]
            b = Book(category_id=cat.id, views=random.randint(5, 400),
                     created_at=now - timedelta(hours=len(BOOKS) - i), **data)
            db.session.add(b)
            books.append(b)
        db.session.flush()

        users = []
        for name, username, email in DEMO_USERS:
            u = User(name=name, username=username, email=email, role="user")
            u.set_password("user12345")
            db.session.add(u)
            users.append(u)
        db.session.flush()

        digital = [b for b in books if b.is_digital]
        physical_books = [b for b in books if not b.is_digital]
        for u in users:  # ulasan & favorit contoh
            for b in random.sample(digital, 6):
                db.session.add(Review(user_id=u.id, book_id=b.id, rating=random.randint(3, 5),
                                      comment=random.choice(COMMENTS)))
            for b in random.sample(books, 3):
                db.session.add(Favorite(user_id=u.id, book_id=b.id))

        # Contoh pinjaman: 1 terlambat, 1 aktif, 1 menunggu persetujuan, 1 sudah kembali
        def loan(user, book, status, borrowed_days_ago=None):
            l = Loan(user_id=user.id, book_id=book.id, status=status,
                     requested_at=now - timedelta(days=(borrowed_days_ago or 0) + 1))
            if borrowed_days_ago is not None:
                l.borrowed_at = now - timedelta(days=borrowed_days_ago)
                l.due_date = l.borrowed_at + timedelta(days=7)
                if status == "returned":
                    l.returned_at = l.borrowed_at + timedelta(days=5)
                else:
                    book.stock -= 1
            db.session.add(l)

        loan(users[0], physical_books[0], "borrowed", 10)  # terlambat 3 hari
        loan(users[1], physical_books[1], "borrowed", 2)
        loan(users[2], physical_books[2], "pending")
        loan(users[0], physical_books[3], "returned", 20)
        db.session.commit()
        print(f"Seed selesai: {len(CATEGORIES)} kategori, {len(books)} buku, {len(users)} user demo.")


if __name__ == "__main__":
    if "--reset-admin" in sys.argv:
        with app.app_context():
            ensure_default_admin(app, force_reset=True)
        print("Akun admin dipulihkan: username 'admin', password 'admin12345'.")
    elif "--add-more" in sys.argv:
        add_more()
    elif "--download-covers" in sys.argv:
        download_covers()
    else:
        run(reset="--reset" in sys.argv)
