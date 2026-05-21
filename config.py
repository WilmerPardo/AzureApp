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
    # DATABASE_URL debe apuntar a PostgreSQL (local o Azure)
    _database_url = os.environ.get("DATABASE_URL", "")

    # Azure PostgreSQL requiere sslmode=require en la cadena de conexión.
    # Si la URL no lo incluye, se agrega automáticamente.
    if _database_url and "sslmode" not in _database_url:
        # Solo agregar sslmode si la URL apunta a un host remoto (no localhost)
        if "localhost" not in _database_url and "127.0.0.1" not in _database_url:
            _database_url += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = _database_url or "postgresql://postgres:password@localhost:5432/taskflowdb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Evitar overhead innecesario

    # ── Flask-WTF ──────────────────────────────────────────────
    WTF_CSRF_ENABLED = True

    # ── Flask-Login ────────────────────────────────────────────
    # Si el usuario intenta acceder a una ruta privada, se redirige aquí
    LOGIN_VIEW = "login"
