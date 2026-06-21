# =============================================================
# app.py - TaskFlow SaaS
# Punto de entrada principal de la aplicacion Flask.
# Azure ejecuta: gunicorn app:app
# =============================================================

import atexit
import os
from datetime import datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from posthog import Posthog, identify_context, tag
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from forms import LoginForm, RegisterForm, TaskForm
from models import TASK_STATUSES, login_manager, db
from services.db_service import (
    create_task as cosmos_create_task,
    create_user,
    delete_task as cosmos_delete_task,
    get_recent_tasks_by_user,
    get_task_by_id,
    get_tasks_by_user,
    get_user_by_email,
    normalize_email,
    toggle_task_status,
    update_task,
    user_exists,
)


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager.init_app(app)

posthog_client = Posthog(
    project_api_key=os.environ.get("POSTHOG_API_KEY", ""),
    host=os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com"),
    enable_exception_autocapture=True,
)
atexit.register(posthog_client.shutdown)


@app.route("/")
def index():
    """Pagina de inicio publica con informacion del servicio SaaS."""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = normalize_email(form.email.data)

        try:
            if user_exists(email):
                flash("Ya existe una cuenta con ese correo electronico.", "danger")
                return render_template("register.html", form=form)

            create_user(
                name=form.name.data,
                email=email,
                password_hash=generate_password_hash(form.password.data),
            )
            with posthog_client.new_context():
                identify_context(email)
                tag("name", form.name.data)
                posthog_client.capture("user_signed_up", properties={"signup_method": "form"})
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("register.html", form=form)
        except RuntimeError:
            app.logger.exception("Error al crear usuario en Cosmos DB")
            flash(
                "No se pudo crear la cuenta. Verifica la conexion con Cosmos DB.",
                "danger",
            )
            return render_template("register.html", form=form)

        flash("Cuenta creada exitosamente. Ahora puedes iniciar sesion.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesion de usuarios existentes."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = get_user_by_email(form.email.data)
        except RuntimeError:
            app.logger.exception("Error al leer usuario desde Cosmos DB")
            flash(
                "No se pudo validar el inicio de sesion. Verifica Cosmos DB.",
                "danger",
            )
            return render_template("login.html", form=form)

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            with posthog_client.new_context():
                identify_context(user.id)
                tag("name", user.name)
                posthog_client.capture("user_logged_in", properties={"login_method": "password"})
            next_page = request.args.get("next")
            flash(f"Bienvenido de vuelta, {user.name}.", "success")
            return redirect(next_page or url_for("dashboard"))

        flash("Correo o contrasena incorrectos.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Cierre de sesion del usuario."""
    with posthog_client.new_context():
        identify_context(current_user.id)
        posthog_client.capture("user_logged_out")
    logout_user()
    flash("Has cerrado sesion correctamente.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Panel principal del usuario autenticado con estadisticas."""
    all_tasks = get_tasks_by_user(current_user.id)
    total = len(all_tasks)
    completed = sum(1 for task in all_tasks if task.is_completed())
    pending = total - completed
    recent_tasks = get_recent_tasks_by_user(current_user.id, limit=5)

    with posthog_client.new_context():
        identify_context(current_user.id)
        posthog_client.capture(
            "dashboard_viewed",
            properties={"total_tasks": total, "completed_tasks": completed, "pending_tasks": pending},
        )

    return render_template(
        "dashboard.html",
        total=total,
        completed=completed,
        pending=pending,
        recent_tasks=recent_tasks,
    )


@app.route("/tasks")
@login_required
def tasks():
    """Listado completo de tareas del usuario."""
    filter_status = request.args.get("status", "all")
    if filter_status not in ["all", *TASK_STATUSES]:
        filter_status = "all"

    status_filter = filter_status if filter_status in TASK_STATUSES else None

    all_tasks = get_tasks_by_user(current_user.id, status=status_filter)
    return render_template("tasks.html", tasks=all_tasks, filter_status=filter_status)


@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():
    """Crear una nueva tarea."""
    form = TaskForm()
    if form.validate_on_submit():
        try:
            cosmos_create_task(
                user_id=current_user.id,
                title=form.title.data,
                description=form.description.data or "",
            )
            with posthog_client.new_context():
                identify_context(current_user.id)
                posthog_client.capture(
                    "task_created",
                    properties={"has_description": bool(form.description.data)},
                )
        except (RuntimeError, ValueError):
            app.logger.exception("Error al crear tarea en Cosmos DB")
            flash("No se pudo crear la tarea. Intenta nuevamente.", "danger")
            return render_template("create_task.html", form=form)

        flash("Tarea creada exitosamente.", "success")
        return redirect(url_for("tasks"))

    return render_template("create_task.html", form=form)


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    """Editar una tarea existente del usuario."""
    task = get_task_by_id(current_user.id, task_id)
    if task is None:
        abort(404)

    if task.userId != current_user.id:
        abort(403)

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        try:
            task = update_task(
                user_id=current_user.id,
                task_id=task_id,
                title=form.title.data,
                description=form.description.data or "",
                status=form.status.data,
            )
        except (RuntimeError, ValueError):
            app.logger.exception("Error al actualizar tarea en Cosmos DB")
            flash("No se pudo actualizar la tarea. Intenta nuevamente.", "danger")
            return render_template("edit_task.html", form=form, task=task)

        if task is None:
            abort(404)

        with posthog_client.new_context():
            identify_context(current_user.id)
            posthog_client.capture(
                "task_updated",
                properties={"new_status": form.status.data},
            )
        flash("Tarea actualizada correctamente.", "success")
        return redirect(url_for("tasks"))

    return render_template("edit_task.html", form=form, task=task)


@app.route("/tasks/<task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    """Eliminar una tarea del usuario."""
    task = get_task_by_id(current_user.id, task_id)
    if task is None:
        abort(404)

    if task.userId != current_user.id:
        abort(403)

    if not cosmos_delete_task(current_user.id, task_id):
        abort(404)

    with posthog_client.new_context():
        identify_context(current_user.id)
        posthog_client.capture("task_deleted")
    flash("Tarea eliminada.", "warning")
    return redirect(url_for("tasks"))


@app.route("/tasks/<task_id>/toggle", methods=["GET", "POST"])
@login_required
def toggle_task(task_id):
    """Cambiar el estado de una tarea entre pendiente y completada."""
    task = get_task_by_id(current_user.id, task_id)
    if task is None:
        abort(404)

    if task.userId != current_user.id:
        abort(403)

    updated_task = toggle_task_status(current_user.id, task_id)
    if updated_task is None:
        abort(404)

    with posthog_client.new_context():
        identify_context(current_user.id)
        posthog_client.capture(
            "task_status_toggled",
            properties={"new_status": updated_task.status},
        )
    flash(f"Tarea marcada como {updated_task.status}.", "info")
    return redirect(url_for("tasks"))


@app.errorhandler(403)
def forbidden(e):
    return (
        render_template(
            "error.html",
            code=403,
            message="No tienes permiso para acceder a este recurso.",
        ),
        403,
    )


@app.errorhandler(404)
def not_found(e):
    return (
        render_template(
            "error.html", code=404, message="La pagina que buscas no existe."
        ),
        404,
    )


@app.errorhandler(500)
def server_error(e):
    posthog_client.capture_exception(e)
    return (
        render_template(
            "error.html",
            code=500,
            message="Error interno del servidor. Intenta mas tarde.",
        ),
        500,
    )


@app.context_processor
def inject_now():
    """Inyectar el ano actual en todas las plantillas."""
    return {"now": datetime.utcnow()}


if __name__ == "__main__":
    app.run(debug=True)
