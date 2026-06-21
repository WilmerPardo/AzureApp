# =============================================================
# services/db_service.py - TaskFlow SaaS
# Capa de acceso a datos usando SQLAlchemy (SQLite local).
# =============================================================

from models import db, User, Task, TASK_STATUS_PENDING, TASK_STATUS_DONE, TASK_STATUSES
from sqlalchemy.exc import IntegrityError

def normalize_email(email):
    return (email or "").strip().lower()

def get_user_by_email(email):
    email_norm = normalize_email(email)
    if not email_norm:
        return None
    return User.query.filter_by(email=email_norm).first()

def user_exists(email):
    return get_user_by_email(email) is not None

def create_user(name, email, password_hash):
    email_norm = normalize_email(email)
    if not email_norm:
        raise ValueError("El email del usuario es obligatorio.")
    
    user = User(
        id=email_norm,
        name=(name or "").strip(),
        email=email_norm,
        password_hash=password_hash
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Ya existe un usuario con ese email.")

def get_tasks_by_user(user_id, status=None):
    owner_id = normalize_email(user_id)
    if not owner_id:
        return []

    query = Task.query.filter_by(userId=owner_id)
    
    if status in TASK_STATUSES:
        query = query.filter_by(status=status)
        
    return query.order_by(Task.created_at.desc()).all()

def get_recent_tasks_by_user(user_id, limit=5):
    owner_id = normalize_email(user_id)
    if not owner_id:
        return []

    safe_limit = max(1, min(int(limit), 100))
    return Task.query.filter_by(userId=owner_id).order_by(Task.created_at.desc()).limit(safe_limit).all()

def create_task(user_id, title, description):
    owner_id = normalize_email(user_id)
    if not owner_id:
        raise ValueError("El usuario de la tarea es obligatorio.")
        
    task = Task(
        userId=owner_id,
        title=(title or "").strip(),
        description=(description or "").strip(),
        status=TASK_STATUS_PENDING
    )
    
    db.session.add(task)
    db.session.commit()
    return task

def get_task_by_id(user_id, task_id):
    owner_id = normalize_email(user_id)
    if not owner_id or not task_id:
        return None

    return Task.query.filter_by(id=str(task_id), userId=owner_id).first()

def update_task(user_id, task_id, title, description, status):
    if status not in TASK_STATUSES:
        raise ValueError("Estado de tarea no valido.")

    task = get_task_by_id(user_id, task_id)
    if task is None:
        return None

    task.title = (title or "").strip()
    task.description = (description or "").strip()
    task.status = status

    db.session.commit()
    return task

def delete_task(user_id, task_id):
    task = get_task_by_id(user_id, task_id)
    if task is None:
        return False

    db.session.delete(task)
    db.session.commit()
    return True

def toggle_task_status(user_id, task_id):
    task = get_task_by_id(user_id, task_id)
    if task is None:
        return None

    next_status = (
        TASK_STATUS_DONE if task.status == TASK_STATUS_PENDING else TASK_STATUS_PENDING
    )
    return update_task(
        user_id=user_id,
        task_id=task_id,
        title=task.title,
        description=task.description,
        status=next_status,
    )
