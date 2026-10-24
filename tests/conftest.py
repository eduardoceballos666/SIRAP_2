"""Configuración común de pytest: raíz del repo en sys.path y base SQLite temporal."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def db(tmp_path):
    """Base SQLite nueva con los datos de demostración, en una carpeta temporal."""
    from src.database import Database

    return Database(sqlite_path=tmp_path / "test.db")
