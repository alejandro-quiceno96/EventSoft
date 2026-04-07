# Imagen base
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Instalar dependencias necesarias
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       libpq-dev \
       pkg-config \
       curl \
       netcat-traditional \
       # 🔥 claves para que no falle pip
       libssl-dev \
       libffi-dev \
       python3-dev \
       # WeasyPrint
       libpango-1.0-0 \
       libpangoft2-1.0-0 \
       libcairo2 \
       libgdk-pixbuf-2.0-0 \
       libxml2 \
       libxslt1.1 \
       shared-mime-info \
       fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "pr_eventsoft.wsgi:application", "--bind", "0.0.0.0:8000"]