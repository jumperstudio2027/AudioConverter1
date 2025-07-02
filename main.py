from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import subprocess
import uuid
import os
import tempfile
from starlette.background import BackgroundTask

app = FastAPI()

@app.post("/convert")
async def convert_audio(file: UploadFile = File(...)):
    # Verifica extensión
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".aac", ".amr", ".3gp"]:
        raise HTTPException(status_code=400, detail="Formato no compatible")

    # Rutas temporales multiplataforma
    temp_dir = tempfile.gettempdir()
    input_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
    output_path = input_path.rsplit(".", 1)[0] + ".m4a"

    # Guarda el archivo
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Ejecuta ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c:a", "aac", "-b:a", "128k", output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        # Limpia archivo temporal de entrada si hay error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise HTTPException(status_code=500, detail="Error al convertir el audio")

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
