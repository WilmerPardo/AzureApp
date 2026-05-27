# =============================================================
# config.py - TaskFlow SaaS
# Configuracion de la aplicacion. Lee variables de entorno.
# =============================================================

import os
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv

# Cargar variables del archivo .env en desarrollo local.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _env(name):
    return os.environ.get(name, "").strip()


def _is_azure_postgres_host(hostname):
    return bool(hostname and hostname.endswith(".postgres.database.azure.com"))


def _ensure_azure_sslmode(database_url):
    parts = urlsplit(database_url)
    if not _is_azure_postgres_host(parts.hostname):
        return database_url

    query_items = parse_qsl(parts.query, keep_blank_values=True)
    if any(key.lower() == "sslmode" for key, _ in query_items):
        return database_url

    query_items.append(("sslmode", "require"))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_items), parts.fragment)
    )


def normalize_database_url(database_url):
    """Normalize PostgreSQL URLs for SQLAlchemy + psycopg2."""
    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgres://") :]
    elif database_url.startswith("postgresql://"):
        database_url = (
            "postgresql+psycopg2://" + database_url[len("postgresql://") :]
        )

    if database_url.startswith("postgresql+psycopg2://"):
        database_url = _ensure_azure_sslmode(database_url)

    return database_url


def _azure_postgres_url_from_env():
    azure_vars = {
        "AZURE_POSTGRESQL_USER": _env("AZURE_POSTGRESQL_USER"),
        "AZURE_POSTGRESQL_PASSWORD": _env("AZURE_POSTGRESQL_PASSWORD"),
        "AZURE_POSTGRESQL_HOST": _env("AZURE_POSTGRESQL_HOST"),
        "AZURE_POSTGRESQL_NAME": _env("AZURE_POSTGRESQL_NAME"),
    }

    if not any(azure_vars.values()):
        return None

    missing = [name for name, value in azure_vars.items() if not value]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno para PostgreSQL en Azure: "
            + ", ".join(missing)
        )

    host = azure_vars["AZURE_POSTGRESQL_HOST"].replace("https://", "").replace(
        "http://", ""
    )
    host = host.strip("/")
    if ":" not in host:
        host = f"{host}:5432"

    username = quote(azure_vars["AZURE_POSTGRESQL_USER"], safe="")
    password = quote(azure_vars["AZURE_POSTGRESQL_PASSWORD"], safe="")
    database_name = quote(azure_vars["AZURE_POSTGRESQL_NAME"], safe="")

    return (
        f"postgresql+psycopg2://{username}:{password}@{host}/{database_name}"
        "?sslmode=require"
    )


def resolve_sqlite_path():
    sqlite_path = _env("SQLITE_DB_PATH")
    if sqlite_path:
        return Path(sqlite_path).expanduser().resolve()

    if os.environ.get("WEBSITE_SITE_NAME") and os.environ.get("HOME"):
        return Path(os.environ["HOME"], "site", "data", "taskflow.db").resolve()

    return Path(BASE_DIR, "instance", "taskflow.db").resolve()


def _configured_external_database_url():
    database_url = _env("DATABASE_URL")
    if database_url:
        return normalize_database_url(database_url)

    return _azure_postgres_url_from_env()


def get_database_uri():
    external_database_url = _configured_external_database_url()
    if external_database_url:
        return external_database_url

    sqlite_path = resolve_sqlite_path()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path.as_posix()}"


def get_postgres_database_uri():
    postgres_url = _configured_external_database_url()
    if not postgres_url:
        raise RuntimeError(
            "Configura DATABASE_URL o las variables AZURE_POSTGRESQL_* para "
            "usar PostgreSQL como destino."
        )

    if not postgres_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise RuntimeError("La conexion de destino debe ser PostgreSQL.")

    return postgres_url


def build_engine_options(database_uri):
    if database_uri.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}

    return {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }


class Config:
    # Seguridad
    # SECRET_KEY se debe definir en las variables de entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Base de datos
    # Prioridad: DATABASE_URL, variables AZURE_POSTGRESQL_* y fallback SQLite.
    SQLITE_DB_PATH = resolve_sqlite_path()
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = build_engine_options(SQLALCHEMY_DATABASE_URI)

    # Flask-WTF
    WTF_CSRF_ENABLED = True

    # Flask-Login
    # Si el usuario intenta acceder a una ruta privada, se redirige aqui.
    LOGIN_VIEW = "login"
