"""Objek ekstensi Flask dibuat di sini agar tidak terjadi circular import."""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu untuk mengakses halaman ini."
login_manager.login_message_category = "warning"
