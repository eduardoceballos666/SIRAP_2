"""Configuración común de pytest: raíz del repositorio y almacenamiento CSV temporal."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def db(tmp_path):
    """Archivos CSV aislados para cada prueba."""
    from src.storage import CsvStore

    return CsvStore(data_dir=tmp_path)
