"""GitHub privado es la fuente persistente de CSV operativos de SIRAP.

El disco del hosting se usa solo como copia de trabajo. Las escrituras usan el
SHA de GitHub para evitar sobreescribir cambios concurrentes o registros previos.
No se envían datos a ningún repositorio público.
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
    """Fallo al leer, confirmar o escribir CSV en GitHub privado."""


def _token() -> str | None:
    return os.getenv("SIRAP_DATA_GITHUB_TOKEN") or None


def remote_storage_required() -> bool:
    return os.getenv("SIRAP_GITHUB_REQUIRED", "").strip().lower() in ("1", "true", "yes", "si", "sí")


def durable_backup_configured() -> bool:
    """La presencia del token no prueba acceso; la escritura comprueba el repo."""
    return bool(_token())


def _request(method: str, path: str, payload: dict | None = None) -> dict | None:
    token = _token()
    if not token:
        raise GitHubStorageError("Falta SIRAP_DATA_GITHUB_TOKEN para acceder al almacenamiento privado.")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SIRAP-private-csv-primary",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        # Un 409/422 siempre significa abortar, NUNCA repetir la misma copia antigua.
        raise GitHubStorageError(f"GitHub respondió HTTP {exc.code} al acceder al CSV privado.") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise GitHubStorageError("No se pudo acceder al repositorio privado de GitHub.") from exc


def _repo_path(file_name: str) -> str:
    if file_name not in _ALLOWED:
        raise ValueError("CSV no permitido para sincronización: " + file_name)
    owner, repo = REPOSITORY.split("/", 1)
    return f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/contents/data/processed/{file_name}"


def _verify_private_repository() -> None:
    global _PRIVATE_REPO_VERIFIED
    if not _token():
        raise GitHubStorageError("GitHub es obligatorio: configure SIRAP_DATA_GITHUB_TOKEN.")
    if _PRIVATE_REPO_VERIFIED:
        return
    owner, repo = REPOSITORY.split("/", 1)
    info = _request("GET", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}")
    if not info or info.get("private") is not True:
        raise GitHubStorageError(f"El repositorio {REPOSITORY} debe existir y ser privado.")
    _PRIVATE_REPO_VERIFIED = True


def _read_item(file_name: str) -> tuple[str | None, str | None]:
    _verify_private_repository()
    item = _request("GET", _repo_path(file_name))
    if item is None:
        return None, None
    if item.get("type") != "file" or not item.get("sha"):
        raise GitHubStorageError(f"Archivo remoto no válido: {file_name}")
    encoded = item.get("content") if item.get("encoding") == "base64" else None
    if not encoded:
        blob_sha = item["sha"]
        blob = _request("GET", f"/repos/{REPOSITORY}/git/blobs/{blob_sha}")
        encoded = blob.get("content") if blob and blob.get("encoding") == "base64" else None
    if not encoded:
        raise GitHubStorageError(f"GitHub no entregó el contenido de {file_name}.")
    try:
        return base64.b64decode(encoded, validate=False).decode("utf-8-sig"), item["sha"]
    except (ValueError, UnicodeDecodeError) as exc:
        raise GitHubStorageError(f"CSV remoto ilegible: {file_name}") from exc


def read_csv(file_name: str) -> tuple[str | None, str | None]:
    """Leer siempre la versión más reciente; nunca dar por buena una caché local."""
    if not _token():
        if remote_storage_required():
            raise GitHubStorageError("GitHub es obligatorio: falta SIRAP_DATA_GITHUB_TOKEN.")
        return None, None
    with _LOCK:
        return _read_item(file_name)


def restore_csvs(data_dir: str | Path) -> bool:
    """Descarga todos los CSV antes de tocar el disco; no crea ni trunca los remotos."""
    if not _token():
        if remote_storage_required():
            raise GitHubStorageError("No se iniciará SIRAP sin el token de GitHub privado.")
        return False
    target = Path(data_dir)
    with _LOCK:
        downloaded = {}
        for file_name in sorted(_ALLOWED):
            contents, _sha = _read_item(file_name)
            if contents is None:
                if remote_storage_required():
                    raise GitHubStorageError(f"Falta {file_name} en GitHub privado; no inicializar con CSV vacío.")
                continue
            downloaded[file_name] = contents
        target.mkdir(parents=True, exist_ok=True)
        for file_name, contents in downloaded.items():
            (target / file_name).write_text(contents, encoding="utf-8")
    return True


def backup_missing_csvs(data_dir: str | Path) -> None:
    """Solo para instalaciones locales iniciales; nunca importa copias de hosting obsoletas."""
    if remote_storage_required() or not _token():
        return
    with _LOCK:
        _verify_private_repository()
        for file_name in sorted(_ALLOWED):
            existing, _sha = _read_item(file_name)
            if existing is not None:
                continue
            path = Path(data_dir) / file_name
            if path.is_file():
                save_csv(file_name, path.read_text(encoding="utf-8"), expected_sha=None)


def save_csv(file_name: str, contents: str, *, expected_sha: str | None = None) -> str | None:
    """CAS: si otro escritor cambió GitHub, abortar sin sustituir registros ajenos.

    Un caller no debe volver a enviar el mismo contenido después de un conflicto:
    debe releer GitHub, reconstruir su cambio y ejecutar otra vez la operación.
    """
    if not _token():
        if remote_storage_required():
            raise GitHubStorageError("GitHub obligatorio: se canceló escritura sin token.")
        return None
    with _LOCK:
        _verify_private_repository()
        path = _repo_path(file_name)
        existing = _request("GET", path)
        actual_sha = existing.get("sha") if existing else None
        if actual_sha != expected_sha:
            raise GitHubStorageError(
                f"Conflicto de versión en {file_name}. Se conservan los registros de GitHub; "
                "vuelva a cargar el historial antes de reintentar."
            )
        payload = {
            "message": f"Guardar CSV persistente SIRAP: {file_name}",
            "content": base64.b64encode(contents.encode("utf-8")).decode("ascii"),
        }
        if expected_sha:
            payload["sha"] = expected_sha
        result = _request("PUT", path, payload)
        if not result or not result.get("content", {}).get("sha"):
            raise GitHubStorageError(f"GitHub no confirmó la escritura de {file_name}.")
        return result["content"]["sha"]
