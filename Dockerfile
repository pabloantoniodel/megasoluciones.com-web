FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    PORT=5000

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Chromium headless para leer transcripciones de YouTube como un navegador real
# (YouTube bloquea las peticiones directas de la API desde IPs de datacenter)
RUN python -m playwright install --with-deps chromium-headless-shell \
    && rm -rf /var/lib/apt/lists/*

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "300", "--keep-alive", "5", "--graceful-timeout", "30", "app:app"]
