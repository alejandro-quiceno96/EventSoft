#!/bin/sh

echo "🚀 Iniciando entrypoint..."

# Variables de entorno desde docker-compose.yml
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

echo "⏳ Esperando a que MySQL ($DB_HOST:$DB_PORT) esté disponible..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "✅ MySQL está disponible"

# Aplicar migraciones de Django
echo "📂 Ejecutando migraciones..."
python manage.py migrate --noinput

# Crear superusuario automáticamente (opcional)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "👤 Creando superusuario..."
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

# Ejecutar comando por defecto
echo "🚀 Iniciando servidor Django en 0.0.0.0:8000"
exec "$@"
