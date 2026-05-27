# TaskFlow SaaS

Aplicacion web de gestion de tareas academicas y personales hecha con Flask, Jinja2, Bootstrap, Flask-Login y SQLAlchemy. La aplicacion mantiene SQLite para desarrollo local y queda preparada para usar Azure Database for PostgreSQL Flexible Server en produccion.

## Funcionalidades

- Registro e inicio de sesion de usuarios.
- Contrasenas cifradas.
- Dashboard con estadisticas.
- Crear, editar, completar y eliminar tareas.
- Cada usuario ve solo sus propias tareas.
- Soporte para SQLite local y PostgreSQL externo.

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.11 + Flask |
| Frontend | HTML + Bootstrap + Jinja2 |
| Base de datos local | SQLite |
| Base de datos produccion | Azure Database for PostgreSQL Flexible Server |
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
|-- scripts/
|   `-- migrate_sqlite_to_postgres.py
|-- templates/
|-- static/
`-- instance/
```

## Configuracion de base de datos

La aplicacion decide la conexion en este orden:

1. `DATABASE_URL`, si existe.
2. Variables de Azure App Service: `AZURE_POSTGRESQL_USER`, `AZURE_POSTGRESQL_PASSWORD`, `AZURE_POSTGRESQL_HOST`, `AZURE_POSTGRESQL_NAME`.
3. SQLite como fallback local.

Las URLs `postgres://` y `postgresql://` se normalizan automaticamente a `postgresql+psycopg2://` para SQLAlchemy. Si el host termina en `.postgres.database.azure.com`, se agrega `sslmode=require` cuando no venga definido.

SQLite local por defecto:

```text
instance/taskflow.db
```

SQLite en Azure App Service, solo si no configuras PostgreSQL:

```text
/home/site/data/taskflow.db
```

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

Crear `.env` local si quieres fijar SQLite:

```env
SECRET_KEY=una-clave-segura
SQLITE_DB_PATH=instance/taskflow.db
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

## Variables de entorno

Desarrollo local con SQLite:

```env
SECRET_KEY=una-clave-segura
SQLITE_DB_PATH=instance/taskflow.db
```

Produccion con PostgreSQL usando `DATABASE_URL`:

```env
SECRET_KEY=una-clave-segura
DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/nombre_db?sslmode=require
```

Produccion con variables de Azure App Service:

```env
SECRET_KEY=una-clave-segura
AZURE_POSTGRESQL_USER=usuario
AZURE_POSTGRESQL_PASSWORD=password
AZURE_POSTGRESQL_HOST=servidor.postgres.database.azure.com
AZURE_POSTGRESQL_NAME=nombre_db
```

Si `DATABASE_URL` existe, tiene prioridad sobre las variables `AZURE_POSTGRESQL_*`.

## Despliegue en Azure App Service con PostgreSQL

1. Crear un recurso **Azure Database for PostgreSQL Flexible Server**.
2. Crear la base de datos de la aplicacion, por ejemplo `taskflowdb`.
3. Configurar red/firewall para permitir la conexion desde Azure App Service, o usar **Service Connector**.
4. En la Web App, abrir `Settings -> Environment variables`.
5. Agregar `SECRET_KEY` y una de estas opciones:

```text
DATABASE_URL = postgresql+psycopg2://usuario:password@servidor.postgres.database.azure.com:5432/taskflowdb?sslmode=require
```

O:

```text
AZURE_POSTGRESQL_USER = usuario
AZURE_POSTGRESQL_PASSWORD = password
AZURE_POSTGRESQL_HOST = servidor.postgres.database.azure.com
AZURE_POSTGRESQL_NAME = taskflowdb
```

6. En `Settings -> Configuration -> General settings`, configurar **Startup command**:

```text
gunicorn app:app --bind=0.0.0.0 --timeout 600
```

7. Guardar cambios y reiniciar la Web App.
8. Si ya habia datos en SQLite, ejecutar la migracion.
9. Revisar logs en App Service si hay errores de conexion o credenciales.

La aplicacion crea las tablas faltantes al arrancar. Para cambios de esquema futuros se recomienda agregar migraciones formales con Flask-Migrate/Alembic.

## Migracion SQLite a PostgreSQL

El script `scripts/migrate_sqlite_to_postgres.py`:

- Lee SQLite desde `SQLITE_DB_PATH` o `instance/taskflow.db`.
- Lee PostgreSQL desde `DATABASE_URL` o `AZURE_POSTGRESQL_*`.
- Crea tablas en PostgreSQL si no existen.
- Migra primero `users` y luego `tasks`.
- Conserva `id`, `name`, `email`, `password_hash`, `created_at`, `title`, `description`, `status` y `user_id`.
- Evita duplicar usuarios por `email`.
- No borra ni modifica el archivo SQLite original.

Ejemplo local:

```powershell
$env:SQLITE_DB_PATH = "instance/taskflow.db"
$env:DATABASE_URL = "postgresql+psycopg2://usuario:password@host:5432/nombre_db?sslmode=require"
python scripts/migrate_sqlite_to_postgres.py
```

Ejemplo desde consola SSH/Kudu de Azure App Service:

```bash
cd /home/site/wwwroot
export SQLITE_DB_PATH=/home/site/data/taskflow.db
export DATABASE_URL='postgresql+psycopg2://usuario:password@servidor.postgres.database.azure.com:5432/taskflowdb?sslmode=require'
python scripts/migrate_sqlite_to_postgres.py
```

## Backup y migracion de base de datos

### Backup de SQLite local

Crear una carpeta de respaldos y copiar el archivo:

```powershell
mkdir backups
copy instance\taskflow.db backups\taskflow-sqlite-backup.db
```

### Backup de SQLite en Azure App Service

El archivo anterior de SQLite puede estar en:

```text
/home/site/data/taskflow.db
```

Desde SSH/Kudu puedes copiarlo dentro del almacenamiento persistente:

```bash
mkdir -p /home/site/data/backups
cp /home/site/data/taskflow.db /home/site/data/backups/taskflow-sqlite-backup.db
```

Luego descargalo desde Kudu/Advanced Tools o por el metodo de transferencia permitido en tu entorno.

### Backup manual de PostgreSQL con pg_dump

`pg_dump` usa URLs PostgreSQL/libpq, no URLs SQLAlchemy. Si tu `DATABASE_URL` contiene `postgresql+psycopg2://`, quita `+psycopg2` para el comando.

Formato URL:

```bash
mkdir -p backups
pg_dump "postgresql://usuario:password@servidor.postgres.database.azure.com:5432/taskflowdb?sslmode=require" -Fc -f backups/taskflow-postgres.dump
```

Formato libpq:

```bash
pg_dump "host=servidor.postgres.database.azure.com port=5432 dbname=taskflowdb user=usuario sslmode=require" -Fc -f backups/taskflow-postgres.dump
```

Azure Database for PostgreSQL Flexible Server tambien incluye backups automaticos y restauracion a un punto en el tiempo. El backup manual con `pg_dump` sirve como respaldo adicional o para entregar evidencia academica.

## Seguridad

- No subir `.env`.
- No subir archivos `.db`.
- No subir contrasenas ni cadenas reales de conexion.
- Guardar respaldos fuera del repositorio o en `backups/`, que esta ignorado por Git.
- Definir `SECRET_KEY` con un valor largo y aleatorio en Azure.

## Script opcional de inicializacion

Para crear/verificar tablas manualmente en la base configurada:

```powershell
python init_db.py
```
