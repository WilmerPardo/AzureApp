# TaskFlow SaaS

> **Aplicación web de gestión de tareas académicas y personales desplegada en Microsoft Azure como servicio SaaS.**

---

## 📋 Descripción de la aplicación

**TaskFlow SaaS** es una plataforma web desarrollada con **Flask (Python)** que permite a múltiples usuarios registrarse, iniciar sesión y gestionar sus tareas personales o académicas de forma segura en la nube.

La aplicación permite:
- ✅ Crear, editar, eliminar y completar tareas
- 👤 Registro e inicio de sesión con contraseña cifrada
- 📊 Dashboard con estadísticas de progreso
- 🔒 Cada usuario solo accede a sus propias tareas

---

## ☁️ ¿Por qué es un SaaS?

Esta aplicación es un **Software as a Service (SaaS)** porque:

| Característica SaaS | Implementación en TaskFlow |
|---|---|
| **Multi-usuario** | Múltiples cuentas independientes con datos aislados |
| **Acceso desde la nube** | Desplegado en Azure App Service, accesible desde cualquier navegador |
| **Sin instalación local** | El usuario solo necesita un navegador web |
| **Escalable** | Azure permite escalar verticalmente/horizontalmente |
| **Datos centralizados** | PostgreSQL en Azure gestiona todos los datos |
| **Disponibilidad 24/7** | Infraestructura administrada por Azure |

---

## 🗂️ Estructura del proyecto

```
taskflow-saas/
│
├── app.py              ← Punto de entrada principal de Flask
├── config.py           ← Configuración (lee variables de entorno)
├── models.py           ← Modelos SQLAlchemy (User, Task)
├── forms.py            ← Formularios WTForms
├── init_db.py          ← Script para inicializar la base de datos
├── requirements.txt    ← Dependencias Python
├── startup.txt         ← Comando de inicio para Azure
├── README.md           ← Esta documentación
├── .env.example        ← Plantilla de variables de entorno
├── .gitignore          ← Archivos ignorados por Git
│
├── templates/
│   ├── base.html       ← Plantilla base (navbar, footer, alerts)
│   ├── index.html      ← Página de inicio pública
│   ├── login.html      ← Formulario de inicio de sesión
│   ├── register.html   ← Formulario de registro
│   ├── dashboard.html  ← Panel de control privado
│   ├── tasks.html      ← Listado de tareas con filtros
│   ├── create_task.html← Formulario para crear tarea
│   ├── edit_task.html  ← Formulario para editar tarea
│   └── error.html      ← Página de error (403, 404, 500)
│
└── static/
    ├── css/
    │   └── styles.css  ← Estilos personalizados (tema oscuro)
    └── img/
        └── logo.svg    ← Logo de la aplicación
```

---

## 🚀 Ejecución local

### 1. Requisitos previos

- Python 3.10 o superior
- PostgreSQL instalado localmente
- Git

### 2. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/taskflow-saas.git
cd taskflow-saas
```

### 3. Crear y activar entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env con tus datos reales
```

Contenido del archivo `.env`:
```env
SECRET_KEY=mi-clave-secreta-muy-segura
DATABASE_URL=postgresql://postgres:mi_password@localhost:5432/taskflowdb
```

---

## 🗄️ Crear la base de datos PostgreSQL

### Opción A: Usando psql (línea de comandos)

```bash
# Conectarse a PostgreSQL
psql -U postgres

# Dentro de psql:
CREATE DATABASE taskflowdb;
\q
```

### Opción B: Usando pgAdmin

1. Abre pgAdmin
2. Clic derecho en "Databases" → "Create" → "Database"
3. Nombre: `taskflowdb`
4. Guardar

### Inicializar las tablas

```bash
python init_db.py
```

Salida esperada:
```
Conectando a la base de datos...
✅ Tablas creadas correctamente:
   - users
   - tasks

¡Base de datos inicializada exitosamente!
```

---

## ▶️ Ejecutar localmente

```bash
# Modo desarrollo
flask run

# O con Python directamente
python app.py
```

Abrir en el navegador: **http://localhost:5000**

Para ejecutar en modo producción localmente:

```bash
gunicorn app:app --bind=0.0.0.0:5000 --timeout 600
```

---

## ☁️ Despliegue en Azure App Service

### Paso 1 — Subir el proyecto a GitHub

```bash
git init
git add .
git commit -m "feat: TaskFlow SaaS inicial"
git remote add origin https://github.com/tu-usuario/taskflow-saas.git
git push -u origin main
```

> ⚠️ **Importante:** Asegúrate de que `.env` esté en `.gitignore`. Nunca subas claves al repositorio.

---

### Paso 2 — Crear un grupo de recursos en Azure

```bash
az group create \
  --name rg-taskflow \
  --location eastus
```

O desde el portal:
1. Ir a **Azure Portal** → Grupos de recursos
2. Clic en **Crear**
3. Nombre: `rg-taskflow`
4. Región: `East US` (o la más cercana)

---

### Paso 3 — Crear Azure Database for PostgreSQL (Flexible Server)

