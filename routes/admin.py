"""Panel admin: dashboard, CRUD buku/kategori/user, peminjaman, ulasan.
Seluruh blueprint dilindungi decorator @admin_required lewat before_request."""
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from extensions import db
from models import Book, Category, Loan, Review, User
from utils import (DEFAULT_SETTINGS, USERNAME_RE, admin_required, all_settings, delete_upload, download_cover,
                   fetch_page_meta, get_int, like_escape, save_settings, save_upload, search_covers, valid_email,
                   valid_url)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@admin_required
def guard():
    """Semua route /admin/* hanya untuk admin (403 untuk user biasa)."""
    return None


def per_page():
    return current_app.config["ADMIN_PER_PAGE"]


def like(text):
    return f"%{like_escape(text)}%"


def month_start(d, back):
    y, m = d.year, d.month - back
    while m <= 0:
        m += 12
        y -= 1
    return datetime(y, m, 1)


# ---------------------------------------------------------------- Dashboard
@admin_bp.route("/")
def dashboard():
    now = datetime.now()
    stats = {
        "books": Book.query.count(),
        "users": User.query.count(),
        "active_loans": Loan.query.filter_by(status="borrowed").count(),
        "pending": Loan.query.filter_by(status="pending").count(),
        "overdue": Loan.query.filter(Loan.status == "borrowed", Loan.due_date < now).count(),
        "reviews": Review.query.count(),
    }
    popular = Book.query.order_by(Book.views.desc(), Book.id).limit(6).all()
    cat_stats = (db.session.query(Category.name, func.count(Book.id))
                 .outerjoin(Book, Book.category_id == Category.id).group_by(Category.id)
                 .order_by(func.count(Book.id).desc()).all())
    monthly = []
    for back in range(5, -1, -1):
        start, end = month_start(now, back), month_start(now, back - 1)
        n = Loan.query.filter(Loan.requested_at >= start, Loan.requested_at < end).count()
        monthly.append((start.strftime("%b %Y"), n))
    recent = Loan.query.order_by(Loan.requested_at.desc()).limit(6).all()
    return render_template("admin/dashboard.html", stats=stats, popular=popular, cat_stats=cat_stats,
                           monthly=monthly, recent=recent,
                           max_views=max([b.views for b in popular] + [1]),
                           max_cat=max([c[1] for c in cat_stats] + [1]),
                           max_month=max([m[1] for m in monthly] + [1]))


# -------------------------------------------------------------------- Buku
@admin_bp.route("/books")
def books():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    page = request.args.get("page", 1, type=int)
    query = Book.query
    if q:
        query = query.filter(or_(Book.title.ilike(like(q), escape="\\"), Book.author.ilike(like(q), escape="\\")))
    if cat:
        query = query.filter(Book.category_id == cat)
    pag = query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page(), error_out=False)
    return render_template("admin/books.html", pag=pag, categories=Category.query.order_by(Category.name).all())


def book_values(book):
    if not book:
        return {"book_type": "digital", "stock": 0, "language": "Indonesia", "save_local": "on"}
    vals = {c.name: getattr(book, c.name) for c in Book.__table__.columns}
    vals["save_local"] = "on"
    return vals


