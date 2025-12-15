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

-Registro y administración completa de eventos.

-Inscripción automática de participantes con carga de documentos.

-Gestión de criterios de evaluación para cada evento.

-Asignación de evaluadores y control de accesos.

-Proceso de evaluación con cálculos automáticos y ranking.

-Generación de reportes en PDF para evaluadores y eventos.

-Dashboard con estadísticas para cada usuario.

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

**Paso a Paso clonar el proyecto**
paso 1: Ingresar a archivos del Pc.

paso 2: Elegir donde descargar el proyecto

Paso 3: Entrar al cmd de git hub 

Paso 4: Iniciarlizar el repositorio con **git init**

Paso 5: Clonar el proyecto del repositorio **git clone https://github.com/alejandro-quiceno96/EventSoft.git**

Paso 6: Entrar al archivo a verificar los archivos 

Paso 7: Entrar al VS CODE, seleccionar la carpeta y abrirla

Paso 8: Abrir el terminal ingresar a la carpeta **cd Eventsoft**

Paso 9: Activar el entorno virtual 

Paso 10: descargar todos los paquetes **pip install -r requirements.txt**

Paso 11: Hacer las migraciones en la BD **python manage.py makemigrations** , **python manage.py migrate**, (LLenar la BD)

Paso 12:Crear el SuperUsuario **python manage.py createsuperuser** (Llenar el panel)

Paso 13 Ejectuar la aplicacion localmente **python manage.py runserver**

Paso 14: ingresar al localHost **http://127.0.0.1:8000**

**Características del despliegue en PythonAnywhere:**

-Se configuró el virtual environment del proyecto.

-Se instaló Django, WeasyPrint y demás dependencias.

-Se configuró el archivo WSGI para ejecutar el proyecto.

-Se configuró la base de datos para uso en producción.

-Se configuró la ruta de archivos estáticos (collectstatic).

-Se habilitaron las rutas de documentos cargados por los usuarios.


**Despliegue del proyecto en PythonAnywhere**

1. Control de versiones

Inicialmente, el proyecto fue organizado y subido a un repositorio en GitHub, lo que permitió una gestión adecuada del código y facilitó su instalación en el servidor.

2. Creación del entorno virtual

En el servidor de PythonAnywhere se creó un entorno virtual con la misma versión de Python utilizada en desarrollo local, asegurando compatibilidad entre ambientes:

**mkvirtualenv virtual --python=python3.10**

Posteriormente, se activó el entorno virtual para trabajar de forma aislada.

3. Clonación del proyecto

El proyecto fue clonado directamente desde el repositorio de GitHub al servidor:

**git clone https://github.com/alejandro-quiceno96/EventSoft.git**

Esto permitió contar con la misma estructura y código del entorno local.

4. Instalación de dependencias

Con el entorno virtual activo, se instalaron todas las dependencias necesarias usando el archivo requirements.txt:

**pip install -r requirements.txt**

Esto aseguró que todas las librerías requeridas por Django y el proyecto estuvieran disponibles.

5. Configuración del archivo WSGI

Se configuró el archivo WSGI de PythonAnywhere para que apunte correctamente al módulo principal del proyecto Django, permitiendo que la aplicación web pueda ejecutarse en producción.

6. Configuración de archivos estáticos y multimedia

Se configuraron las rutas necesarias en el panel de PythonAnywhere para:

Static files, utilizados por el diseño y la interfaz.

Media files, destinados al almacenamiento de documentos e imágenes subidas por los participantes.

Además, se ejecutó el comando:

**python manage.py collectstatic**

para centralizar los archivos estáticos en el servidor.

7. Configuración de la base de datos

La base de datos fue configurada utilizando SQLite, opción adecuada para el tamaño y alcance del proyecto, y se verificó su correcto funcionamiento desde el panel de PythonAnywhere.

8. Migraciones

Se ejecutaron las migraciones para asegurar que la estructura de la base de datos estuviera sincronizada con los modelos del proyecto:

**python manage.py migrate**

9. Variables de entorno y seguridad

Se ajustaron parámetros importantes del proyecto, como:

D**EBUG = False para entorno de producción.**

Configuración correcta de ALLOWED_HOSTS.

Uso de variables de entorno para datos sensibles.

10. Reinicio y verificación

Finalmente, se reinició la aplicación web desde el panel de PythonAnywhere y se realizaron pruebas funcionales para validar el acceso correcto de todos los roles del sistema.






**Equipo del Proyecto**
Integrantes: 
Santiago Alzate/Desarrollador Backend / Frontend:
Santiago Molano/Desarrollador Backend / Frontend:
Alejandro Quiceno/Desarrollador Backend / Frontend:
Sebastian Perdomo/Desarrollador Backend / Frontend:
Equipo SCRUM/Acompañamiento y dirección metodológica:
Instructoras (Clientes)/Especificación de requisitos:
