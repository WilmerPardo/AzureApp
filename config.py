# =============================================================
# config.py — TaskFlow SaaS
# Configuración de la aplicación. Lee variables de entorno.
# =============================================================

import os
from dotenv import load_dotenv

# Cargar variables del archivo .env en desarrollo local
load_dotenv()


class Config:
    # ── Seguridad ──────────────────────────────────────────────
    # SECRET_KEY se debe definir en las variables de entorno
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # ── Base de datos ──────────────────────────────────────────
    # DATABASE_URL debe apuntar a MySQL (local o Azure)
    _database_url = os.environ.get("DATABASE_URL", "")

    SQLALCHEMY_DATABASE_URI = _database_url or "mysql+pymysql://root:password@localhost:3306/taskflowdb?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Evitar overhead innecesario
    _engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    _mysql_ssl_ca = os.environ.get("MYSQL_SSL_CA")
    if SQLALCHEMY_DATABASE_URI.startswith("mysql") and _mysql_ssl_ca:
        _engine_options["connect_args"] = {"ssl": {"ca": _mysql_ssl_ca}}
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options

    # ── Flask-WTF ──────────────────────────────────────────────
    WTF_CSRF_ENABLED = True

    # ── Flask-Login ────────────────────────────────────────────
    # Si el usuario intenta acceder a una ruta privada, se redirige aquí
    LOGIN_VIEW = "login"
