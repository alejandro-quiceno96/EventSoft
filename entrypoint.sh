#!/bin/sh

echo "🚀 Iniciando entrypoint..."

# Variables de entorno
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT:-5432}

echo "⏳ Esperando a que PostgreSQL ($DB_HOST:$DB_PORT) esté disponible..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "✅ PostgreSQL está disponible"

echo "📝 Creando migraciones automáticamente..."
python manage.py makemigrations --noinput
# Migraciones
echo "📂 Ejecutando migraciones..."
python manage.py migrate --noinput

# Superusuario automático (opcional)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "👤 Creando superusuario..."
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

# Ejecutar servidor
echo "🚀 Iniciando servidor Django en 0.0.0.0:8000"
exec "$@"