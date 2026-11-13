"""Register, login, logout."""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from extensions import db
from models import Loan, User
from utils import USERNAME_RE, get_bool, is_safe_next, valid_email

auth_bp = Blueprint("auth", __name__)


def home_for(user):
    """Redirect sesuai role."""
    return url_for("admin.dashboard") if user.is_admin else url_for("user.dashboard")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(home_for(current_user))
    if not get_bool("allow_register"):
        flash("Pendaftaran anggota baru sedang ditutup oleh administrator.", "warning")
        return redirect(url_for("auth.login"))
    form = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("name", "username", "email")}
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        errors = []
        if len(form["name"]) < 2 or len(form["name"]) > 100:
            errors.append("Nama lengkap harus 2–100 karakter.")
        if not USERNAME_RE.match(form["username"]):
            errors.append("Username 3–30 karakter, hanya huruf, angka, dan garis bawah (_).")
        elif User.query.filter(func.lower(User.username) == form["username"].lower()).first():
            errors.append("Username sudah dipakai.")
        if not valid_email(form["email"]):
            errors.append("Format email tidak valid.")
        elif User.query.filter(func.lower(User.email) == form["email"].lower()).first():
            errors.append("Email sudah terdaftar.")
        if len(password) < 8:
            errors.append("Password minimal 8 karakter.")
        if password != confirm:
            errors.append("Konfirmasi password tidak cocok.")
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user = User(name=form["name"], username=form["username"].lower(),
                        email=form["email"].lower(), role="user")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registrasi berhasil! Silakan login.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(home_for(current_user))
    if request.method == "POST":
        ident = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        user = User.query.filter((func.lower(User.username) == ident) | (func.lower(User.email) == ident)).first()
        if not user or not user.check_password(password):
            flash("Username/email atau password salah.", "danger")
        elif not user.is_active:
            flash("Akun Anda diblokir. Hubungi administrator.", "danger")
        else:
            login_user(user, remember=remember)
            flash(f"Selamat datang, {user.name}!", "success")
            if not user.is_admin:
                late = Loan.query.filter(Loan.user_id == user.id, Loan.status == "borrowed",
                                         Loan.due_date < datetime.now()).count()
                if late:
                    flash(f"Perhatian: {late} buku Anda melewati batas pengembalian. Segera kembalikan.", "warning")
            nxt = request.args.get("next")
            return redirect(nxt if is_safe_next(nxt) else home_for(user))
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Anda telah keluar.", "info")
    return redirect(url_for("main.index"))
