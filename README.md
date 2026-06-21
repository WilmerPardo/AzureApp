# TaskFlow SaaS

Aplicación web de gestión de tareas académicas y personales hecha con Flask, Jinja2, Bootstrap, Flask-Login y Azure Cosmos DB for NoSQL.

## Funcionalidades

- Registro e inicio de sesión de usuarios.
- Contraseñas cifradas con Werkzeug.
- Dashboard con estadísticas.
- Crear, editar, completar y eliminar tareas.
- Cada usuario ve solo sus propias tareas.
- Persistencia en documentos JSON usando Azure Cosmos DB for NoSQL.

## Stack

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11 + Flask |
| Frontend | HTML + Bootstrap + Jinja2 |
| Base de datos | Azure Cosmos DB for NoSQL |
| SDK de datos | azure-cosmos |
| Autenticación | Flask-Login |
| Producción | Gunicorn |
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
|-- services/
|   |-- __init__.py
|   `-- cosmos_service.py
|-- scripts/
|   |-- init_cosmos.py
|   |-- migrate_sqlite_to_cosmos.py
|   `-- export_cosmos_to_json.py
|-- templates/
|-- static/
`-- instance/
```

## Modelo de datos NoSQL

La aplicación usa dos contenedores en Azure Cosmos DB for NoSQL.

Contenedor `users`, partition key `/id`:

```json
{
  "id": "correo@ejemplo.com",
  "type": "user",
  "name": "Nombre del usuario",
  "email": "correo@ejemplo.com",
  "password_hash": "hash_de_password",
  "created_at": "fecha_iso"
}
```

Contenedor `tasks`, partition key `/userId`:

```json
{
  "id": "uuid-generado",
  "type": "task",
  "userId": "correo@ejemplo.com",
  "title": "Título",
  "description": "Descripción",
  "status": "pendiente",
  "created_at": "fecha_iso"
}
```

El email se normaliza en minúsculas y se usa como `id` del usuario. Las tareas se consultan por `userId` para evitar consultas cross-partition en el flujo normal de la aplicación.

## Ejecutar en local

Crear y activar entorno virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Crear `.env` local:

```env
SECRET_KEY=una_clave_larga_y_segura
COSMOS_ENDPOINT=https://NOMBRE.documents.azure.com:443/
COSMOS_KEY=CLAVE_DE_COSMOS
COSMOS_DATABASE_NAME=taskflowdb
COSMOS_USERS_CONTAINER=users
COSMOS_TASKS_CONTAINER=tasks
```

Inicializar base y contenedores:

```powershell
python scripts/init_cosmos.py
```

Ejecutar la aplicación:

```powershell
python app.py
```

Abrir:

```text
http://localhost:5000
```

## Variables de entorno para Azure App Service

En Azure App Service se deben configurar estas variables:

```env
SECRET_KEY=una_clave_larga_y_segura
COSMOS_ENDPOINT=https://NOMBRE.documents.azure.com:443/
COSMOS_KEY=CLAVE_DE_COSMOS
COSMOS_DATABASE_NAME=taskflowdb
COSMOS_USERS_CONTAINER=users
COSMOS_TASKS_CONTAINER=tasks
```

Ruta en Azure:

```text
Azure App Service
Settings
Environment variables
```

Después de guardar las variables, reinicia el App Service.

El comando de inicio recomendado es:

```text
gunicorn app:app --bind=0.0.0.0 --timeout 600
```

## Pasos en Azure Portal

1. Crear recurso en Azure.
2. Buscar Azure Cosmos DB.
3. Seleccionar Azure Cosmos DB for NoSQL.
4. Crear la cuenta.
5. Elegir modo serverless si está disponible para reducir costos académicos.
6. Crear una base llamada `taskflowdb`.
7. Crear contenedor `users` con partition key `/id`.
8. Crear contenedor `tasks` con partition key `/userId`.
9. Copiar URI/Endpoint y Primary Key.
10. Pegar esas credenciales como variables de entorno en Azure App Service.
11. Reiniciar App Service.
12. Probar registro, login y CRUD de tareas.

## Inicialización de Cosmos DB

El script `scripts/init_cosmos.py` lee:

- `COSMOS_ENDPOINT`
- `COSMOS_KEY`
- `COSMOS_DATABASE_NAME`
- `COSMOS_USERS_CONTAINER`
- `COSMOS_TASKS_CONTAINER`

