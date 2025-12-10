# EventSoft

**Descripción del Proyecto**

Este proyecto corresponde a una aplicación web completa para la gestión automatizada de eventos, desarrollada como solución a una necesidad presentada por varias instructoras (clientes), quienes requerían un sistema capaz de administrar todo tipo de eventos de forma eficiente, ordenada y centralizada.

El sistema permite manejar eventos académicos, culturales, empresariales, e integra varios tipos de usuarios con funcionalidades específicas:

**Roles del Sistema**

**Exponentes:** realizan preinscripción, cargan documentación y consultan estado.

**Evaluadores:** califican participantes según criterios definidos, modifican sus datos y descargan reportes.

**Administradores:** gestionan eventos, participantes, evaluadores y asignaciones.

**Super Administradores:** control total sobre todas las apps del sistema.

**Funcionalidades Principales**

Registro y administración completa de eventos.

Inscripción automática de participantes con carga de documentos.

Gestión de criterios de evaluación para cada evento.

Asignación de evaluadores y control de accesos.

Proceso de evaluación con cálculos automáticos y ranking.

Generación de reportes en PDF para evaluadores y eventos.

Dashboard con estadísticas para cada usuario.

////////////////////////////////////////////////////////////


**Enlace del despliegue (PythonAnywhere):**

[https://tuprojecto.pythonanywhere.com](https://sebastian1010101010.pythonanywhere.com/)


**Instrucciones claras para la ejecución en línea**

La aplicación está desplegada en PythonAnywhere, lo que permite acceder al sistema directamente desde cualquier navegador sin necesidad de instalar nada.

**Cómo usar la aplicación online:**

-Entra al enlace del sitio web desplegado.

-Selecciona el rol con el que deseas ingresar (Participante, Evaluador, Administrador, etc.).

-Si eres evaluador o participante:

-Ingresa con tu cédula o el identificador asignado.

-Accede a tu panel personal.

-Si eres administrador:

-Accede con las credenciales entregadas por el Product Owner.

-Gestiona eventos, evaluadores, categorías, criterios o participantes.

-El sistema se ejecuta automáticamente en un servidor PythonAnywhere:

-Base de datos configurada.

-Archivos estáticos cargados.

-Media y documentos habilitados.

-Interpretación de Django desde un virtual environment en la nube.

**Características del despliegue en PythonAnywhere:**

-Se configuró el virtual environment del proyecto.

-Se instaló Django, WeasyPrint y demás dependencias.

-Se configuró el archivo WSGI para ejecutar el proyecto.

-Se configuró la base de datos para uso en producción.

-Se configuró la ruta de archivos estáticos (collectstatic).

-Se habilitaron las rutas de documentos cargados por los usuarios.

**Instrucciones para Clonar y Ejecutar el Proyecto en un Entorno de Desarrollo (LOCAL)**

A continuación están los pasos completamente detallados, pensados incluso para alguien que nunca haya abierto Django:

**1. Clonar el repositorio desde GitHub**

Abre la terminal y ejecuta:

git clone https://github.com/alejandro-quiceno96/EventSoft.git

**2. Entrar en la carpeta del proyecto**
cd https://github.com/alejandro-quiceno96/EventSoft.git

**3. Crear un entorno virtual (recomendado)**

Esto evita errores por versiones de librerías.

Windows:
python -m venv virtual

Linux / Mac:
python3 -m venv virtual

**4. Activar el entorno virtual**
Windows:
virtual\Scripts\activate


**5. Instalar dependencias**

Con el entorno virtual activo, ejecuta:

pip install -r requirements.txt


**Esto instalará:**

Django

WeasyPrint

Pillow

psycopg2 / sqlite

Django REST Framework 

Cualquier otra librería del sistema

**6. Crear las migraciones**
python manage.py makemigrations
python manage.py migrate

**7. Crear un superusuario (opcional pero recomendado)**
python manage.py createsuperuser


Sigue las instrucciones en pantalla.

**8. Cargar archivos estáticos (solo una vez)**
python manage.py collectstatic

**9. Ejecutar el servidor local**

Finalmente:

python manage.py runserver


**Ahora entra a:**

http://127.0.0.1:8000

Y podrás ver la aplicación funcionando localmente.

**EXTRA: Cómo lo desplegamos en PythonAnywhere?**

La aplicación fue desplegada usando PythonAnywhere, siguiendo estos pasos:

Se subió el código al repositorio GitHub.

En PythonAnywhere se creó un virtual environment idéntico al local:

mkvirtualenv virtual --python=python3.10


Se instaló el proyecto desde GitHub dentro del servidor:

git clone https://github.com/alejandro-quiceno96/EventSoft.git


Se instaló requirements.txt.

Se configuró el archivo WSGI para apuntar al módulo Django principal.

Se configuraron las rutas:

Static files

Media files (documentos de los participantes)

Se configuró la base de datos en el panel (SQLite o PostgreSQL).

Se corrió collectstatic en el servidor.

Se reinició la app web.

Con esto el proyecto quedó en producción, accesible para todos los roles del sistema.



**Equipo del Proyecto**
Integrantes: 
Santiago Alzate/Desarrollador Backend / Frontend:
Santiago Molano/Desarrollador Backend / Frontend:
Alejandro Quiceno/Desarrollador Backend / Frontend:
Sebastian Perdomo/Desarrollador Backend / Frontend:
Equipo SCRUM/Acompañamiento y dirección metodológica:
Instructoras (Clientes)/Especificación de requisitos:
