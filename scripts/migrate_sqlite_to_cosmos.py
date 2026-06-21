# =============================================================
# scripts/migrate_sqlite_to_cosmos.py - TaskFlow SaaS
# Migra datos desde SQLite a Azure Cosmos DB for NoSQL.
# =============================================================

import os
import sqlite3
import sys
from datetime import datetime
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


def _sqlite_path():
    configured = _env("SQLITE_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (ROOT_DIR / "instance" / "taskflow.db").resolve()


def _read_sqlite_rows(sqlite_db_path):
    if not sqlite_db_path.exists():
        raise FileNotFoundError(f"No existe la base SQLite: {sqlite_db_path}")

    connection = sqlite3.connect(sqlite_db_path)
    connection.row_factory = sqlite3.Row
    try:
        users = connection.execute(
            "SELECT id, name, email, password_hash, created_at FROM users"
        ).fetchall()
        tasks = connection.execute(
            "SELECT id, title, description, status, created_at, user_id FROM tasks"
        ).fetchall()
        return users, tasks
    finally:
        connection.close()


def _normalize_email(email):
    return (email or "").strip().lower()


def _iso_datetime(value):
    if not value:
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    text = str(value).strip()
    if text.endswith("Z"):
        return text

    try:
        parsed = datetime.fromisoformat(text.replace(" ", "T"))
        return parsed.replace(microsecond=0).isoformat() + "Z"
    except ValueError:
        return text


def _cosmos_containers():
    endpoint = _require("COSMOS_ENDPOINT")
    key = _require("COSMOS_KEY")
    database_name = _env("COSMOS_DATABASE_NAME", "taskflowdb")
    users_container_name = _env("COSMOS_USERS_CONTAINER", "users")
    tasks_container_name = _env("COSMOS_TASKS_CONTAINER", "tasks")

    client = CosmosClient(endpoint, credential=key)
    database = client.create_database_if_not_exists(id=database_name)
    users_container = database.create_container_if_not_exists(
        id=users_container_name,
        partition_key=PartitionKey(path="/id"),
    )
    tasks_container = database.create_container_if_not_exists(
        id=tasks_container_name,
        partition_key=PartitionKey(path="/userId"),
    )
    return users_container, tasks_container


def _migrate_users(users_container, users):
    old_id_to_email = {}
    migrated = 0

    for row in users:
        email = _normalize_email(row["email"])
        if not email:
            print(f"Usuario SQLite id={row['id']} omitido: email vacio.")
            continue

        document = {
            "id": email,
            "type": "user",
            "name": row["name"] or "",
            "email": email,
            "password_hash": row["password_hash"] or "",
            "created_at": _iso_datetime(row["created_at"]),
        }

        users_container.upsert_item(document)
        old_id_to_email[row["id"]] = email
        migrated += 1

    return old_id_to_email, migrated


def _migrate_tasks(tasks_container, tasks, old_id_to_email):
    migrated = 0
    skipped = 0

    for row in tasks:
        owner_email = old_id_to_email.get(row["user_id"])
        if not owner_email:
            print(
                "Tarea SQLite id="
                f"{row['id']} omitida: usuario {row['user_id']} no encontrado."
            )
            skipped += 1
            continue

        status = row["status"] if row["status"] in ("pendiente", "completada") else "pendiente"
        document = {
            "id": str(row["id"]),
            "type": "task",
            "userId": owner_email,
            "title": row["title"] or "",
            "description": row["description"] or "",
            "status": status,
            "created_at": _iso_datetime(row["created_at"]),
        }

        tasks_container.upsert_item(document)
        migrated += 1

    return migrated, skipped


def main():
    sqlite_db_path = _sqlite_path()
    print(f"Leyendo SQLite desde: {sqlite_db_path}")
    users, tasks = _read_sqlite_rows(sqlite_db_path)

    print("Conectando a Azure Cosmos DB for NoSQL...")
    users_container, tasks_container = _cosmos_containers()

    old_id_to_email, users_count = _migrate_users(users_container, users)
    tasks_count, skipped_tasks = _migrate_tasks(
        tasks_container, tasks, old_id_to_email
    )

    print("Migracion completada.")
    print(f"Usuarios migrados: {users_count}")
    print(f"Tareas migradas: {tasks_count}")
    print(f"Tareas omitidas: {skipped_tasks}")
    print(f"SQLite original conservado en: {sqlite_db_path}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, sqlite3.Error, CosmosHttpResponseError) as exc:
        print(f"Error durante la migracion: {exc}")
        raise SystemExit(1)
