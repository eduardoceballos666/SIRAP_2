"""Dependencias compartidas: archivos CSV, pipeline ALPR, barrera y usuario autenticado."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.security import decode_token, ensure_credentials_table
from api.settings import settings
from src.access_control import barrier_from_config
from src.storage import CsvStore
from src.model import ALPRPipeline
from src.utils import load_config, load_json

_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    return load_config()


@lru_cache(maxsize=1)
def get_store() -> CsvStore:
    """Usa el archivo local de demostración configurado para la API."""
    db = CsvStore(data_dir=settings.data_dir)
    ensure_credentials_table(db)
    return db


@lru_cache(maxsize=1)
def get_pipeline() -> ALPRPipeline:
    """El detector y el OCR se cargan una sola vez por proceso."""
    return ALPRPipeline.from_config(get_config())


@lru_cache(maxsize=1)
def get_barrier():
    return barrier_from_config(get_config())


def thresholds() -> tuple[float, float, int]:
    """(umbral OCR, umbral de decisión del detector, distancia de «casi coincide»)."""
    cfg = get_config()
    det = (load_json("results/metrics/umbrales.json") or {}).get("YOLO11", {}).get(
        "conf", cfg["detector"].get("conf_decision", 0.30))
    return float(cfg["decision"]["umbral_confianza_ocr"]), float(det), int(cfg["decision"]["distancia_max_similar"])


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict[str, Any]:
    """Usuario del token ``Authorization: Bearer …``."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicie sesión.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La sesión expiró; vuelva a iniciar sesión.")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido.")
    store = get_store()
    if not store.is_user_active(payload["sub"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El usuario está inactivo; vuelva a iniciar sesión con otra cuenta.")
    rows = store.table("usuarios")
    rows = rows[rows["usuario"].astype(str) == payload["sub"]]
    if rows.empty:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El usuario ya no existe; vuelva a iniciar sesión.")
    row = rows.iloc[-1]
    # Lee nombre y rol vigentes desde el CSV para aplicar de inmediato cambios administrativos.
    return {"usuario": payload["sub"], "nombre": row["nombre"], "rol": row["rol"]}


def require_roles(*roles: str) -> Callable[..., dict[str, Any]]:
    """Dependencia que exige uno de los roles indicados."""

    def checker(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["rol"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Su rol no tiene permiso para esta acción.")
        return user

    return checker