@admin_bp.route("/books/new", methods=["GET", "POST"])
@admin_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def book_form(book_id=None):
    book = db.get_or_404(Book, book_id) if book_id else None
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        f = request.form
        errors = []
        title, author = f.get("title", "").strip(), f.get("author", "").strip()
        year = f.get("year", type=int)
        stock = f.get("stock", 0, type=int)
        btype = f.get("book_type", "digital")
        cat_id = f.get("category_id", type=int)
        read_url, dl_url = f.get("read_url", "").strip(), f.get("download_url", "").strip()
        if not title or len(title) > 200:
            errors.append("Judul wajib diisi (maks. 200 karakter).")
        if not author or len(author) > 150:
            errors.append("Penulis wajib diisi (maks. 150 karakter).")
        if year is not None and not (1 <= year <= datetime.now().year + 1):
            errors.append("Tahun terbit tidak valid.")
        if btype not in ("digital", "physical"):
            errors.append("Tipe buku tidak valid.")
        if stock is None or stock < 0:
            errors.append("Stok tidak boleh negatif.")
        if cat_id and not db.session.get(Category, cat_id):
            errors.append("Kategori tidak ditemukan.")
        for label, url in (("Tautan baca", read_url), ("Tautan unduh", dl_url), ("URL cover", f.get("cover_url", "").strip())):
            if url and not valid_url(url):
                errors.append(f"{label} harus diawali http:// atau https://")
        cover_name, err = save_upload(request.files.get("cover"), "cover")
        if err:
            errors.append("Cover: " + err)
        pdf_name, err = save_upload(request.files.get("pdf"), "pdf")
        if err:
            errors.append("PDF: " + err)
        if errors:
            delete_upload("cover", cover_name)  # bersihkan upload jika form gagal
            delete_upload("book", pdf_name)
            for e in errors:
                flash(e, "danger")
            return render_template("admin/book_form.html", book=book, values=f, categories=categories)
        if not book:
            book = Book()
            db.session.add(book)
        book.title, book.author = title, author
        book.description = f.get("description", "").strip()
        book.year, book.publisher = year, f.get("publisher", "").strip()[:150]
        book.language, book.source = f.get("language", "").strip()[:30], f.get("source", "").strip()[:200]
        book.category_id, book.stock, book.book_type = cat_id or None, stock, btype
        book.read_url, book.download_url = read_url or None, dl_url or None
        # ----- Cover: prioritas upload file > URL (disalin ke server) > cover lama
        cover_url = f.get("cover_url", "").strip()
        if f.get("remove_cover") == "on":
            delete_upload("cover", book.cover_file)
            book.cover_file = book.cover_url = None
        if cover_name:
            delete_upload("cover", book.cover_file)
            book.cover_file, book.cover_url = cover_name, None
        elif cover_url:
            if f.get("save_local") == "on":
                name, err = download_cover(cover_url)
                if name:
                    delete_upload("cover", book.cover_file)
                    book.cover_file, book.cover_url = name, None
                else:
                    book.cover_url = cover_url  # tetap pakai tautan langsung
                    flash(f"Cover tidak bisa disalin ke server ({err}). Tautan langsung dipakai sebagai gantinya.", "warning")
            else:
                delete_upload("cover", book.cover_file)
                book.cover_file, book.cover_url = None, cover_url
        if cover_name or cover_url:
            book.cover_fallback = None  # sampul baru dari admin menggantikan sampul bawaan
        if pdf_name:
            delete_upload("book", book.pdf_file)
            book.pdf_file = pdf_name
        db.session.commit()
        flash("Buku berhasil disimpan.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", book=book, values=book_values(book), categories=categories)


@admin_bp.route("/books/<int:book_id>/delete", methods=["POST"])
def book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    if book.loans.filter_by(status="borrowed").count():
        flash("Buku masih dipinjam, tidak bisa dihapus.", "danger")
    else:
        delete_upload("cover", book.cover_file)
        delete_upload("book", book.pdf_file)
        db.session.delete(book)
        db.session.commit()
        flash("Buku dihapus.", "success")
    return redirect(request.referrer or url_for("admin.books"))


# ---------------------------------------------------------------- Kategori
@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_bp.route("/categories/<int:cat_id>/edit", methods=["GET", "POST"])
def categories(cat_id=None):
    cat = db.get_or_404(Category, cat_id) if cat_id else None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()[:255]
        icon = request.form.get("icon", "").strip()[:8] or "📚"
        dup = Category.query.filter(func.lower(Category.name) == name.lower(),
                                    Category.id != (cat.id if cat else 0)).first()
        if not name or len(name) > 80:
            flash("Nama kategori wajib diisi (maks. 80 karakter).", "danger")
        elif dup:
            flash("Nama kategori sudah ada.", "danger")
        else:
            if not cat:
                cat = Category()
                db.session.add(cat)
            cat.name, cat.description, cat.icon = name, desc, icon
            db.session.commit()
            flash("Kategori disimpan.", "success")
            return redirect(url_for("admin.categories"))
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Category.query
    if q:
        query = query.filter(Category.name.ilike(like(q), escape="\\"))
    pag = query.order_by(Category.name).paginate(page=page, per_page=per_page(), error_out=False)
    return render_template("admin/categories.html", pag=pag, cat=cat)


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
def category_delete(cat_id):
    cat = db.get_or_404(Category, cat_id)
    if cat.books.count():
        flash("Kategori masih dipakai oleh buku. Pindahkan bukunya terlebih dahulu.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Kategori dihapus.", "success")
    return redirect(url_for("admin.categories"))


