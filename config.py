# =============================================================
# config.py — TaskFlow SaaS
# Configuración de la aplicación. Lee variables de entorno.
# =============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables del archivo .env en desarrollo local
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # ── Seguridad ──────────────────────────────────────────────
    # SECRET_KEY se debe definir en las variables de entorno
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # ── Base de datos ──────────────────────────────────────────
    # SQLite es el valor por defecto para simplificar el despliegue en Azure.
    # En Azure App Service, /home es persistente entre reinicios y despliegues.
    _database_url = os.environ.get("DATABASE_URL", "").strip()
    _use_database_url = os.environ.get("USE_DATABASE_URL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    _sqlite_path = os.environ.get("SQLITE_DB_PATH", "").strip()
    if not _sqlite_path:
        if os.environ.get("WEBSITE_SITE_NAME") and os.environ.get("HOME"):
            _sqlite_path = str(Path(os.environ["HOME"]) / "site" / "data" / "taskflow.db")
        else:
            _sqlite_path = str(BASE_DIR / "instance" / "taskflow.db")

    SQLITE_DB_PATH = Path(_sqlite_path).expanduser().resolve()
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    _sqlite_database_uri = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"
    SQLALCHEMY_DATABASE_URI = (
        _database_url if _use_database_url and _database_url else _sqlite_database_uri
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Evitar overhead innecesario
    _engine_options = {}
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        _engine_options["connect_args"] = {"check_same_thread": False}
    else:
        _engine_options.update(
            {
                "pool_pre_ping": True,
                "pool_recycle": 280,
            }
        )
    _mysql_ssl_ca = os.environ.get("MYSQL_SSL_CA")
    if SQLALCHEMY_DATABASE_URI.startswith("mysql") and _mysql_ssl_ca:
        _engine_options["connect_args"] = {"ssl": {"ca": _mysql_ssl_ca}}
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options

    # ── Flask-WTF ──────────────────────────────────────────────
    WTF_CSRF_ENABLED = True

    # ── Flask-Login ────────────────────────────────────────────
    # Si el usuario intenta acceder a una ruta privada, se redirige aquí
    LOGIN_VIEW = "login"
