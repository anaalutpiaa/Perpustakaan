"""Fitur user: dashboard, pinjam/kembali, favorit, ulasan, riwayat, profil."""
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from extensions import db
from models import Book, Favorite, Loan, Review, User
from utils import USERNAME_RE, get_bool, get_int, valid_email

user_bp = Blueprint("user", __name__, url_prefix="/user")


def back(default_endpoint="user.dashboard", **kw):
    return redirect(request.referrer or url_for(default_endpoint, **kw))


@user_bp.route("/")
@login_required
def dashboard():
    loans = (Loan.query.filter(Loan.user_id == current_user.id, Loan.status.in_(["pending", "borrowed"]))
             .order_by(Loan.requested_at.desc()).all())
    stats = {
        "active": sum(1 for l in loans if l.status == "borrowed"),
        "overdue": sum(1 for l in loans if l.is_overdue),
        "favorites": Favorite.query.filter_by(user_id=current_user.id).count(),
        "history": Loan.query.filter_by(user_id=current_user.id).count(),
    }
    return render_template("user/dashboard.html", loans=loans, stats=stats)


@user_bp.route("/borrow/<int:book_id>", methods=["POST"])
@login_required
def borrow(book_id):
    """Pinjam buku fisik. Default: langsung aktif 7 hari (atau menunggu admin jika 'require_approval' aktif)."""
    book = db.get_or_404(Book, book_id)
    loan_days, max_loans = get_int("loan_days", 7), get_int("max_active_loans", 3)
    active = Loan.query.filter(Loan.user_id == current_user.id, Loan.status.in_(["pending", "borrowed"]))
    if current_user.is_admin:
        flash("Akun admin tidak dipakai untuk meminjam. Gunakan akun user, atau Admin > Peminjaman > Tambah peminjaman.", "warning")
    elif book.is_digital:
        flash("Buku digital tidak perlu dipinjam. Silakan baca atau unduh langsung.", "info")
    elif book.stock < 1:
        flash("Stok buku sedang habis.", "danger")
    elif active.filter(Loan.book_id == book.id).first():
        flash("Anda sudah meminjam atau mengajukan peminjaman buku ini.", "warning")
    elif active.count() >= max_loans:
        flash(f"Batas maksimal {max_loans} pinjaman aktif sudah tercapai.", "danger")
    elif Loan.query.filter(Loan.user_id == current_user.id, Loan.status == "borrowed",
                           Loan.due_date < datetime.now()).first():
        flash("Kembalikan buku yang terlambat terlebih dahulu sebelum meminjam lagi.", "danger")
    else:
        try:
            if get_bool("require_approval"):
                db.session.add(Loan(user_id=current_user.id, book_id=book.id, status="pending"))
                msg = "Permintaan pinjam dikirim dan menunggu persetujuan admin."
            else:
                # Kurangi stok secara atomik: gagal bila stok sudah diambil orang lain
                taken = Book.query.filter(Book.id == book.id, Book.stock > 0).update({Book.stock: Book.stock - 1})
                if not taken:
                    db.session.rollback()
                    flash("Stok baru saja habis.", "danger")
                    return back("main.book_detail", book_id=book.id)
                now = datetime.now()
                db.session.add(Loan(user_id=current_user.id, book_id=book.id, status="borrowed",
                                    borrowed_at=now, due_date=now + timedelta(days=loan_days)))
                msg = f"Berhasil! Buku “{book.title}” dipinjam. Kembalikan sebelum {(now + timedelta(days=loan_days)).strftime('%d-%m-%Y')}."
            db.session.commit()
            flash(msg, "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Gagal memproses peminjaman")
            flash("Terjadi kesalahan saat memproses peminjaman. Silakan coba lagi.", "danger")
    return back("main.book_detail", book_id=book.id)


