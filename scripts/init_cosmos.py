# =============================================================
# scripts/init_cosmos.py - TaskFlow SaaS
# Crea/verifica la base y contenedores en Azure Cosmos DB for NoSQL.
# =============================================================

import os
import sys
from pathlib import Path

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")


def _env(name, default=""):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _require(name):
    value = _env(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno {name}.")
    return value


def main():
    endpoint = _require("COSMOS_ENDPOINT")
    key = _require("COSMOS_KEY")
    database_name = _env("COSMOS_DATABASE_NAME", "taskflowdb")
    users_container_name = _env("COSMOS_USERS_CONTAINER", "users")
    tasks_container_name = _env("COSMOS_TASKS_CONTAINER", "tasks")

    print("Conectando a Azure Cosmos DB for NoSQL...")
    client = CosmosClient(endpoint, credential=key)

    print(f"Creando/verificando base de datos: {database_name}")
    database = client.create_database_if_not_exists(id=database_name)

    print(f"Creando/verificando contenedor: {users_container_name} (/id)")
    database.create_container_if_not_exists(
        id=users_container_name,
        partition_key=PartitionKey(path="/id"),
    )

    print(f"Creando/verificando contenedor: {tasks_container_name} (/userId)")
    database.create_container_if_not_exists(
        id=tasks_container_name,
        partition_key=PartitionKey(path="/userId"),
    )

    print("Inicializacion completada correctamente.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, CosmosHttpResponseError) as exc:
        print(f"Error al inicializar Cosmos DB: {exc}")
        raise SystemExit(1)
