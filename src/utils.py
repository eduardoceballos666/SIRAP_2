"""Funciones auxiliares de SIRAP: configuración, rutas, secretos, logging y métricas guardadas.

Todo lo que dependa del entorno (rutas absolutas, llaves, DSN) se resuelve aquí para que el
resto del código use rutas relativas a la raíz del repositorio y no tenga valores fijos.
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

import yaml

#: Raíz del repositorio (carpeta que contiene ``src/``).
ROOT_DIR: Path = Path(__file__).resolve().parents[1]
CONFIG_PATH: Path = ROOT_DIR / "config" / "config.yaml"


def resolve_path(relative: str | os.PathLike) -> Path:
    """Convierte una ruta relativa a la raíz del repositorio en una ruta absoluta.

    Args:
        relative: ruta relativa (p. ej. ``"models/best_model.onnx"``) o absoluta.

    Returns:
        La ruta absoluta correspondiente.
    """
    path = Path(relative)
    return path if path.is_absolute() else ROOT_DIR / path


@lru_cache(maxsize=4)
def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    """Lee ``config/config.yaml`` (o la ruta indicada) y devuelve un diccionario.

    Args:
        path: ruta alternativa al archivo de configuración.

    Returns:
        La configuración como diccionario anidado.

    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si el YAML está mal formado.
    """
    config_path = resolve_path(path) if path else CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")
    try:
        with config_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"config.yaml mal formado: {exc}") from exc
    return data


def get_secret(name: str, default: str | None = None) -> str | None:
    """Lee un secreto de ``st.secrets`` (Streamlit), de Colab o de una variable de entorno.

    El orden es: variable de entorno → ``st.secrets`` → ``google.colab.userdata``.
    Nunca se escriben llaves en el código ni en ``config.yaml``.

    Args:
        name: nombre del secreto (p. ej. ``"PG_DSN"``).
        default: valor si no se encuentra.

    Returns:
        El valor del secreto o ``default``.
    """
    value = os.environ.get(name)
    if value:
        return value
    try:  # Streamlit
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001 — sin secrets.toml Streamlit lanza distintas excepciones
        pass
    try:  # Google Colab
        from google.colab import userdata  # type: ignore

        value = userdata.get(name)
        if value:
            return value
    except Exception:  # noqa: BLE001
        pass
    return default


def get_logger(name: str = "sirap") -> logging.Logger:
    """Devuelve un logger configurado una sola vez (consola + archivo de la configuración).

    Args:
        name: nombre del logger.

    Returns:
        Un ``logging.Logger`` listo para usar.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    try:
        cfg = load_config().get("logging", {})
    except (FileNotFoundError, ValueError):
        cfg = {}
    logger.setLevel(cfg.get("nivel", "INFO"))
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    log_file = cfg.get("archivo")
    if log_file:
        try:
            path = resolve_path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:  # p. ej. sistema de archivos de solo lectura
            logger.warning("No se pudo abrir el archivo de log %s; se registra solo en consola.", log_file)
    logger.propagate = False
    return logger


def now_local() -> datetime:
    """Fecha y hora actuales en la zona de la configuración (America/Guayaquil), sin tzinfo.

    Streamlit Community Cloud corre en UTC; sin esto el historial quedaría 5 horas adelantado.
    """
    try:
        tz = ZoneInfo(load_config()["app"].get("zona_horaria", "America/Guayaquil"))
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("America/Guayaquil")
    return datetime.now(tz).replace(tzinfo=None)


@contextmanager
def timer() -> Iterator[dict[str, float]]:
    """Mide el tiempo de un bloque en milisegundos.

    Ejemplo::

        with timer() as t:
            hacer_algo()
        print(t["ms"])
    """
    result: dict[str, float] = {"ms": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["ms"] = (time.perf_counter() - start) * 1000.0


def load_json(relative: str | os.PathLike) -> dict[str, Any] | None:
    """Lee un JSON relativo a la raíz; devuelve ``None`` si no existe o está mal formado."""
    path = resolve_path(relative)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_json(data: dict[str, Any], relative: str | os.PathLike) -> Path:
    """Guarda un diccionario como JSON (UTF-8, indentado) y devuelve la ruta."""
    path = resolve_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
