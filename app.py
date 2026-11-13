"""Titik masuk aplikasi PustakaKu. Jalankan dengan:  python app.py"""
import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, logout_user
from flask_wtf.csrf import CSRFError
from sqlalchemy import inspect, text

from config import Config
from extensions import csrf, db, login_manager
from models import Loan, User
from utils import all_settings, parse_consent

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def ensure_default_admin(app, force_reset=False):
    """Pastikan akun admin default ada dan bisa dipakai login.
    - Dibuat jika belum ada.
    - Diperbaiki (role admin, aktif, hash valid) jika rusak. force_reset=True mengembalikan password default."""
    cfg = app.config
    admin = User.query.filter_by(username=cfg["DEFAULT_ADMIN_USERNAME"]).first()
    if not admin:
        admin = User(name="Administrator", username=cfg["DEFAULT_ADMIN_USERNAME"],
                     email=cfg["DEFAULT_ADMIN_EMAIL"], role="admin")
        admin.set_password(cfg["DEFAULT_ADMIN_PASSWORD"])
        db.session.add(admin)
    else:
        admin.role, admin.active = "admin", True
        try:
            from werkzeug.security import check_password_hash
            check_password_hash(admin.password_hash, "x")  # hash lama yang tak didukung akan error
        except (ValueError, AttributeError):
            force_reset = True
        if force_reset:
            admin.set_password(cfg["DEFAULT_ADMIN_PASSWORD"])
    db.session.commit()


def upgrade_schema():
    """Migrasi ringan: tambah kolom baru pada database lama (tanpa menghapus data)."""
    insp = inspect(db.engine)
    wanted = {"book": [("cover_fallback", "VARCHAR(200)")], "loan": [("extended", "BOOLEAN NOT NULL DEFAULT 0")]}
    for table, cols in wanted.items():
        if insp.has_table(table):
            have = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols:
                if name not in have:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
    db.session.commit()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    for sub in ("covers", "books"):
        os.makedirs(os.path.join(app.static_folder, "uploads", sub), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)  # proteksi CSRF untuk semua request POST

    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.user import user_bp
    for bp in (main_bp, auth_bp, user_bp, admin_bp):
        app.register_blueprint(bp)

    @app.before_request
    def block_inactive_users():
        # Jika akun diblokir admin saat sedang login, paksa logout
        if current_user.is_authenticated and not current_user.is_active:
            logout_user()
            flash("Akun Anda diblokir. Hubungi administrator.", "danger")
            return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_globals():
        overdue = 0
        if current_user.is_authenticated and not current_user.is_admin:
            overdue = Loan.query.filter(Loan.user_id == current_user.id, Loan.status == "borrowed",
                                        Loan.due_date < datetime.now()).count()
        site = all_settings()  # pengaturan situs dari Admin > Pengaturan
        return dict(
            consent=parse_consent(request.cookies.get("cookie_consent")),  # dibaca di sisi Python
            overdue_count=overdue,
            now=datetime.now(),
            site=site,
            app_name=site.get("site_name") or "PustakaKu",
        )

    @app.template_filter("tgl")
    def tgl(value, with_time=False):
        if not value:
            return "-"
        text = f"{value.day} {BULAN[value.month - 1]} {value.year}"
        return text + (value.strftime(" %H:%M") if with_time else "")

    @app.template_global()
    def page_url(page):
        """URL halaman yang sama dengan nomor halaman berbeda (filter tetap dipertahankan)."""
        args = request.args.to_dict()
        args.pop("partial", None)
        args["page"] = page
        return url_for(request.endpoint, **{**(request.view_args or {}), **args})

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        # Token kedaluwarsa / hilang: beri pesan jelas, bukan halaman error mentah
        flash("Formulir kedaluwarsa atau tidak valid. Muat ulang halaman lalu coba lagi.", "warning")
        return redirect(request.referrer or url_for("main.index"))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        flash("Ukuran file terlalu besar.", "danger")
        return redirect(request.referrer or url_for("main.index"))

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()
        upgrade_schema()
        ensure_default_admin(app)
    return app


app = create_app()

def pilih_port():
    """Cari port yang masih bisa dipakai (port 5000 sering diblokir Windows)."""
    import socket
    for port in (5001, 8000, 8080, 5050, 7000, 9000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 5001


if __name__ == "__main__":
    port = pilih_port()
    print(f"\n>>> Buka di browser: http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")