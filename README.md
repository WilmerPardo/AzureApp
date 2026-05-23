# TaskFlow SaaS

Aplicacion web de gestion de tareas academicas y personales hecha con Flask y preparada para desplegarse en Azure App Service.

Esta version usa SQLite por defecto para simplificar el despliegue. No necesitas crear Azure Database for MySQL ni configurar una base externa para la entrega del proyecto.

## Funcionalidades

- Registro e inicio de sesion de usuarios.
- Contrasenas cifradas.
- Dashboard con estadisticas.
- Crear, editar, completar y eliminar tareas.
- Cada usuario ve solo sus propias tareas.
- Base de datos SQLite creada automaticamente al arrancar.

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.11 + Flask |
| Frontend | HTML + Bootstrap + Jinja2 |
| Base de datos | SQLite |
| ORM | SQLAlchemy |
| Autenticacion | Flask-Login |
| Produccion | Gunicorn |
| Hosting | Azure App Service Linux |

## Estructura

```text
taskflow-saas/
|-- app.py
|-- config.py
|-- models.py
|-- forms.py
|-- init_db.py
|-- requirements.txt
|-- startup.txt
|-- templates/
|-- static/
`-- instance/
```

## Base De Datos

La aplicacion usa SQLite automaticamente.

En local, si no configuras nada, se crea en:

```text
instance/taskflow.db
```

En Azure App Service, se crea en:

```text
/home/site/data/taskflow.db
```

Esa ruta esta fuera del codigo desplegado y queda en el almacenamiento persistente de App Service. Para este proyecto academico es suficiente. No es la arquitectura recomendada para una aplicacion con muchos usuarios o varias instancias, pero evita depender de MySQL para la demostracion.

## Ejecutar En Local

Crear y activar entorno virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Ejecutar:

```powershell
python app.py
```

Abrir:

```text
http://localhost:5000
```

La primera vez que arranca, Flask crea automaticamente las tablas `users` y `tasks`.

## Variables De Entorno

La app funciona sin variables obligatorias, pero en Azure debes definir una clave segura.

| Variable | Obligatoria | Descripcion |
|---|---:|---|
| `SECRET_KEY` | Si en Azure | Clave secreta para sesiones y CSRF |
| `SQLITE_DB_PATH` | No | Ruta personalizada del archivo SQLite |
| `USE_DATABASE_URL` | No | Activa una base externa si vale `true` |
| `DATABASE_URL` | No | URL de base externa; se ignora si `USE_DATABASE_URL` no esta activo |

Ejemplo para desarrollo local:

```env
SECRET_KEY=change-this-secret-key-to-something-random-and-long
SQLITE_DB_PATH=instance/taskflow.db
```

## Despliegue En Azure App Service

No crees Azure Database for MySQL. Solo necesitas una Web App.

### 1. Subir A GitHub

```powershell
git add .
git commit -m "use sqlite database for azure deployment"
git push origin main
```

### 2. Crear Web App

En Azure Portal:

```text
Create resource -> Web App
```

Valores recomendados en **Basics**:

| Campo | Valor |
|---|---|
| Subscription | Tu suscripcion |
| Resource group | `rg-taskflow-wilmer` |
| Name | `taskflow-saas-wilmer` o un nombre unico |
| Publish | `Code` |
| Runtime stack | `Python 3.11` |
| Operating System | `Linux` |
| Region | Una region permitida por tu suscripcion |
| App Service Plan | Crear nuevo |
| Plan name | `plan-taskflow` |
| Pricing plan | `Basic B1` |

Valores recomendados en **Deployment**:

| Campo | Valor |
|---|---|
| Continuous deployment | `Enable` |
| Source | `GitHub` |
| Organization | `WilmerPardo` |
| Repository | `AzureApp` |
| Branch | `main` |

### 3. Configurar La Web App

En la Web App:

```text
Settings -> Environment variables
```

Agregar:

```text
SECRET_KEY = una-clave-larga-y-segura
WEBSITES_ENABLE_APP_SERVICE_STORAGE = true
```

Opcional, si quieres fijar la ruta explicitamente:

```text
SQLITE_DB_PATH = /home/site/data/taskflow.db
```

En:

```text
Settings -> Configuration -> General settings
```

Configurar **Startup command**:

```text
gunicorn app:app --bind=0.0.0.0 --timeout 600
```

Guardar y reiniciar la Web App.

### 4. Abrir La Aplicacion

```text
https://NOMBRE-DE-TU-WEB-APP.azurewebsites.net
```

No tienes que ejecutar `python init_db.py` en Azure. La aplicacion crea las tablas automaticamente al arrancar.

## Script Opcional

Si quieres crear la base manualmente en local:

```powershell
python init_db.py
```

## Notas Importantes

- SQLite es suficiente para la entrega y pruebas del profesor.
- Mantener una sola instancia de App Service. No escales horizontalmente esta version.
- Si en el futuro necesitas muchos usuarios, cambia a MySQL, PostgreSQL o Azure SQL.
- No subas `.env` ni archivos `.db` al repositorio.
