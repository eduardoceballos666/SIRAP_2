"""API REST de SIRAP (FastAPI).

Ejecutar desde la raíz del repositorio::

    uvicorn api.main:app --reload

Documentación interactiva en http://localhost:8000/docs. Si existe ``frontend/dist`` (``npm run build``),
la misma API sirve el frontend Vue en ``/``. La app de Streamlit (``app/``) no se modifica ni depende de esto.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api import __version__
from api.deps import get_store, get_pipeline
from api.routers import admin, auth, recognition, reports
from api.settings import settings
from src.utils import ROOT_DIR, get_logger

logger = get_logger("sirap.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_store()
    try:
        get_pipeline()  # carga YOLO11-s y el OCR una sola vez
    except Exception as exc:  # noqa: BLE001 - la API arranca aunque falte el modelo
        logger.error("No se pudo precargar el pipeline: %s", exc)
    yield


app = FastAPI(
    title="SIRAP API",
    version=__version__,
    description="Sistema de Detección y Reconocimiento Automático de Placas · YOLO11-s + fast-plate-ocr.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for module in (auth, recognition, reports, admin):
    app.include_router(module.router)


@app.get("/api/health", tags=["Sistema"], summary="Prueba de vida")
def health() -> dict[str, str]:
    return {"estado": "ok", "version": __version__}


_dist = (ROOT_DIR / settings.frontend_dist).resolve()
if (_dist / "index.html").exists():
    if (_dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(404, "Ruta no encontrada.")
        file = (_dist / path).resolve()
        if path and file.is_file() and _dist in file.parents:
            return FileResponse(file)
        return FileResponse(_dist / "index.html")