# -------------------------------------------------------------------- User
@admin_bp.route("/users")
def users():
    q = request.args.get("q", "").strip()
    role = request.args.get("role", "")
    page = request.args.get("page", 1, type=int)
    query = User.query
    if q:
        query = query.filter(or_(User.name.ilike(like(q), escape="\\"), User.username.ilike(like(q), escape="\\"),
                                 User.email.ilike(like(q), escape="\\")))
    if role in ("user", "admin"):
        query = query.filter(User.role == role)
    pag = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page(), error_out=False)
    return render_template("admin/users.html", pag=pag)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def user_form(user_id=None):
    user = db.get_or_404(User, user_id) if user_id else None
    if request.method == "POST":
        f = request.form
        name, username = f.get("name", "").strip(), f.get("username", "").strip().lower()
        email, password = f.get("email", "").strip().lower(), f.get("password", "")
        role = f.get("role", "user")
        active = f.get("active") == "on"
        uid = user.id if user else 0
        errors = []
        if len(name) < 2 or len(name) > 100:
            errors.append("Nama harus 2–100 karakter.")
        if not USERNAME_RE.match(username):
            errors.append("Username 3–30 karakter (huruf, angka, _).")
        elif User.query.filter(func.lower(User.username) == username, User.id != uid).first():
            errors.append("Username sudah dipakai.")
        if not valid_email(email):
            errors.append("Format email tidak valid.")
        elif User.query.filter(func.lower(User.email) == email, User.id != uid).first():
            errors.append("Email sudah dipakai.")
        if (not user or password) and len(password) < 8:
            errors.append("Password minimal 8 karakter.")
        if role not in ("user", "admin"):
            errors.append("Role tidak valid.")
        if user and user.id == current_user.id and (role != "admin" or not active):
            errors.append("Anda tidak bisa menurunkan role atau memblokir akun sendiri.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/user_form.html", user=user, values=f)
        if not user:
            user = User()
            db.session.add(user)
        user.name, user.username, user.email, user.role, user.active = name, username, email, role, active
        if password:
            user.set_password(password)
        db.session.commit()
        flash("User disimpan.", "success")
        return redirect(url_for("admin.users"))
    values = {"name": user.name, "username": user.username, "email": user.email, "role": user.role,
              "active": "on" if user.active else ""} if user else {"role": "user", "active": "on"}
    return render_template("admin/user_form.html", user=user, values=values)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
def user_toggle(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Anda tidak bisa memblokir akun sendiri.", "danger")
    else:
        user.active = not user.active
        db.session.commit()
        flash(f"Akun {user.username} {'diaktifkan' if user.active else 'diblokir'}.", "success")
    return redirect(request.referrer or url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def user_delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Anda tidak bisa menghapus akun sendiri.", "danger")
    else:
        for loan in user.loans.filter_by(status="borrowed"):  # kembalikan stok
            loan.book.stock += 1
        db.session.delete(user)
        db.session.commit()
        flash("User dihapus.", "success")
    return redirect(url_for("admin.users"))


# -------------------------------------------------------------- Peminjaman
@admin_bp.route("/loans")
def loans():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Loan.query.join(User).join(Book)
    if status == "overdue":
        query = query.filter(Loan.status == "borrowed", Loan.due_date < datetime.now())
    elif status in ("pending", "borrowed", "returned", "rejected"):
        query = query.filter(Loan.status == status)
    if q:
        query = query.filter(or_(User.name.ilike(like(q), escape="\\"), User.username.ilike(like(q), escape="\\"),
                                 Book.title.ilike(like(q), escape="\\")))
    pag = query.order_by(Loan.requested_at.desc()).paginate(page=page, per_page=per_page(), error_out=False)
    return render_template("admin/loans.html", pag=pag,
                           members=User.query.filter_by(role="user", active=True).order_by(User.name).all(),
                           physical=Book.query.filter_by(book_type="physical").order_by(Book.title).all())


@admin_bp.route("/loans/<int:loan_id>/<action>", methods=["POST"])
def loan_action(loan_id, action):
    loan = db.get_or_404(Loan, loan_id)
    if action == "approve" and loan.status == "pending":
        if loan.book.stock < 1:
            flash("Stok buku habis, tidak bisa disetujui.", "danger")
        else:
            loan.status, loan.borrowed_at = "borrowed", datetime.now()
            loan.due_date = loan.borrowed_at + timedelta(days=get_int("loan_days", 7))
            loan.book.stock -= 1
            db.session.commit()
            flash("Peminjaman disetujui.", "success")
    elif action == "reject" and loan.status == "pending":
        loan.status = "rejected"
        db.session.commit()
        flash("Peminjaman ditolak.", "info")
    elif action == "return" and loan.status == "borrowed":
        loan.status, loan.returned_at = "returned", datetime.now()
        loan.book.stock += 1
        db.session.commit()
        flash("Buku ditandai sudah dikembalikan.", "success")
    else:
        flash("Aksi tidak valid untuk status peminjaman ini.", "danger")
    return redirect(request.referrer or url_for("admin.loans"))


# ------------------------------------------------------------------ Ulasan
@admin_bp.route("/reviews")
def reviews():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Review.query.join(User).join(Book)
    if q:
        query = query.filter(or_(Review.comment.ilike(like(q), escape="\\"), User.username.ilike(like(q), escape="\\"),
                                 Book.title.ilike(like(q), escape="\\")))
    pag = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page(), error_out=False)
    return render_template("admin/reviews.html", pag=pag)


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
def review_delete(review_id):
    db.session.delete(db.get_or_404(Review, review_id))
    db.session.commit()
    flash("Ulasan dihapus.", "success")
    return redirect(request.referrer or url_for("admin.reviews"))


# ------------------------------------------- Ambil data dari link / cari cover (API)
@admin_bp.route("/api/fetch-meta", methods=["POST"])
def api_fetch_meta():
    """Dipanggil JavaScript: baca link (halaman, PDF, Gutenberg, gambar) lalu isi form otomatis."""
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not url:
        return jsonify(ok=False, error="Tempel link terlebih dahulu."), 400
    try:
        return jsonify(ok=True, data=fetch_page_meta(url))
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400


@admin_bp.route("/api/cover-search")
def api_cover_search():
    """Cari kandidat sampul buku di Open Library berdasarkan judul/penulis."""
    title = request.args.get("title", "").strip()
    if len(title) < 2:
        return jsonify(ok=False, error="Isi judul buku terlebih dahulu."), 400
    try:
        items = search_covers(title, request.args.get("author", "").strip())
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True, items=items)