Ejecutar:

```powershell
python scripts/init_cosmos.py
```

El script crea la base de datos si no existe y crea los contenedores con estas partition keys:

- `users`: `/id`
- `tasks`: `/userId`

También se puede ejecutar:

```powershell
python init_db.py
```

## Migración SQLite a Cosmos DB

El script `scripts/migrate_sqlite_to_cosmos.py`:

- Lee SQLite desde `SQLITE_DB_PATH` o `instance/taskflow.db`.
- Conecta con Azure Cosmos DB usando variables `COSMOS_*`.
- Migra usuarios al contenedor `users`.
- Usa el email en minúsculas como `id` del usuario.
- Migra tareas al contenedor `tasks`.
- Convierte el `user_id` numérico anterior al email del usuario.
- Usa `upsert_item` para evitar duplicados.
- No borra ni modifica el archivo SQLite original.

Ejemplo local:

```powershell
$env:SQLITE_DB_PATH = "instance/taskflow.db"
$env:COSMOS_ENDPOINT = "https://NOMBRE.documents.azure.com:443/"
$env:COSMOS_KEY = "CLAVE_DE_COSMOS"
$env:COSMOS_DATABASE_NAME = "taskflowdb"
$env:COSMOS_USERS_CONTAINER = "users"
$env:COSMOS_TASKS_CONTAINER = "tasks"
python scripts/migrate_sqlite_to_cosmos.py
```

Ejemplo desde consola SSH/Kudu de Azure App Service:

```bash
cd /home/site/wwwroot
export SQLITE_DB_PATH=/home/site/data/taskflow.db
export COSMOS_ENDPOINT='https://NOMBRE.documents.azure.com:443/'
export COSMOS_KEY='CLAVE_DE_COSMOS'
export COSMOS_DATABASE_NAME='taskflowdb'
export COSMOS_USERS_CONTAINER='users'
export COSMOS_TASKS_CONTAINER='tasks'
python scripts/migrate_sqlite_to_cosmos.py
```

## Backup y migración de base de datos

Antes la aplicación usaba SQLite como archivo local dentro del entorno de la aplicación. Ahora se usa Azure Cosmos DB for NoSQL como base de datos separada de Azure App Service.

Azure Cosmos DB realiza backups automáticos. La cuenta puede configurarse con backup periódico o backup continuo con restauración a punto en el tiempo, según la opción elegida en Azure.

Para un respaldo manual académico, se puede exportar la información a JSON:

```powershell
python scripts/export_cosmos_to_json.py
```

El script crea:

```text
backups/users_backup.json
backups/tasks_backup.json
```

La carpeta `backups/` está ignorada por Git para evitar subir datos sensibles.

## Verificar documentos en Azure Portal

1. Abrir la cuenta de Azure Cosmos DB.
2. Entrar a Data Explorer.
3. Abrir la base `taskflowdb`.
4. Abrir el contenedor `users`.
5. Revisar que los documentos tengan `id`, `type`, `email`, `name`, `password_hash` y `created_at`.
6. Abrir el contenedor `tasks`.
7. Revisar que los documentos tengan `id`, `type`, `userId`, `title`, `description`, `status` y `created_at`.
8. Confirmar que el `userId` de cada tarea coincide con el `id` del usuario.

## Seguridad

- No subir `.env`.
- No subir archivos `.db`.
- No subir respaldos reales con datos sensibles.
- No subir claves reales de Cosmos DB.
- Mantener `backups/` fuera de Git.
- Definir `SECRET_KEY` con un valor largo y aleatorio en Azure.
- Rotar `COSMOS_KEY` si se expone accidentalmente.

`.gitignore` debe incluir:

```gitignore
.env
*.db
instance/
backups/
__pycache__/
venv/
.venv/
```

## Justificación técnica

La aplicación fue modificada para separar la capa de datos del servidor web. Anteriormente usaba SQLite, una base de datos basada en archivo, almacenada dentro del entorno de la aplicación. Ahora se utiliza Azure Cosmos DB for NoSQL, una base de datos administrada en la nube que almacena la información como documentos JSON en contenedores independientes. Esta arquitectura permite separar código y datos, mejorar la escalabilidad, facilitar respaldos automáticos y permitir restauración mediante las opciones de backup de Azure Cosmos DB.
