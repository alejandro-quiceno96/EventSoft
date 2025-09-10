# Imagen base slim (última estable de Debian Trixie)
FROM python:3.11-slim

# Evitar buffer en logs
ENV PYTHONUNBUFFERED=1

# Instalar dependencias necesarias para mysqlclient, weasyprint, pillow, qrcode
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       default-libmysqlclient-dev \
       pkg-config \
       libmariadb-dev \
       curl \
       netcat-traditional \
       # Dependencias de WeasyPrint y renderizado
       libpango-1.0-0 \
       libpangoft2-1.0-0 \
       libcairo2 \
       libgdk-pixbuf-2.0-0 \
       libffi-dev \
       libxml2 \
       libxslt1.1 \
       shared-mime-info \
       fonts-liberation \
    && rm -rf /var/lib/apt/lists/*


# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalarlos
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . /app/

# Exponer puerto Django
EXPOSE 8000

# Copiar entrypoint.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Arrancar el servidor Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
