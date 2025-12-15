from pathlib import Path
import os
import sys
from decouple import config

# BASE
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
#  VARIABLES DE ENTORNO
# -------------------------------
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool, default=False)

ALLOWED_HOSTS = [
    'sebastian1010101010.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
]


# -------------------------------
#  APLICACIONES
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anymail',

    # Tus apps
    'app_administrador',
    'app_areas',
    'app_eventos',
    'app_categorias',
    'app_asistente',
    'app_participante',
    'app_evaluador',
    'app_criterios',
    'app_visitante',
    'app_super_admin',
    'app_usuarios',
    'app_certificados',
]


# -------------------------------
#  MIDDLEWARE
# -------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Debe ir justo después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'pr_eventsoft.urls'


# -------------------------------
#  TEMPLATES
# -------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pr_eventsoft.wsgi.application'


# -------------------------------
#  BASE DE DATOS
# -------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),        # Nombre de tu base local
        'USER': config('DB_USER'),        # Usuario local (ej: root)
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
    }
}



# -------------------------------
#  VALIDACIÓN DE PASSWORDS
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'app_usuarios.Usuario'
LOGIN_URL = '/admin/login/'


# -------------------------------
#  INTERNACIONALIZACIÓN
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# -------------------------------
#  ARCHIVOS MEDIA
# -------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# -------------------------------
#  ARCHIVOS ESTÁTICOS
# -------------------------------
STATIC_URL = '/static/'

# Carpeta donde collectstatic guardará archivos para producción
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Solo la carpeta principal; las apps ya tienen su static interno
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise storage para producción
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# -------------------------------
#  CONFIGURACIÓN DE CORREO
# -------------------------------

USE_BREVO = config('USE_BREVO', cast=bool, default=False)



if USE_BREVO:
    # Producción: Brevo por API HTTP (Anymail)
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    DEFAULT_FROM_EMAIL = "sebastianperdomotriana@gmail.com"

    ANYMAIL = {
        "BREVO_API_KEY": config("BREVO_API_KEY"),
    }
else:
    # Desarrollo local: Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'sebastianperdomotriana@gmail.com'
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = 'sebastianperdomotriana@gmail.com'

# Backend para pruebas
if 'test' in sys.argv:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