@user_bp.route("/return/<int:loan_id>", methods=["POST"])
@login_required
def return_loan(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.user_id != current_user.id:
        flash("Pinjaman tidak ditemukan.", "danger")
    elif loan.status == "pending":  # batalkan permintaan
        db.session.delete(loan)
        db.session.commit()
        flash("Permintaan pinjam dibatalkan.", "info")
    elif loan.status == "borrowed":
        late = loan.days_late
        loan.status, loan.returned_at = "returned", datetime.now()
        loan.book.stock += 1
        db.session.commit()
        flash("Buku berhasil dikembalikan." + (f" Terlambat {late} hari." if late else " Terima kasih!"),
              "warning" if late else "success")
    else:
        flash("Pinjaman ini sudah selesai.", "info")
    return back()


@user_bp.route("/extend/<int:loan_id>", methods=["POST"])
@login_required
def extend_loan(loan_id):
    """Perpanjang masa pinjam satu kali (jika belum terlambat)."""
    loan = db.get_or_404(Loan, loan_id)
    if loan.user_id != current_user.id or loan.status != "borrowed":
        flash("Pinjaman tidak ditemukan.", "danger")
    elif not get_bool("allow_extend"):
        flash("Perpanjangan sedang dinonaktifkan oleh administrator.", "warning")
    elif loan.is_overdue:
        flash("Pinjaman yang sudah terlambat tidak bisa diperpanjang. Silakan kembalikan buku.", "danger")
    elif loan.extended:
        flash("Pinjaman ini sudah pernah diperpanjang.", "warning")
    else:
        days = get_int("loan_days", 7)
        loan.due_date += timedelta(days=days)
        loan.extended = True
        db.session.commit()
        flash(f"Diperpanjang {days} hari. Batas baru: {loan.due_date.strftime('%d-%m-%Y')}.", "success")
    return back()


@user_bp.route("/favorite/<int:book_id>", methods=["POST"])
@login_required
def favorite(book_id):
    book = db.get_or_404(Book, book_id)
    fav = Favorite.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if fav:
        db.session.delete(fav)
        state = False
    else:
        db.session.add(Favorite(user_id=current_user.id, book_id=book.id))
        state = True
    db.session.commit()
    if request.headers.get("X-Requested-With") == "fetch":  # dipanggil via JavaScript fetch
        return jsonify(ok=True, favorite=state)
    flash("Ditambahkan ke favorit." if state else "Dihapus dari favorit.", "success")
    return back("main.book_detail", book_id=book.id)


@user_bp.route("/review/<int:book_id>", methods=["POST"])
@login_required
def review(book_id):
    book = db.get_or_404(Book, book_id)
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()
    if rating not in (1, 2, 3, 4, 5):
        flash("Pilih rating 1–5 bintang.", "danger")
    elif len(comment) > 1000:
        flash("Ulasan maksimal 1000 karakter.", "danger")
    else:
        r = Review.query.filter_by(user_id=current_user.id, book_id=book.id).first()
        if r:
            r.rating, r.comment, r.created_at = rating, comment, datetime.now()
        else:
            db.session.add(Review(user_id=current_user.id, book_id=book.id, rating=rating, comment=comment))
        db.session.commit()
        flash("Ulasan Anda tersimpan.", "success")
    return redirect(url_for("main.book_detail", book_id=book.id) + "#ulasan")


@user_bp.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    r = db.get_or_404(Review, review_id)
    if r.user_id != current_user.id:
        flash("Anda tidak berhak menghapus ulasan ini.", "danger")
    else:
        db.session.delete(r)
        db.session.commit()
        flash("Ulasan dihapus.", "info")
    return back()


@user_bp.route("/favorites")
@login_required
def favorites():
    page = request.args.get("page", 1, type=int)
    pag = (Book.query.join(Favorite, Favorite.book_id == Book.id).filter(Favorite.user_id == current_user.id)
           .order_by(Favorite.created_at.desc()).paginate(page=page, per_page=12, error_out=False))
    return render_template("user/favorites.html", pag=pag)


@user_bp.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    pag = (Loan.query.filter_by(user_id=current_user.id).order_by(Loan.requested_at.desc())
           .paginate(page=page, per_page=10, error_out=False))
    return render_template("user/history.html", pag=pag)


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        errors = []
        if len(name) < 2 or len(name) > 100:
            errors.append("Nama harus 2–100 karakter.")
        if not USERNAME_RE.match(username):
            errors.append("Username 3–30 karakter (huruf, angka, _).")
        elif User.query.filter(func.lower(User.username) == username, User.id != current_user.id).first():
            errors.append("Username sudah dipakai.")
        if not valid_email(email):
            errors.append("Format email tidak valid.")
        elif User.query.filter(func.lower(User.email) == email, User.id != current_user.id).first():
            errors.append("Email sudah dipakai.")
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            current_user.name, current_user.username, current_user.email = name, username, email
            db.session.commit()
            flash("Profil diperbarui.", "success")
            return redirect(url_for("user.profile"))
    return render_template("user/profile.html")


@user_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    old, new, confirm = (request.form.get(k, "") for k in ("old_password", "new_password", "confirm"))
    if not current_user.check_password(old):
        flash("Password lama salah.", "danger")
    elif len(new) < 8:
        flash("Password baru minimal 8 karakter.", "danger")
    elif new != confirm:
        flash("Konfirmasi password baru tidak cocok.", "danger")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("Password berhasil diganti.", "success")
    return redirect(url_for("user.profile"))
