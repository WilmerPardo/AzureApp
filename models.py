# =============================================================
# models.py — TaskFlow SaaS
# Definición de modelos de base de datos con SQLAlchemy.
# =============================================================

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

# ── Inicialización de extensiones (sin app, se vinculan en app.py) ──
db = SQLAlchemy()
login_manager = LoginManager()

# Ruta a la que Flask-Login redirige si el usuario no está autenticado
login_manager.login_view = "login"
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "warning"


# ──────────────────────────────────────────────
# Cargador de usuario para Flask-Login
# ──────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario desde la base de datos a partir de su ID de sesión."""
    return User.query.get(int(user_id))


# ──────────────────────────────────────────────
# Modelo: User (usuarios del sistema)
# ──────────────────────────────────────────────

class User(UserMixin, db.Model):
    """
    Tabla de usuarios registrados en la plataforma.
    UserMixin provee métodos requeridos por Flask-Login:
      is_authenticated, is_active, is_anonymous, get_id
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relación: un usuario tiene muchas tareas
    tasks = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ──────────────────────────────────────────────
# Modelo: Task (tareas de los usuarios)
# ──────────────────────────────────────────────

# Estados válidos para una tarea
TASK_STATUS_PENDING = "pendiente"
TASK_STATUS_DONE = "completada"
TASK_STATUSES = [TASK_STATUS_PENDING, TASK_STATUS_DONE]


class Task(db.Model):
    """
    Tabla de tareas. Cada tarea pertenece a un único usuario (user_id).
    El estado puede ser 'pendiente' o 'completada'.
    """
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True, default="")
    status = db.Column(
        db.String(20),
        nullable=False,
        default=TASK_STATUS_PENDING,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Clave foránea hacia la tabla users
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def is_completed(self):
        """Retorna True si la tarea está completada."""
        return self.status == TASK_STATUS_DONE

    def __repr__(self):
        return f"<Task id={self.id} title='{self.title}' status={self.status}>"
