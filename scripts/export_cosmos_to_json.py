# =============================================================
# scripts/export_cosmos_to_json.py - TaskFlow SaaS
# Exporta users y tasks desde Cosmos DB a archivos JSON locales.
# =============================================================

import json
import os
import sys
from pathlib import Path

from azure.cosmos import CosmosClient
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


def _container(database, name):
    return database.get_container_client(name)


def _strip_cosmos_metadata(item):
    return {key: value for key, value in item.items() if not key.startswith("_")}


def main():
    endpoint = _require("COSMOS_ENDPOINT")
    key = _require("COSMOS_KEY")
    database_name = _env("COSMOS_DATABASE_NAME", "taskflowdb")
    users_container_name = _env("COSMOS_USERS_CONTAINER", "users")
    tasks_container_name = _env("COSMOS_TASKS_CONTAINER", "tasks")

    client = CosmosClient(endpoint, credential=key)
    database = client.get_database_client(database_name)
    users_container = _container(database, users_container_name)
    tasks_container = _container(database, tasks_container_name)

    users = [
        _strip_cosmos_metadata(item)
        for item in users_container.query_items(
            query="SELECT * FROM c WHERE c.type = 'user'",
            enable_cross_partition_query=True,
        )
    ]
    tasks = [
        _strip_cosmos_metadata(item)
        for item in tasks_container.query_items(
            query="SELECT * FROM c WHERE c.type = 'task'",
            enable_cross_partition_query=True,
        )
    ]

    backups_dir = ROOT_DIR / "backups"
    backups_dir.mkdir(exist_ok=True)

    users_path = backups_dir / "users_backup.json"
    tasks_path = backups_dir / "tasks_backup.json"

    users_path.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")
    tasks_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Usuarios exportados: {len(users)} -> {users_path}")
    print(f"Tareas exportadas: {len(tasks)} -> {tasks_path}")
    print("No se exportaron claves ni secretos de configuracion.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, CosmosHttpResponseError) as exc:
        print(f"Error durante la exportacion: {exc}")
        raise SystemExit(1)
