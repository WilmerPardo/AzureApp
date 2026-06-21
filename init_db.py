# =============================================================
# init_db.py - TaskFlow SaaS
# Script opcional para inicializar Azure Cosmos DB for NoSQL.
#
# Ejecutar:
#   python init_db.py
# =============================================================

from services.cosmos_service import initialize_cosmos


if __name__ == "__main__":
    print("Conectando a Azure Cosmos DB for NoSQL...")
    initialize_cosmos()
    print("Base de datos y contenedores verificados correctamente:")
    print("   - users  partition key /id")
    print("   - tasks  partition key /userId")
    print("\nCosmos DB inicializado exitosamente.")
