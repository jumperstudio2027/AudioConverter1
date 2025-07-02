FROM python:3.10-slim

# Instala ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Copia el código
WORKDIR /app
COPY . /app

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el servicio
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000}"]
