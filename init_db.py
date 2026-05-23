# =============================================================
# init_db.py — TaskFlow SaaS
# Script para inicializar la base de datos MySQL.
# Ejecutar una sola vez antes del primer despliegue:
#   python init_db.py
# =============================================================

from app import app
from models import db

with app.app_context():
    print("Conectando a la base de datos...")
    db.create_all()
    print("Tablas creadas correctamente:")
    print("   - users")
    print("   - tasks")
    print("\nBase de datos inicializada exitosamente!")
    print("Ahora puedes ejecutar: flask run  o  gunicorn app:app")