```bash
az postgres flexible-server create \
  --resource-group rg-taskflow \
  --name taskflow-pgserver \
  --location eastus \
  --admin-user adminuser \
  --admin-password "TuPassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access all
```

Crear la base de datos:
```bash
az postgres flexible-server db create \
  --resource-group rg-taskflow \
  --server-name taskflow-pgserver \
  --database-name taskflowdb
```

O desde el portal:
1. Busca **Azure Database for PostgreSQL**
2. Selecciona **Flexible Server**
3. Configura nombre, región, usuario y contraseña
4. En **Networking**, permite acceso desde Azure Services
5. Crea la base de datos `taskflowdb`

---

### Paso 4 — Crear Azure App Service

```bash
# Crear plan de servicio
az appservice plan create \
  --name plan-taskflow \
  --resource-group rg-taskflow \
  --sku B1 \
  --is-linux

# Crear la aplicación web
az webapp create \
  --resource-group rg-taskflow \
  --plan plan-taskflow \
  --name taskflow-saas-app \
  --runtime "PYTHON:3.11"
```

O desde el portal:
1. Busca **App Services** → Crear
2. Runtime: **Python 3.11**
3. Sistema operativo: **Linux**
4. Plan: **Basic B1** (o superior)

---

### Paso 5 — Configurar variables de entorno en Azure

```bash
az webapp config appsettings set \
  --resource-group rg-taskflow \
  --name taskflow-saas-app \
  --settings \
    SECRET_KEY="tu-clave-secreta-muy-larga-y-aleatoria" \
    DATABASE_URL="postgresql://adminuser:TuPassword123!@taskflow-pgserver.postgres.database.azure.com:5432/taskflowdb?sslmode=require"
```

O desde el portal:
1. App Service → **Configuración** → **Configuración de la aplicación**
2. Agregar:
   - `SECRET_KEY` = (clave aleatoria segura)
   - `DATABASE_URL` = (cadena de conexión PostgreSQL con `?sslmode=require`)

---

### Paso 6 — Configurar el comando de inicio

```bash
az webapp config set \
  --resource-group rg-taskflow \
  --name taskflow-saas-app \
  --startup-file "gunicorn app:app --bind=0.0.0.0 --timeout 600"
```

O desde el portal:
1. App Service → **Configuración** → **Configuración general**
2. **Comando de inicio**: `gunicorn app:app --bind=0.0.0.0 --timeout 600`

---

### Paso 7 — Activar despliegue desde GitHub

1. App Service → **Centro de implementación**
2. Fuente: **GitHub**
3. Autorizar con tu cuenta de GitHub
4. Seleccionar repositorio y rama `main`
5. Guardar → Azure crea un workflow de CI/CD automáticamente

---

### Paso 8 — Inicializar la base de datos en Azure

Una vez desplegada la aplicación, inicializa las tablas:

**Opción A: SSH en Azure**
1. App Service → **SSH** → **Ir**
2. En la terminal:
```bash
cd /home/site/wwwroot
python init_db.py
```

**Opción B: Kudu Console**
1. `https://taskflow-saas-app.scm.azurewebsites.net/DebugConsole`
2. Navegar a `/home/site/wwwroot`
3. Ejecutar: `python init_db.py`

---

### Paso 9 — Abrir la aplicación

```
https://taskflow-saas-app.azurewebsites.net
```

---

## ✅ Checklist final de verificación

### Local
- [ ] `pip install -r requirements.txt` ejecuta sin errores
- [ ] `python init_db.py` crea las tablas exitosamente
- [ ] `flask run` inicia la aplicación en puerto 5000
- [ ] Se puede registrar un usuario nuevo
- [ ] El login funciona correctamente
- [ ] Se pueden crear, editar y eliminar tareas
- [ ] El logout cierra la sesión
- [ ] Un usuario no puede ver las tareas de otro

### Azure
- [ ] El repositorio está en GitHub (sin `.env`)
- [ ] Azure Database for PostgreSQL está creado y accesible
- [ ] El App Service tiene Python 3.11 en Linux
- [ ] `SECRET_KEY` configurada en App Settings
- [ ] `DATABASE_URL` configurada con `sslmode=require`
- [ ] Startup command configurado correctamente
- [ ] El deployment desde GitHub está activo
- [ ] `python init_db.py` ejecutado correctamente en Azure
- [ ] La URL pública (`https://xxx.azurewebsites.net`) carga la app
- [ ] Registro, login y CRUD de tareas funcionan en producción

---

## 🔧 Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Flask (sesiones y CSRF) | `super-secret-random-key-123` |
| `DATABASE_URL` | Cadena de conexión PostgreSQL | `postgresql://user:pass@host:5432/db?sslmode=require` |

---

## 🛠️ Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11 + Flask 3.0 |
| Frontend | HTML5 + Bootstrap 5 + Jinja2 |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy |
| Autenticación | Flask-Login + Werkzeug |
| Formularios | Flask-WTF + WTForms |
| Servidor producción | Gunicorn |
| Hosting | Azure App Service (Linux) |
| Base de datos cloud | Azure Database for PostgreSQL |

---

## 📄 Licencia

Proyecto académico de demostración. Uso libre con fines educativos.
