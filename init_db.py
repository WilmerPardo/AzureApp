# =============================================================
# init_db.py - TaskFlow SaaS
# Script opcional para inicializar la base configurada.
#
# Usa la misma prioridad de config.py:
#   1. DATABASE_URL
#   2. AZURE_POSTGRESQL_*
#   3. SQLite local
#
# Ejecutar solo si quieres preparar las tablas manualmente:
#   python init_db.py
# =============================================================

from app import app
from models import db

with app.app_context():
    print("Conectando a la base de datos configurada...")
    db.create_all()
    print("Tablas creadas/verificadas correctamente:")
    print("   - users")
    print("   - tasks")
    print("\nBase de datos inicializada exitosamente.")
    print("Ahora puedes ejecutar: flask run  o  gunicorn app:app")
