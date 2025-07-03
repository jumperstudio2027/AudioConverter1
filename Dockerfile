# Dockerfile para FastAPI + ffmpeg en Railway
FROM python:3.11-slim

# Instala ffmpeg y dependencias del sistema
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Crea el directorio de la app
WORKDIR /app

# Copia los archivos de la app
COPY . /app

# Instala dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto (Railway usará la variable $PORT)
EXPOSE 8080

# Comando de inicio
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT}"