# ------------------------------------------------------------ Impor massal buku
IMPORT_MAX_LINES, IMPORT_MAX_LINKS = 40, 10


@admin_bp.route("/books/import", methods=["GET", "POST"])
def books_import():
    """Tambah banyak buku sekaligus. Satu baris = satu buku:
    (a) hanya link  ->  data diambil otomatis dari halaman
    (b) Judul | Penulis | Kategori | Jenis | Link baca/unduh | URL cover | Stok"""
    report = []
    if request.method == "POST":
        save_local = request.form.get("save_local") == "on"
        default_cat = request.form.get("category_id", type=int)
        default_type = request.form.get("book_type", "digital")
        lines = [l.strip() for l in request.form.get("lines", "").splitlines() if l.strip() and not l.strip().startswith("#")]
        fetched = 0
        for line in lines[:IMPORT_MAX_LINES]:
            parts = [p.strip() for p in line.split("|")]
            try:
                d = {"book_type": default_type if default_type in ("digital", "physical") else "digital", "stock": 0}
                cat_name = ""
                if len(parts) == 1 and valid_url(parts[0]):
                    if fetched >= IMPORT_MAX_LINKS:
                        raise ValueError(f"Batas {IMPORT_MAX_LINKS} link per impor. Ulangi untuk sisanya.")
                    fetched += 1
                    meta = fetch_page_meta(parts[0])
                    d.update(title=meta["title"], author=meta["author"] or "Anonim", description=meta["description"],
                             read_url=meta["read_url"] or None, download_url=meta["download_url"] or None,
                             source=meta["source"], publisher=meta["publisher"], language=meta["language"] or "Indonesia",
                             year=int(meta["year"]) if meta["year"].isdigit() else None)
                    cover_ref = meta["cover_url"]
                else:
                    d["title"] = parts[0]
                    d["author"] = parts[1] if len(parts) > 1 and parts[1] else "Anonim"
                    cat_name = parts[2] if len(parts) > 2 else ""
                    if len(parts) > 3 and parts[3].lower() in ("fisik", "physical", "pinjam"):
                        d["book_type"] = "physical"
                    elif len(parts) > 3 and parts[3].lower() in ("digital", "gratis"):
                        d["book_type"] = "digital"
                    link = parts[4] if len(parts) > 4 else ""
                    if link and not valid_url(link):
                        raise ValueError("Link baca/unduh tidak valid")
                    if link:
                        d["read_url"] = d["download_url"] = link
                    cover_ref = parts[5] if len(parts) > 5 else ""
                    if cover_ref and not valid_url(cover_ref):
                        raise ValueError("URL cover tidak valid")
                    if len(parts) > 6 and parts[6].isdigit():
                        d["stock"] = int(parts[6])
                if not d.get("title"):
                    raise ValueError("Judul tidak ditemukan")
                d["title"], d["author"] = d["title"][:200], d["author"][:150]
                if Book.query.filter(func.lower(Book.title) == d["title"].lower(),
                                     func.lower(Book.author) == d["author"].lower()).first():
                    raise ValueError("sudah ada di katalog (dilewati)")
                if d["book_type"] == "physical" and not d["stock"]:
                    d["stock"] = 1
                cat = None
                if cat_name:
                    cat = Category.query.filter(func.lower(Category.name) == cat_name.lower()).first()
                    if not cat:
                        cat = Category(name=cat_name[:80], icon="📚")
                        db.session.add(cat)
                        db.session.flush()
                elif default_cat:
                    cat = db.session.get(Category, default_cat)
                book = Book(category_id=cat.id if cat else None, **d)
                note = ""
                if cover_ref:
                    if save_local:
                        name, err = download_cover(cover_ref)
                        if name:
                            book.cover_file = name
                        else:
                            book.cover_url, note = cover_ref, "cover dipakai lewat tautan (salin gagal)"
                    else:
                        book.cover_url = cover_ref
                db.session.add(book)
                db.session.commit()
                report.append((d["title"], True, note or "ditambahkan"))
            except ValueError as exc:
                db.session.rollback()
                report.append((line[:70], False, str(exc)))
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Impor gagal")
                report.append((line[:70], False, "kesalahan tak terduga"))
        if len(lines) > IMPORT_MAX_LINES:
            flash(f"Hanya {IMPORT_MAX_LINES} baris pertama yang diproses.", "warning")
        ok = sum(1 for r in report if r[1])
        flash(f"Impor selesai: {ok} buku ditambahkan, {len(report) - ok} dilewati/gagal.", "success" if ok else "warning")
    return render_template("admin/import.html", report=report, categories=Category.query.order_by(Category.name).all())


