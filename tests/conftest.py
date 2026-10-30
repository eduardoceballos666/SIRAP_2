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


def seed_test_vehicles(store):
    """Datos totalmente ficticios, solo para pruebas: nunca cargar en GitHub privado."""
    store.upsert_vehicle(
        "PBA-8901", "Toyota", "Hilux", "Blanco", "CAMION", "Juan Pérez", "Transportista de prueba"
    )
    store.upsert_vehicle(
        "GBO-0429", "Chevrolet", "NLR", "Rojo", "CAMION", "Empresa de prueba", "Transportista de prueba"
    )
    store.set_authorization("PBA-8901", "BLANCA", "Acceso de prueba", None, "test-admin")
    store.set_authorization("GBO-0429", "RESTRINGIDA", "Restricción de prueba", None, "test-admin")


@pytest.fixture()
def seeded_db(db):
    """La prueba del modelo necesita datos; otras pruebas reciben una BD vacía."""
    seed_test_vehicles(db)
    return db
