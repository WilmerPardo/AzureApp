# =============================================================
# app.py — TaskFlow SaaS
# Punto de entrada principal de la aplicación Flask.
# Azure ejecuta: gunicorn app:app
# =============================================================

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from config import Config
from models import db, login_manager, User, Task
from forms import RegisterForm, LoginForm, TaskForm

# ──────────────────────────────────────────────
# Inicialización de la aplicación
# ──────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones con la app
db.init_app(app)
login_manager.init_app(app)

# Crear las tablas automáticamente para que el despliegue funcione sin pasos manuales.
with app.app_context():
    db.create_all()

# ──────────────────────────────────────────────
# Rutas Públicas
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Página de inicio pública con información del servicio SaaS."""
    return render_template("index.html")


# ──────────────────────────────────────────────
# Autenticación
# ──────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Verificar que el correo no esté registrado
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash("Ya existe una cuenta con ese correo electrónico.", "danger")
            return render_template("register.html", form=form)

        # Crear el nuevo usuario con contraseña cifrada
        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(new_user)
        db.session.commit()

        flash("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión de usuarios existentes."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        # Validar credenciales
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            # Redirigir a la página que intentaba acceder (si aplica)
            next_page = request.args.get("next")
            flash(f"¡Bienvenido de vuelta, {user.name}!", "success")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Cierre de sesión del usuario."""
    logout_user()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
# Dashboard (privado)
# ──────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    """Panel principal del usuario autenticado con estadísticas."""
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completada")
    pending = total - completed

    return render_template(
        "dashboard.html",
        total=total,
        completed=completed,
        pending=pending,
        recent_tasks=tasks[-5:][::-1],  # Últimas 5 tareas
    )


# ──────────────────────────────────────────────
# CRUD de Tareas (privado)
# ──────────────────────────────────────────────

@app.route("/tasks")
@login_required
def tasks():
    """Listado completo de tareas del usuario."""
    filter_status = request.args.get("status", "all")

    query = Task.query.filter_by(user_id=current_user.id)
    if filter_status == "pendiente":
        query = query.filter_by(status="pendiente")
    elif filter_status == "completada":
        query = query.filter_by(status="completada")

    all_tasks = query.order_by(Task.created_at.desc()).all()
    return render_template("tasks.html", tasks=all_tasks, filter_status=filter_status)


@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():
    """Crear una nueva tarea."""
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else "",
            status="pendiente",
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        flash("¡Tarea creada exitosamente!", "success")
        return redirect(url_for("tasks"))

    return render_template("create_task.html", form=form)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    """Editar una tarea existente del usuario."""
    task = Task.query.get_or_404(task_id)

    # Verificar que la tarea pertenece al usuario actual
    if task.user_id != current_user.id:
        abort(403)

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data.strip()
        task.description = form.description.data.strip() if form.description.data else ""
        task.status = form.status.data
        db.session.commit()
        flash("Tarea actualizada correctamente.", "success")
        return redirect(url_for("tasks"))

    return render_template("edit_task.html", form=form, task=task)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    """Eliminar una tarea del usuario."""
    task = Task.query.get_or_404(task_id)

    # Verificar propiedad antes de eliminar
    if task.user_id != current_user.id:
        abort(403)

    db.session.delete(task)
    db.session.commit()
    flash("Tarea eliminada.", "warning")
    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/toggle", methods=["GET", "POST"])
@login_required
def toggle_task(task_id):
    """Cambiar el estado de una tarea entre pendiente y completada."""
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        abort(403)

    # Alternar estado
    task.status = "completada" if task.status == "pendiente" else "pendiente"
    db.session.commit()
    flash(f"Tarea marcada como {task.status}.", "info")
    return redirect(url_for("tasks"))


# ──────────────────────────────────────────────
# Manejo de errores
# ──────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="No tienes permiso para acceder a este recurso."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="La página que buscas no existe."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Error interno del servidor. Intenta más tarde."), 500


# ──────────────────────────────────────────────
# Contexto global para plantillas Jinja2
# ──────────────────────────────────────────────

@app.context_processor
def inject_now():
    """Inyectar el año actual en todas las plantillas."""
    return {"now": datetime.utcnow()}


# ──────────────────────────────────────────────
# Punto de entrada para desarrollo local
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
