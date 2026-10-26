"""Respaldo privado de los CSV de SIRAP en GitHub Contents API.

El repositorio se valida como privado antes de leer o guardar datos. El token solo se
lee desde el entorno; nunca se escribe en archivos ni registros.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPOSITORY = os.getenv("SIRAP_DATA_GITHUB_REPO", "eduardoceballos666/SIRAP_datos_privados")
API = "https://api.github.com"
_ALLOWED = {
    "vehiculos.csv", "autorizaciones.csv", "operaciones.csv",
    "garitas.csv", "usuarios.csv", "credenciales.csv",
}
_LOCK = threading.RLock()
_PRIVATE_REPO_VERIFIED = False


class GitHubStorageError(RuntimeError):
    """Fallo de acceso al respaldo privado de datos."""


def _token() -> str | None:
    return os.getenv("SIRAP_DATA_GITHUB_TOKEN") or None


def _request(method: str, path: str, payload: dict | None = None) -> dict | None:
    token = _token()
    if not token:
        return None
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SIRAP-private-csv-backup",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise GitHubStorageError(f"GitHub respondió HTTP {exc.code} al acceder al respaldo.") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GitHubStorageError(f"No se pudo acceder al respaldo privado de GitHub: {exc}") from exc


def _repo_path(file_name: str) -> str:
    if file_name not in _ALLOWED:
        raise ValueError(f"CSV no permitido para sincronización: {file_name}")
    owner, repo = REPOSITORY.split("/", 1)
    return f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/contents/data/processed/{file_name}"


def _verify_private_repository() -> None:
    global _PRIVATE_REPO_VERIFIED
    if not _token():
        return
    if _PRIVATE_REPO_VERIFIED:
        return
    owner, repo = REPOSITORY.split("/", 1)
    info = _request("GET", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}")
    if not info or info.get("private") is not True:
        raise GitHubStorageError(f"El repositorio {REPOSITORY} no existe, no es accesible o no es privado.")
    _PRIVATE_REPO_VERIFIED = True


def restore_csvs(data_dir: str | Path) -> bool:
    """Descarga los CSV existentes antes de que CsvStore cree tablas iniciales."""
    if not _token():
        return False
    _verify_private_repository()
    target = Path(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        for file_name in sorted(_ALLOWED):
            item = _request("GET", _repo_path(file_name))
            if not item:
                continue
            if item.get("type") != "file":
                raise GitHubStorageError(f"El archivo {file_name} del respaldo no tiene un formato compatible.")
            encoded = item.get("content")
            if item.get("encoding") != "base64" or not encoded:
                blob_sha = item.get("sha")
                blob_path = "/repos/" + REPOSITORY + "/git/blobs/" + blob_sha if blob_sha else ""
                blob = _request("GET", blob_path) if blob_path else None
                encoded = blob.get("content") if blob and blob.get("encoding") == "base64" else None
            if not encoded:
                raise GitHubStorageError(f"No se pudo descargar el contenido de {file_name}.")
            try:
                contents = base64.b64decode(encoded)
                contents.decode("utf-8")
            except (ValueError, UnicodeDecodeError) as exc:
                raise GitHubStorageError(f"El archivo {file_name} del respaldo no es un CSV UTF-8 válido.") from exc
            (target / file_name).write_bytes(contents)
    return True


def backup_missing_csvs(data_dir: str | Path) -> None:
    """Sube las tablas locales que aún no existen en el respaldo (primera inicialización)."""
    if not _token():
        return
    _verify_private_repository()
    target = Path(data_dir)
    with _LOCK:
        for file_name in sorted(_ALLOWED):
            if _request("GET", _repo_path(file_name)):
                continue
            path = target / file_name
            if path.is_file():
                save_csv(file_name, path.read_text(encoding="utf-8"))


def save_csv(file_name: str, contents: str) -> None:
    """Guarda un CSV completo en una ruta permitida del repositorio privado."""
    if not _token():
        return
    _verify_private_repository()
    path = _repo_path(file_name)
    encoded = base64.b64encode(contents.encode("utf-8")).decode("ascii")
    with _LOCK:
        for attempt in range(2):
            existing = _request("GET", path)
            payload = {
                "message": f"Actualizar respaldo SIRAP: {file_name}",
                "content": encoded,
            }
            if existing and existing.get("sha"):
                payload["sha"] = existing["sha"]
            try:
                _request("PUT", path, payload)
                return
            except GitHubStorageError as exc:
                if "HTTP 409" not in str(exc) or attempt:
                    raise
        raise GitHubStorageError(f"No se pudo guardar {file_name} en el respaldo privado.")
