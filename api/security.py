"""Autenticación de la API: contraseñas con PBKDF2 y tokens JWT con rol.

Las contraseñas viven en una tabla propia de la API (``api_credenciales``), separada de
``usuarios``, para no modificar el esquema que usa la app de Streamlit.
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


def ensure_credentials_table(db: Any) -> None:
    """Crea la tabla de credenciales y, si hay contraseña de demo, la asigna a los usuarios que no tienen."""
    db.execute("""CREATE TABLE IF NOT EXISTS api_credenciales (
                    usuario TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL)""")
    if not settings.demo_password:
        return
    users = db.query("SELECT usuario FROM usuarios WHERE activo = ?", (True,))["usuario"].tolist()
    existing = set(db.query("SELECT usuario FROM api_credenciales")["usuario"].tolist())
    for usuario in users:
        if usuario not in existing:
            db.execute("INSERT INTO api_credenciales (usuario, password_hash) VALUES (?, ?)",
                       (usuario, hash_password(settings.demo_password)))
            logger.info("Usuario de demostración habilitado en la API: %s", usuario)


def authenticate(db: Any, usuario: str, password: str) -> dict[str, Any] | None:
    """Devuelve el usuario si la contraseña es correcta y está activo."""
    df = db.query("""SELECT u.usuario, u.nombre, u.rol, c.password_hash FROM usuarios u
                     JOIN api_credenciales c ON c.usuario = u.usuario
                     WHERE u.usuario = ? AND u.activo = ?""", (usuario.strip(), True))
    if df.empty or not verify_password(password, df.iloc[0]["password_hash"]):
        return None
    row = df.iloc[0]
    return {"usuario": row["usuario"], "nombre": row["nombre"], "rol": row["rol"]}


def set_password(db: Any, usuario: str, password: str) -> None:
    """Crea o cambia la contraseña de un usuario."""
    hashed = hash_password(password)
    if db.query("SELECT 1 FROM api_credenciales WHERE usuario = ?", (usuario,)).empty:
        db.execute("INSERT INTO api_credenciales (usuario, password_hash) VALUES (?, ?)", (usuario, hashed))
    else:
        db.execute("UPDATE api_credenciales SET password_hash = ? WHERE usuario = ?", (hashed, usuario))