# --------------------------------------------------------------- Pengaturan
@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        f = request.form
        values = {k: f.get(k, "").strip() for k in ("site_name", "tagline", "address", "contact_email", "open_hours")}
        errors = []
        if not 1 <= len(values["site_name"]) <= 60:
            errors.append("Nama perpustakaan wajib diisi (maks. 60 karakter).")
        if values["contact_email"] and not valid_email(values["contact_email"]):
            errors.append("Format email kontak tidak valid.")
        for key, label, lo, hi in (("loan_days", "Lama pinjam", 1, 60), ("max_active_loans", "Batas pinjaman aktif", 1, 20)):
            val = f.get(key, type=int)
            if val is None or not lo <= val <= hi:
                errors.append(f"{label} harus {lo}–{hi}.")
            values[key] = val
        for key in ("require_approval", "allow_register", "allow_extend"):
            values[key] = "1" if f.get(key) == "on" else "0"
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/settings.html", s=f)
        save_settings(values)
        flash("Pengaturan disimpan.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", s=all_settings())


# --------------------------------------------- Tambah peminjaman manual (admin)
@admin_bp.route("/loans/new", methods=["POST"])
def loan_create():
    user = db.session.get(User, request.form.get("user_id", type=int) or 0)
    book = db.session.get(Book, request.form.get("book_id", type=int) or 0)
    if not user or not book:
        flash("Pilih anggota dan buku yang valid.", "danger")
    elif book.is_digital:
        flash("Buku digital tidak perlu dipinjam.", "warning")
    elif Loan.query.filter(Loan.user_id == user.id, Loan.book_id == book.id, Loan.status.in_(["pending", "borrowed"])).first():
        flash("Anggota ini masih meminjam buku tersebut.", "warning")
    elif not Book.query.filter(Book.id == book.id, Book.stock > 0).update({Book.stock: Book.stock - 1}):
        db.session.rollback()
        flash("Stok buku habis.", "danger")
    else:
        now = datetime.now()
        db.session.add(Loan(user_id=user.id, book_id=book.id, status="borrowed", borrowed_at=now,
                            due_date=now + timedelta(days=get_int("loan_days", 7))))
        db.session.commit()
        flash(f"Peminjaman “{book.title}” untuk {user.name} dicatat.", "success")
    return redirect(url_for("admin.loans"))
