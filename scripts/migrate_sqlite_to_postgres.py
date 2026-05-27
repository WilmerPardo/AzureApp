#!/usr/bin/env python
# =============================================================
# Migracion SQLite -> PostgreSQL para TaskFlow SaaS
#
# Uso:
#   python scripts/migrate_sqlite_to_postgres.py
#
# Variables:
#   SQLITE_DB_PATH=instance/taskflow.db
#   DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/db?sslmode=require
#
# Tambien acepta AZURE_POSTGRESQL_USER, AZURE_POSTGRESQL_PASSWORD,
# AZURE_POSTGRESQL_HOST y AZURE_POSTGRESQL_NAME si DATABASE_URL no existe.
# =============================================================

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import build_engine_options, get_postgres_database_uri  # noqa: E402
from models import Task, User, db  # noqa: E402


def _sqlite_path():
    raw_path = os.environ.get("SQLITE_DB_PATH", "").strip()
    path = Path(raw_path) if raw_path else PROJECT_ROOT / "instance" / "taskflow.db"
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.expanduser().resolve()


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if value is None or value == "":
        return datetime.utcnow()

    text_value = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text_value)
    except ValueError as exc:
        raise ValueError(f"Fecha invalida en SQLite: {value!r}") from exc


def _read_sqlite_rows(sqlite_db_path):
    if not sqlite_db_path.exists():
        raise FileNotFoundError(
            f"No existe la base SQLite: {sqlite_db_path}. "
            "Define SQLITE_DB_PATH si esta en otra ruta."
        )

    try:
        connection = sqlite3.connect(sqlite_db_path)
        connection.row_factory = sqlite3.Row
        with connection:
            users = connection.execute(
                """
                SELECT id, name, email, password_hash, created_at
                FROM users
                ORDER BY id
                """
            ).fetchall()
            tasks = connection.execute(
                """
                SELECT id, title, description, status, created_at, user_id
                FROM tasks
                ORDER BY id
                """
            ).fetchall()
        return users, tasks
    except sqlite3.Error as exc:
        raise RuntimeError(f"No se pudo leer SQLite: {exc}") from exc
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass


def _create_postgres_app(postgres_uri):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = postgres_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = build_engine_options(postgres_uri)
    db.init_app(app)
    return app


def _reset_postgres_sequences():
    db.session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('users', 'id'),
                COALESCE((SELECT MAX(id) FROM users), 1),
                (SELECT COUNT(*) FROM users) > 0
            )
            """
        )
    )
    db.session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('tasks', 'id'),
                COALESCE((SELECT MAX(id) FROM tasks), 1),
                (SELECT COUNT(*) FROM tasks) > 0
            )
            """
        )
    )
    db.session.commit()


def _migrate(users, tasks):
    db.create_all()

    existing_user_ids = {row[0] for row in db.session.query(User.id).all()}
    existing_users_by_email = {
        row[0].lower(): row[1]
        for row in db.session.query(User.email, User.id).all()
        if row[0]
    }

    migrated_users = 0
    skipped_users = 0
    valid_user_ids = set(existing_user_ids)

    for row in users:
        user_id = int(row["id"])
        email = str(row["email"]).strip()
        email_key = email.lower()

        if email_key in existing_users_by_email:
            if existing_users_by_email[email_key] == user_id:
                valid_user_ids.add(user_id)
            else:
                print(
                    "Usuario omitido por email duplicado con otro id: "
                    f"{email} (SQLite id={user_id}, PostgreSQL id="
                    f"{existing_users_by_email[email_key]})"
                )
                skipped_users += 1
            continue

        if user_id in existing_user_ids:
            print(f"Usuario omitido por id duplicado: {user_id}")
            skipped_users += 1
            continue

        db.session.add(
            User(
                id=user_id,
                name=row["name"],
                email=email,
                password_hash=row["password_hash"],
                created_at=_parse_datetime(row["created_at"]),
            )
        )
        existing_user_ids.add(user_id)
        existing_users_by_email[email_key] = user_id
        valid_user_ids.add(user_id)
        migrated_users += 1

    db.session.commit()

    valid_user_ids = {row[0] for row in db.session.query(User.id).all()}
    existing_task_ids = {row[0] for row in db.session.query(Task.id).all()}
    migrated_tasks = 0
    skipped_tasks = 0

    for row in tasks:
        task_id = int(row["id"])
        user_id = int(row["user_id"])

        if task_id in existing_task_ids:
            skipped_tasks += 1
            continue

        if user_id not in valid_user_ids:
            print(
                f"Tarea omitida porque su user_id no existe en PostgreSQL: "
                f"task_id={task_id}, user_id={user_id}"
            )
            skipped_tasks += 1
            continue

        db.session.add(
            Task(
                id=task_id,
                title=row["title"],
                description=row["description"] or "",
                status=row["status"],
                created_at=_parse_datetime(row["created_at"]),
                user_id=user_id,
            )
        )
        existing_task_ids.add(task_id)
        migrated_tasks += 1

    db.session.commit()
    _reset_postgres_sequences()

    return migrated_users, migrated_tasks, skipped_users, skipped_tasks


def main():
    sqlite_db_path = _sqlite_path()

    try:
        postgres_uri = get_postgres_database_uri()
        users, tasks = _read_sqlite_rows(sqlite_db_path)
        app = _create_postgres_app(postgres_uri)

        with app.app_context():
            migrated_users, migrated_tasks, skipped_users, skipped_tasks = _migrate(
                users, tasks
            )

        print("Migracion completada.")
        print(f"Usuarios migrados: {migrated_users}")
        print(f"Tareas migradas: {migrated_tasks}")
        print(f"Usuarios omitidos: {skipped_users}")
        print(f"Tareas omitidas: {skipped_tasks}")
        print(f"SQLite original conservado en: {sqlite_db_path}")
    except (FileNotFoundError, RuntimeError, SQLAlchemyError, ValueError) as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        print(f"Error de migracion: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
