"""Configuración de la API, leída de variables de entorno (ver ``api/.env.example``)."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field

from src.utils import ROOT_DIR, get_logger, get_secret

logger = get_logger("sirap.api")


def _load_dotenv(path=ROOT_DIR / ".env") -> None:
    """Carga ``.env`` de la raíz en ``os.environ`` sin pisar variables ya definidas (formato ``NOMBRE=valor``)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        if name.strip() and value:
            os.environ.setdefault(name.strip(), value)


_load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    value = get_secret(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    """Parámetros de la API."""

    #: Clave para firmar los JWT. Si no se define, se genera una al iniciar (los tokens dejan de valer al reiniciar).
    jwt_secret: str = field(default_factory=lambda: _env("SIRAP_JWT_SECRET") or secrets.token_urlsafe(48))
    jwt_hours: float = float(_env("SIRAP_JWT_HOURS", "12"))
    #: Base SQLite propia de la API (demo). Con PG_DSN se usa PostgreSQL, compartida con la app de Streamlit.
    sqlite_path: str = _env("SIRAP_API_DB", "data/processed/sirap_api.db")
    #: Contraseña inicial de los usuarios de demostración (operador, supervisor, admin). Vacía = no crear.
    demo_password: str = _env("SIRAP_DEMO_PASSWORD", "sirap2026") or ""
    #: Orígenes permitidos para el frontend en desarrollo (Vite usa el puerto 5173).
    cors_origins: tuple[str, ...] = tuple(
        o.strip() for o in (_env("SIRAP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173") or "").split(",")
        if o.strip())
    #: Carpeta del frontend compilado (``npm run build``); si existe, la API también lo sirve.
    frontend_dist: str = _env("SIRAP_FRONTEND_DIST", "frontend/dist")


settings = Settings()
if not _env("SIRAP_JWT_SECRET"):
    logger.warning("SIRAP_JWT_SECRET no está definido: se generó una clave temporal (solo para desarrollo).")
