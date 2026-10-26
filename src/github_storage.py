"""Persistencia privada de las tablas CSV de SIRAP en GitHub."""

from __future__ import annotations

import base64
import functools
import os
import re
import tempfile
import threading
from pathlib import Path
from urllib.parse import quote

import requests

from src.utils import get_logger, get_secret

logger = get_logger("sirap.github_storage")
_API = "https://api.github.com"
_DEFAULT_REPOSITORY = "eduardoceballos666/SIRAP_datos_privados"
_LOCK = threading.RLock()


@functools.lru_cache(maxsize=1)
def _config() -> tuple[str, str, str, str] | None:
    token = get_secret("GITHUB_TOKEN")
    repository = get_secret("GITHUB_DATA_REPOSITORY", _DEFAULT_REPOSITORY) or _DEFAULT_REPOSITORY
    if not token:
        logger.warning(
            "Respaldo CSV de SIRAP desactivado: falta el secreto GITHUB_TOKEN en Hugging Face."
        )
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise RuntimeError("GITHUB_DATA_REPOSITORY debe tener el formato propietario/repositorio.")
    branch = get_secret("GITHUB_DATA_BRANCH", "main") or "main"
    root = (get_secret("GITHUB_STORAGE_DATA_PATH", "data/processed") or "data/processed").strip("/")
    if not root or any(part in {".", ".."} for part in root.split("/")):
        raise RuntimeError("GITHUB_STORAGE_DATA_PATH no es una ruta válida.")
    return token, repository, branch, root


def is_configured() -> bool:
    return _config() is not None


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@functools.lru_cache(maxsize=4)
def _ensure_private(repository: str, token: str) -> None:
    response = requests.get(f"{_API}/repos/{repository}", headers=_headers(token), timeout=15)
    response.raise_for_status()
    if response.json().get("private") is not True:
        raise RuntimeError("El repositorio de datos debe ser privado; no se guardó información.")


def _url(repository: str, remote_path: str) -> str:
    return f"{_API}/repos/{repository}/contents/{quote(remote_path, safe='/')}"


def _read_remote(token: str, repository: str, branch: str, remote_path: str) -> tuple[bytes | None, str | None]:
    response = requests.get(
        _url(repository, remote_path), headers=_headers(token), params={"ref": branch}, timeout=20
    )
    if response.status_code == 404:
        return None, None
    response.raise_for_status()
    item = response.json()
    encoded = item.get("content")
    if item.get("encoding") == "base64" and encoded:
        return base64.b64decode(encoded), item.get("sha")
    download_url = item.get("download_url")
    if download_url:
        downloaded = requests.get(download_url, headers=_headers(token), timeout=30)
        downloaded.raise_for_status()
        return downloaded.content, item.get("sha")
    raise RuntimeError(f"GitHub no devolvió el contenido de {remote_path}.")


def restore_csv_tables(data_dir: Path, table_names) -> set[str]:
    """Restaura las tablas remotas antes de que CsvStore cree archivos vacíos."""
    config = _config()
    if not config:
        return set()
    token, repository, branch, root = config
    _ensure_private(repository, token)
    restored: set[str] = set()
    with _LOCK:
        for name in table_names:
            raw, _ = _read_remote(token, repository, branch, f"{root}/{name}.csv")
            if raw is None:
                continue
            target = data_dir / f"{name}.csv"
            fd, temp_name = tempfile.mkstemp(dir=data_dir, suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                os.replace(temp_name, target)
            except OSError:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
                raise
            restored.add(name)
    return restored


def persist_csv_table(name: str, content: bytes) -> bool:
    """Guarda una tabla CSV en la rama privada de datos."""
    config = _config()
    if not config:
        return False
    token, repository, branch, root = config
    _ensure_private(repository, token)
    remote_path = f"{root}/{name}.csv"
    with _LOCK:
        for attempt in range(3):
            _, sha = _read_remote(token, repository, branch, remote_path)
            payload = {
                "message": f"Actualizar tabla SIRAP: {name}",
                "branch": branch,
                "content": base64.b64encode(content).decode("ascii"),
            }
            if sha:
                payload["sha"] = sha
            response = requests.put(
                _url(repository, remote_path), headers=_headers(token), json=payload, timeout=30
            )
            if response.status_code in (200, 201):
                return True
            if response.status_code not in (409, 422) or attempt == 2:
                response.raise_for_status()
            logger.warning("Conflicto al guardar %s en GitHub; reintentando.", remote_path)
    raise RuntimeError(f"No se pudo guardar {remote_path} tras varios intentos.")
