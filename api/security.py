"""Autenticación de la API: contraseñas con PBKDF2 y tokens JWT con rol.

Las contraseñas se guardan como hashes en `credenciales.csv`, separados de `usuarios.csv`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from api.settings import settings
from src.utils import get_logger

logger = get_logger("sirap.api.security")

ROLES = ("OPERADOR", "SUPERVISOR", "ADMINISTRADOR")
_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    """Hash PBKDF2-SHA256 con sal aleatoria, en formato ``pbkdf2$iteraciones$sal$hash``."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return "pbkdf2${}${}${}".format(_ITERATIONS, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password: str, stored: str) -> bool:
    """Compara en tiempo constante una contraseña con su hash."""
    try:
        _, iterations, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(candidate, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def create_token(user: dict[str, Any]) -> str:
    """JWT con usuario, nombre y rol, válido ``settings.jwt_hours`` horas."""
    now = datetime.now(timezone.utc)
    payload = {"sub": user["usuario"], "nombre": user["nombre"], "rol": user["rol"],
               "iat": now, "exp": now + timedelta(hours=settings.jwt_hours)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """Valida firma y vencimiento. Lanza ``jwt.PyJWTError`` si el token no es válido."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def ensure_credentials_table(store: Any) -> None:
    """Crea credenciales CSV para los usuarios activos de demostración."""
    if not settings.demo_password:
        return
    for usuario in store.active_users():
        if not store.credential_hash(usuario):
            store.set_credential(usuario, hash_password(settings.demo_password))
            logger.info("Usuario de demostración habilitado en la API: %s", usuario)


def authenticate(store: Any, usuario: str, password: str) -> dict[str, Any] | None:
    """Devuelve el usuario si la contraseña es correcta y sigue activo."""
    usuario = usuario.strip()
    if not store.is_user_active(usuario):
        return None
    password_hash = store.credential_hash(usuario)
    if not password_hash or not verify_password(password, password_hash):
        return None
    rows = store.table("usuarios")
    rows = rows[rows["usuario"] == usuario]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    return {"usuario": row["usuario"], "nombre": row["nombre"], "rol": row["rol"]}


def set_password(store: Any, usuario: str, password: str) -> None:
    """Crea o cambia la contraseña de un usuario."""
    store.set_credential(usuario, hash_password(password))
