"""Halaman publik: beranda, katalog, detail, baca/unduh, live search, cookie consent."""
import os
import re

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from extensions import db
from models import Book, Category, Favorite, Loan, Review, User
from utils import build_consent, like_escape, upload_dir, valid_url

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    new_books = Book.query.order_by(Book.created_at.desc(), Book.id.desc()).limit(8).all()
    popular = Book.query.order_by(Book.views.desc(), Book.id).limit(8).all()
    cats = (db.session.query(Category, func.count(Book.id))
            .outerjoin(Book, Book.category_id == Category.id)
            .group_by(Category.id).order_by(Category.name).all())
    stats = {
        "books": Book.query.count(),
        "digital": Book.query.filter_by(book_type="digital").count(),
        "members": User.query.filter_by(role="user").count(),
        "categories": len(cats),
    }
    return render_template("index.html", new_books=new_books, popular=popular, cats=cats, stats=stats)


@main_bp.route("/books")
def books():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", type=int)
    author = request.args.get("author", "").strip()
    year = request.args.get("year", type=int)
    btype = request.args.get("type", "")
    sort = request.args.get("sort", "terbaru")
    page = request.args.get("page", 1, type=int)

    query = Book.query
    if q:
        like = f"%{like_escape(q)}%"
        query = query.filter(or_(Book.title.ilike(like, escape="\\"), Book.author.ilike(like, escape="\\"),
                                 Book.publisher.ilike(like, escape="\\")))
    if category:
        query = query.filter(Book.category_id == category)
    if author:
        query = query.filter(Book.author.ilike(f"%{like_escape(author)}%", escape="\\"))
    if year:
        query = query.filter(Book.year == year)
    if btype in ("digital", "physical"):
        query = query.filter(Book.book_type == btype)

    order = {"populer": (Book.views.desc(), Book.id), "judul": (func.lower(Book.title),)}.get(
        sort, (Book.created_at.desc(), Book.id.desc()))
    pag = query.order_by(*order).paginate(page=page, per_page=current_app.config["PER_PAGE"], error_out=False)

    if request.args.get("partial"):  # dipakai live search (fetch) untuk mengganti grid saja
        return render_template("_book_grid.html", pag=pag)
    categories = Category.query.order_by(Category.name).all()
    return render_template("books.html", pag=pag, categories=categories)


@main_bp.route("/api/search")
def api_search():
    """Endpoint live search: mengembalikan JSON hasil pencarian cepat."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify(results=[])
    like = f"%{like_escape(q)}%"
    rows = (Book.query.filter(or_(Book.title.ilike(like, escape="\\"), Book.author.ilike(like, escape="\\")))
            .order_by(Book.views.desc()).limit(8).all())
    return jsonify(results=[{
        "id": b.id, "title": b.title, "author": b.author, "type": b.type_label,
        "url": url_for("main.book_detail", book_id=b.id), "cover": b.cover_src,
    } for b in rows])


@main_bp.route("/api/cookie-consent", methods=["POST"])
def cookie_consent():
    """Validasi pilihan cookie di sisi server lalu set cookie 'cookie_consent' selama 365 hari."""
    data = request.get_json(silent=True) or {}
    resp = jsonify(ok=True)
    resp.set_cookie("cookie_consent", build_consent(data.get("analytics") is True, data.get("marketing") is True),
                    max_age=current_app.config["COOKIE_CONSENT_DAYS"] * 86400, path="/",
                    samesite="Lax", secure=request.is_secure, httponly=False)
    return resp


@main_bp.route("/book/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    book.views += 1
    db.session.commit()
    reviews = Review.query.filter_by(book_id=book.id).order_by(Review.created_at.desc()).limit(30).all()
    related = (Book.query.filter(Book.category_id == book.category_id, Book.id != book.id)
               .order_by(Book.views.desc()).limit(4).all())
    my_review = is_fav = active_loan = None
    if current_user.is_authenticated:
        my_review = Review.query.filter_by(user_id=current_user.id, book_id=book.id).first()
        is_fav = Favorite.query.filter_by(user_id=current_user.id, book_id=book.id).first() is not None
        active_loan = Loan.query.filter(Loan.user_id == current_user.id, Loan.book_id == book.id,
                                        Loan.status.in_(["pending", "borrowed"])).first()
    return render_template("book_detail.html", book=book, reviews=reviews, related=related,
                           my_review=my_review, is_fav=is_fav, active_loan=active_loan)


@main_bp.route("/book/<int:book_id>/read")
@login_required
def read(book_id):
    book = db.get_or_404(Book, book_id)
    if not book.is_digital or not (book.pdf_file or book.read_url):
        flash("Buku ini tidak tersedia untuk dibaca online.", "warning")
        return redirect(url_for("main.book_detail", book_id=book.id))
    book.views += 1
    db.session.commit()
    src = url_for("main.pdf_file", filename=book.pdf_file) if book.pdf_file else book.read_url
    return render_template("read.html", book=book, src=src)


@main_bp.route("/book/<int:book_id>/download")
@login_required
def download(book_id):
    book = db.get_or_404(Book, book_id)
    if not book.is_digital:
        abort(404)
    if book.pdf_file:
        safe = re.sub(r"[^A-Za-z0-9]+", "-", book.title).strip("-")[:60] or "buku"
        return send_from_directory(upload_dir("book"), book.pdf_file, as_attachment=True,
                                   download_name=f"{safe}.pdf")
    if book.download_url and valid_url(book.download_url):
        return redirect(book.download_url)
    flash("Berkas unduhan belum tersedia.", "warning")
    return redirect(url_for("main.book_detail", book_id=book.id))


@main_bp.route("/files/<path:filename>")
@login_required
def pdf_file(filename):
    """Menyajikan PDF unggahan (inline) untuk fitur baca online."""
    return send_from_directory(upload_dir("book"), os.path.basename(filename), mimetype="application/pdf")
