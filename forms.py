# =============================================================
# forms.py — TaskFlow SaaS
# Formularios WTForms con validaciones para la aplicación.
# =============================================================

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


# ──────────────────────────────────────────────
# Formulario: Registro de usuario
# ──────────────────────────────────────────────

class RegisterForm(FlaskForm):
    """Formulario para crear una nueva cuenta de usuario."""

    name = StringField(
        "Nombre completo",
        validators=[
            DataRequired(message="El nombre es obligatorio."),
            Length(min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres."),
        ],
    )

    email = StringField(
        "Correo electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            Email(message="Introduce un correo electrónico válido."),
            Length(max=150),
        ],
    )

    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Length(min=6, message="La contraseña debe tener al menos 6 caracteres."),
        ],
    )

    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(message="Por favor confirma tu contraseña."),
            EqualTo("password", message="Las contraseñas no coinciden."),
        ],
    )

    submit = SubmitField("Crear cuenta")


# ──────────────────────────────────────────────
# Formulario: Inicio de sesión
# ──────────────────────────────────────────────

class LoginForm(FlaskForm):
    """Formulario para iniciar sesión en la plataforma."""

    email = StringField(
        "Correo electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio."),
            Email(message="Introduce un correo electrónico válido."),
        ],
    )

    password = PasswordField(
        "Contraseña",
        validators=[DataRequired(message="La contraseña es obligatoria.")],
    )

    remember = BooleanField("Recordar sesión")

    submit = SubmitField("Iniciar sesión")


# ──────────────────────────────────────────────
# Formulario: Crear / Editar Tarea
# ──────────────────────────────────────────────

class TaskForm(FlaskForm):
    """Formulario reutilizable para crear y editar tareas."""

    title = StringField(
        "Título de la tarea",
        validators=[
            DataRequired(message="El título es obligatorio."),
            Length(min=2, max=200, message="El título debe tener entre 2 y 200 caracteres."),
        ],
    )

    description = TextAreaField(
        "Descripción (opcional)",
        validators=[Optional(), Length(max=1000)],
    )

    # El campo status solo se muestra al editar; al crear siempre es 'pendiente'
    status = SelectField(
        "Estado",
        choices=[("pendiente", "Pendiente"), ("completada", "Completada")],
        default="pendiente",
    )

    submit = SubmitField("Guardar tarea")
