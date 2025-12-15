# 🎯 EventSoft  
**Sistema Web de Gestión Automatizada de Eventos**

---

## 📌 Descripción del Proyecto

**EventSoft** es una aplicación web desarrollada con **Django**, orientada a la gestión integral y automatizada de eventos académicos, culturales y empresariales.

El sistema surge como respuesta a una necesidad real presentada por instructoras (clientes), quienes requerían una plataforma centralizada, eficiente y segura para administrar eventos con múltiples roles y procesos de evaluación.

La aplicación permite registrar eventos, gestionar participantes, evaluadores y criterios de evaluación, realizar procesos de calificación con cálculos automáticos, generar reportes y visualizar estadísticas mediante dashboards personalizados.

---

## 👥 Roles del Sistema

### 🔹 Exponentes / Participantes
- Realizan preinscripción a eventos.
- Cargan documentación requerida.
- Consultan el estado de su inscripción y evaluación.

### 🔹 Evaluadores
- Califican participantes según criterios definidos.
- Modifican su información personal.
- Descargan reportes en PDF.

### 🔹 Administradores
- Gestionan eventos.
- Administran participantes, evaluadores y asignaciones.
- Configuran criterios de evaluación y categorías.

### 🔹 Super Administradores
- Control total del sistema.
- Gestión completa de todas las aplicaciones y módulos.

---

## ⚙️ Funcionalidades Principales

- Registro y administración completa de eventos.
- Inscripción automática de participantes con carga de documentos.
- Gestión de criterios de evaluación por evento.
- Asignación de evaluadores y control de accesos.
- Proceso de evaluación con cálculos automáticos y ranking.
- Generación de reportes en PDF.
- Dashboard con estadísticas personalizadas por rol.
- Control de inscripciones habilitadas o deshabilitadas.
- Gestión de archivos estáticos y multimedia.

---

## 🌐 Enlace del Despliegue

La aplicación se encuentra desplegada en **PythonAnywhere**:

🔗 https://sebastian1010101010.pythonanywhere.com/

No es necesario realizar ninguna instalación para usar la aplicación en línea.

---

## 🧭 Uso de la Aplicación en Línea

1. Ingresar al enlace del despliegue.
2. Seleccionar el rol correspondiente (Participante, Evaluador, Administrador).
3. Acceder con las credenciales asignadas.
4. Acceder al panel correspondiente según el rol.
5. Ejecutar las funcionalidades permitidas por el sistema.

---

## 💻 Instalación y Ejecución Local

### 🔹 Requisitos Previos
- Python 3.10 o superior
- Git
- MySQL
- Pip
- Virtualenv / venv

---

### 🔹 Clonar el Proyecto

```bash
git init
git clone https://github.com/alejandro-quiceno96/EventSoft.git
cd EventSoft
git checkout master
```

### 🔹Crear y Activar Entorno Virtual

```bash
python -m venv venv
venv\Scripts\activate
```
### Configuración de Variables de Entorno

Crear un archivo .env en la raiz del proyecto y copiar y pegar lo siguiente: 
```bash
# Django
SECRET_KEY=django-insecure-xxxx
DEBUG=True

# Base de Datos
DB_NAME=eventsoft
DB_USER=usuario_db
DB_PASSWORD=contraseña_db
DB_HOST=localhost
DB_PORT=3306

# Correo
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=correo@gmail.com
EMAIL_HOST_PASSWORD=clave_correo
DEFAULT_FROM_EMAIL=eventsoft3@gmail.com
```
### Instalar Dependencias 
```bash
pip install -r requirements.txt
```
### Migraciones y creación 
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
````

### Ejecutar Aplicación 
```bash
python manage.py runserver
```
### Acceder desde el navegador 
```bash
http://127.0.0.1:8000
```

### 🚀 Despliegue en PythonAnywhere (Resumen)
Creación del entorno virtual:
```bash
mkvirtualenv virtual --python=python3.10
```
Clonación del repositorio desde GitHub.

Instalación de dependencias.

Configuración del archivo WSGI.

Configuración de archivos estáticos y multimedia.

Ejecución de:
```bash
python manage.py collectstatic
python manage.py migrate
```

Configuración de:

DEBUG = False

ALLOWED_HOSTS

Variables de entorno

Reinicio y validación del sistema.

### Equipo del Proyecto
**Desarrollo Backend / Frontend**

Santiago Alzate

Santiago Molano

Alejandro Quiceno

Sebastián Perdomo

**SCRUM / Acompañamiento**

Instructoras:

Diana Carolina Gálvez

Diana Carolina Vargas


