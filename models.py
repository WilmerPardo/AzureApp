# =============================================================
# models.py - TaskFlow SaaS
# Modelos de base de datos relacional (SQLAlchemy).
# =============================================================

from datetime import datetime
from uuid import uuid4

from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Por favor, inicia sesion para acceder a esta pagina."
login_manager.login_message_category = "warning"


TASK_STATUS_PENDING = "pendiente"
TASK_STATUS_DONE = "completada"
TASK_STATUSES = [TASK_STATUS_PENDING, TASK_STATUS_DONE]


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('Task', backref='user', lazy=True)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"<User id={self.id}>"


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    userId = db.Column(db.String(120), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default=TASK_STATUS_PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def user_id(self):
        return self.userId

    def is_completed(self):
        return self.status == TASK_STATUS_DONE

    def __repr__(self):
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"


@login_manager.user_loader
def load_user(user_id):
    from services.db_service import get_user_by_email

    return get_user_by_email(user_id)
