from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import subprocess
import uuid
import os
import tempfile
from starlette.background import BackgroundTask
import shutil

app = FastAPI()

# Imprime la versión de ffmpeg, el PATH, busca ffmpeg en rutas comunes y lista /nix/var/nix/profiles/default/bin al iniciar el servidor
try:
    ffmpeg_version = subprocess.check_output(["ffmpeg", "-version"]).decode().split("\n")[0]
    print(f"[INFO] {ffmpeg_version}")
except Exception as e:
    print(f"[ERROR] ffmpeg no está disponible: {e}")

print(f"[INFO] PATH actual: {os.environ.get('PATH')}")

# Busca ffmpeg en rutas comunes
for path in ["/usr/bin/ffmpeg", "/nix/var/nix/profiles/default/bin/ffmpeg", "/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
    if os.path.exists(path):
        print(f"[INFO] ffmpeg encontrado en: {path}")

# Lista el contenido de /nix/var/nix/profiles/default/bin
try:
    files = os.listdir("/nix/var/nix/profiles/default/bin")
    print(f"[INFO] Archivos en /nix/var/nix/profiles/default/bin: {files}")
except Exception as e:
    print(f"[ERROR] No se pudo listar /nix/var/nix/profiles/default/bin: {e}")

@app.post("/convert")
async def convert_audio(file: UploadFile = File(...)):
    # Verifica extensión
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".aac", ".amr", ".3gp"]:
        return PlainTextResponse("Formato no compatible", status_code=400)

    # Verifica que ffmpeg esté disponible
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return PlainTextResponse("ffmpeg no está instalado o no está en PATH", status_code=500)

    # Rutas temporales multiplataforma
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
    output_path = input_path.rsplit(".", 1)[0] + ".m4a"

    # Guarda el archivo
    try:
        with open(input_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        return PlainTextResponse(f"Error guardando archivo: {e}", status_code=500)

    # Ejecuta ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c:a", "aac", "-b:a", "128k", output_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        if os.path.exists(input_path):
            os.remove(input_path)
        return PlainTextResponse(f"Error al convertir el audio: {error_msg}", status_code=500)

    # Tarea para limpiar archivos temporales después de la respuesta
    def cleanup():
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

    return FileResponse(
        path=output_path,
        media_type="audio/m4a",
        filename="output.m4a",
        background=BackgroundTask(cleanup)
    )
