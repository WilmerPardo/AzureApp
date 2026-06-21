# =============================================================
# config.py - TaskFlow SaaS
# Configuracion de Flask y Azure Cosmos DB for NoSQL.
# =============================================================

import os

from dotenv import load_dotenv


load_dotenv()


def _env(name, default=""):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _is_production_environment():
    return bool(
        os.environ.get("WEBSITE_SITE_NAME")
        or _env("FLASK_ENV").lower() == "production"
        or _env("APP_ENV").lower() == "production"
    )


class Config:
    # Seguridad
    SECRET_KEY = _env("SECRET_KEY", "dev-secret-key-change-in-production")

    # Base de Datos
    SQLALCHEMY_DATABASE_URI = _env("DATABASE_URL", "sqlite:///taskflow.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF
    WTF_CSRF_ENABLED = True

    # Flask-Login
    LOGIN_VIEW = "login"
