"""Model database (SQLAlchemy ORM). Semua query lewat ORM => aman dari SQL Injection."""
from datetime import datetime

from flask import url_for
from flask_login import UserMixin
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")  # "user" | "admin"
    active = db.Column(db.Boolean, nullable=False, default=True)     # False = diblokir
    created_at = db.Column(db.DateTime, default=datetime.now)

    loans = db.relationship("Loan", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    reviews = db.relationship("Review", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    favorites = db.relationship("Favorite", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    # Password selalu disimpan dalam bentuk hash, tidak pernah teks biasa
    def set_password(self, password):
        # pbkdf2:sha256 tersedia di semua build Python (scrypt bisa tidak ada di sebagian instalasi)
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except (ValueError, AttributeError):  # hash lama dengan algoritma yang tidak didukung
            return False

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_active(self):  # dipakai Flask-Login; akun diblokir tidak bisa login
        return self.active


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), default="")
    icon = db.Column(db.String(8), default="📚")
    books = db.relationship("Book", backref="category", lazy="dynamic")


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, default="")
    year = db.Column(db.Integer)
    publisher = db.Column(db.String(150), default="")
    language = db.Column(db.String(30), default="Indonesia")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    stock = db.Column(db.Integer, nullable=False, default=0)           # hanya untuk buku fisik
    book_type = db.Column(db.String(10), nullable=False, default="digital")  # "digital" | "physical"
    cover_file = db.Column(db.String(120))     # file cover hasil upload
    cover_url = db.Column(db.String(500))      # atau URL cover eksternal
    cover_fallback = db.Column(db.String(200)) # gambar sampul lokal (static/...) bila sampul utama gagal dimuat
    pdf_file = db.Column(db.String(120))       # file PDF hasil upload
    read_url = db.Column(db.String(500))       # tautan baca online (sumber legal)
    download_url = db.Column(db.String(500))   # tautan unduh (sumber legal)
    source = db.Column(db.String(200), default="")  # sumber & lisensi
    views = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

    loans = db.relationship("Loan", backref="book", cascade="all, delete-orphan", lazy="dynamic")
    reviews = db.relationship("Review", backref="book", cascade="all, delete-orphan", lazy="dynamic")
    favorites = db.relationship("Favorite", backref="book", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def is_digital(self):
        return self.book_type == "digital"

    @property
    def type_label(self):
        return "Gratis/Digital" if self.is_digital else "Fisik/Pinjam"

    @property
    def cover_backup(self):
        """Gambar sampul lokal bawaan (dibuat oleh make_covers.py)."""
        return url_for("static", filename=self.cover_fallback) if self.cover_fallback else None

    @property
    def cover_src(self):
        """Urutan prioritas: file upload admin -> sampul bawaan unik (static/img/covers) -> URL eksternal."""
        if self.cover_file:
            return url_for("static", filename="uploads/covers/" + self.cover_file)
        return self.cover_backup or self.cover_url

    @property
    def avg_rating(self):
        value = db.session.query(func.avg(Review.rating)).filter(Review.book_id == self.id).scalar()
        return round(float(value), 1) if value else 0

    @property
    def rating_count(self):
        return Review.query.filter_by(book_id=self.id).count()

    @property
    def loan_count(self):
        return Loan.query.filter_by(book_id=self.id).count()


class Loan(db.Model):
    """Status: pending (menunggu persetujuan) -> borrowed (dipinjam) -> returned / rejected."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, default="pending", index=True)
    requested_at = db.Column(db.DateTime, default=datetime.now)
    borrowed_at = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    extended = db.Column(db.Boolean, nullable=False, default=False)  # sudah diperpanjang 1x

    @property
    def is_overdue(self):
        return self.status == "borrowed" and self.due_date is not None and self.due_date < datetime.now()

    @property
    def days_late(self):
        return (datetime.now() - self.due_date).days if self.is_overdue else 0

    @property
    def days_left(self):
        if self.status != "borrowed" or not self.due_date:
            return None
        return (self.due_date - datetime.now()).days

    @property
    def status_label(self):
        if self.is_overdue:
            return "Terlambat"
        return {"pending": "Menunggu persetujuan", "borrowed": "Dipinjam",
                "returned": "Dikembalikan", "rejected": "Ditolak"}.get(self.status, self.status)

    @property
    def status_class(self):
        if self.is_overdue:
            return "danger"
        return {"pending": "warning", "borrowed": "info", "returned": "success",
                "rejected": "muted"}.get(self.status, "muted")


class Review(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)


class Favorite(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="uq_fav_user_book"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Setting(db.Model):
    """Pengaturan situs (key-value) yang bisa diubah admin."""
    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.Text, default="")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
