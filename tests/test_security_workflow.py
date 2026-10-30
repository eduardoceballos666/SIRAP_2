"""Pruebas aisladas de seguridad de garita; no requieren imágenes ni credenciales de demo."""

import uuid

import pytest
from fastapi import BackgroundTasks, HTTPException

from api import schemas
from api.routers import recognition
from src.access_control import AccessDecision
from src.storage import CsvStore, StorageError


@pytest.fixture
def store(tmp_path, monkeypatch):
    db = CsvStore(data_dir=tmp_path)
    monkeypatch.setattr(recognition, "get_store", lambda: db)
    return db


def vehicle(plate, **kwargs):
    return schemas.VehicleIn(
        placa=plate, marca="Chevrolet", modelo="NLR", color="Blanco",
        propietario="Empresa ejemplo", placa_confirmada=True, **kwargs
    )


@pytest.mark.parametrize("role", ["OPERADOR", "SUPERVISOR", "ADMINISTRADOR"])
def test_all_authenticated_roles_can_authorize_new_trucks(store, role):
    plate = f"ABC-{1000 + ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR'].index(role)}"
    user = {"usuario": role.lower(), "rol": role, "nombre": role}
    saved = recognition.register_vehicle(vehicle(plate, autorizar=True), user)
    assert saved["placa"] == plate
    assert store.get_authorization(plate)["lista"] == "BLANCA"
    assert store.get_authorization(plate)["creado_por"] == role.lower()
    assert store.get_vehicle(plate)["registrado_por"] == role.lower()


def test_registration_is_pending_without_explicit_authorization(store):
    user = {"usuario": "operador", "rol": "OPERADOR"}
    saved = recognition.register_vehicle(vehicle("XYZ-1234", autorizar=False), user)
    assert "pendiente de autorización" in saved["mensaje"]
    assert store.get_vehicle("XYZ-1234") is not None
    assert store.get_authorization("XYZ-1234") is None


def test_registration_requires_visual_confirmation(store):
    user = {"usuario": "operador", "rol": "OPERADOR"}
    payload = vehicle("XYZ-1234", autorizar=True).model_copy(update={"placa_confirmada": False})
    with pytest.raises(HTTPException) as exc:
        recognition.register_vehicle(payload, user)
    assert exc.value.status_code == 422
    assert store.get_vehicle("XYZ-1234") is None


def test_cannot_overwrite_existing_restricted_plate(store):
    store.upsert_vehicle("GBO-0429", "Original", "Modelo", "Rojo", "CAMION", "Titular", "")
    store.set_authorization("GBO-0429", "RESTRINGIDA", "No permitir", None, "admin")
    with pytest.raises(HTTPException) as exc:
        recognition.register_vehicle(
            vehicle("GBO-0429", autorizar=True),
            {"usuario": "operador", "rol": "OPERADOR"}
        )
    assert exc.value.status_code == 409
    assert store.get_vehicle("GBO-0429")["marca"] == "Original"
    assert store.get_authorization("GBO-0429")["lista"] == "RESTRINGIDA"


class Barrier:
    simulated = True

    def __init__(self, opened=True):
        self.opened = opened
        self.calls = 0

    def open(self, garita, accion):
        self.calls += 1
        return self.opened


def setup_operation(monkeypatch, barrier):
    monkeypatch.setattr(recognition, "get_barrier", lambda: barrier)
    monkeypatch.setattr(recognition, "_decide", lambda *args: AccessDecision(
        "AUTORIZADO", "AUTORIZADO", "LISTA BLANCA", "BLANCA"))
    return schemas.OperationIn(
        garita="Garita 3", tipo_movimiento="ENTRADA", accion="APERTURA_AUTOMATICA",
        placa_final="ABC-1234", origen="MANUAL", operacion_id=str(uuid.uuid4())
    )


def request_operation(body):
    return recognition.register_operation(
        body, BackgroundTasks(), {"usuario": "operador", "nombre": "Operador", "rol": "OPERADOR"}
    )


def test_csv_failure_blocks_barrier_before_open(store, monkeypatch):
    barrier = Barrier()
    body = setup_operation(monkeypatch, barrier)
    original = store._write

    def fail_csv(name, frame):
        if name == "operaciones":
            raise StorageError("CSV indisponible")
        return original(name, frame)

    monkeypatch.setattr(store, "_write", fail_csv)
    with pytest.raises(HTTPException) as exc:
        request_operation(body)
    assert exc.value.status_code == 503
    assert barrier.calls == 0


def test_success_writes_requested_then_confirmed(store, monkeypatch):
    barrier = Barrier()
    body = setup_operation(monkeypatch, barrier)
    events = []
    orig_log = store.log_operation
    orig_update = store.update_operation_state

    def log(*args, **kwargs):
        events.append(("write", kwargs["estado_barrera"]))
        return orig_log(*args, **kwargs)

    def update(*args):
        events.append(("update", args[1]))
        return orig_update(*args)

    def open_barrier(*args):
        events.append(("open", None))
        return True

    monkeypatch.setattr(store, "log_operation", log)
    monkeypatch.setattr(store, "update_operation_state", update)
    monkeypatch.setattr(barrier, "open", open_barrier)
    result = request_operation(body)
    assert events == [("write", "SOLICITADA"), ("open", None), ("update", "CONFIRMADA")]
    assert result.barrera_abierta is True
    assert result.estado_barrera == "CONFIRMADA"
    stored = store.operations()
    assert stored.iloc[0]["estado_barrera"] == "CONFIRMADA"
    assert stored.iloc[0]["operacion_id"] == str(body.operacion_id)


def test_failure_records_failed_open(store, monkeypatch):
    barrier = Barrier(opened=False)
    body = setup_operation(monkeypatch, barrier)
    with pytest.raises(HTTPException) as exc:
        request_operation(body)
    assert exc.value.status_code == 502
    assert barrier.calls == 1
    assert store.operations().iloc[0]["estado_barrera"] == "FALLIDA"


def test_final_write_failure_keeps_requested_audit_record(store, monkeypatch):
    barrier = Barrier()
    body = setup_operation(monkeypatch, barrier)
    monkeypatch.setattr(store, "update_operation_state", lambda *args: (_ for _ in ()).throw(
        StorageError("El almacenamiento final no responde")))
    with pytest.raises(HTTPException) as exc:
        request_operation(body)
    assert exc.value.status_code == 503
    assert barrier.calls == 1
    assert store.operations().iloc[0]["estado_barrera"] == "SOLICITADA"


def test_retried_operation_id_never_opens_twice(store, monkeypatch):
    barrier = Barrier()
    body = setup_operation(monkeypatch, barrier)
    assert request_operation(body).barrera_abierta
    with pytest.raises(HTTPException) as exc:
        request_operation(body)
    assert exc.value.status_code == 409
    assert barrier.calls == 1
    assert len(store.operations()) == 1


def test_physical_barrier_requires_private_backup(store, monkeypatch):
    class PhysicalBarrier(Barrier):
        simulated = False

    barrier = PhysicalBarrier()
    body = setup_operation(monkeypatch, barrier)
    monkeypatch.setattr(recognition, "durable_backup_configured", lambda: False)
    with pytest.raises(HTTPException) as exc:
        request_operation(body)
    assert exc.value.status_code == 503
    assert barrier.calls == 0
    assert store.operations().empty
