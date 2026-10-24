"""Administración: vehículos, listas de autorización, propietarios, garitas, usuarios y datos de demostración."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status

from api import schemas
from api.jsonsafe import plain
from api.deps import current_user, get_db, require_roles
from api.security import set_password
from src.data_processing import normalize_plate
from src.database import DatabaseError

router = APIRouter(prefix="/api/admin", tags=["Administración"])
admin_only = require_roles("ADMINISTRADOR")

Table = Literal["vehiculos", "propietarios", "autorizaciones", "garitas", "usuarios"]


def _plate(raw: str) -> str:
    plate = normalize_plate(raw)
    if not plate:
        raise HTTPException(422, "Placa inválida (3 letras y 3 o 4 dígitos).")
    return plate


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (DatabaseError, ValueError) as exc:
        raise HTTPException(422, str(exc))


@router.get("/{table}", summary="Contenido de una tabla")
def get_table(table: Table, _: dict = Depends(current_user)) -> list[dict[str, Any]]:
    df = get_db().table(table)
    return plain(df.to_dict(orient="records"))


@router.post("/vehiculos", status_code=201, summary="Crear o actualizar un vehículo")
def upsert_vehicle(body: schemas.VehicleIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(body.placa)
    _run(get_db().upsert_vehicle, plate, body.marca, body.modelo, body.color, body.tipo,
         body.propietario or None, body.transportista or None)
    return {"placa": plate, "mensaje": f"Vehículo {plate} guardado."}


@router.post("/autorizaciones", status_code=201, summary="Asignar lista blanca o restringida")
def set_authorization(body: schemas.AuthorizationIn, user: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(body.placa)
    _run(get_db().set_authorization, plate, body.lista, body.motivo, body.vigente_hasta, user["usuario"])
    return {"placa": plate, "mensaje": f"{plate} ahora está en la lista {body.lista}."}


@router.delete("/autorizaciones/{placa}", summary="Quitar una placa de todas las listas")
def revoke_authorization(placa: str, _: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(placa)
    _run(get_db().revoke_authorization, plate)
    return {"placa": plate, "mensaje": f"{plate} quedó sin autorización."}


@router.post("/garitas", status_code=201, summary="Agregar una garita")
def add_gate(body: schemas.GateIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    _run(get_db().add_garita, body.nombre, body.ubicacion)
    return {"mensaje": f"Garita {body.nombre} agregada."}


@router.post("/usuarios", status_code=201, summary="Agregar un usuario con contraseña")
def add_user(body: schemas.UserIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    db = get_db()
    _run(db.add_user, body.usuario, body.nombre, body.rol)
    _run(set_password, db, body.usuario, body.password)
    return {"mensaje": f"Usuario {body.usuario} creado."}


@router.post("/demo", summary="Generar operaciones de demostración (origen DEMO)")
def demo_generate(n: int = 120, _: dict = Depends(admin_only)) -> dict[str, Any]:
    n = max(1, min(int(n), 1000))
    return {"creadas": get_db().load_demo_history(n)}


@router.delete("/demo", summary="Borrar las operaciones de demostración")
def demo_clear(_: dict = Depends(admin_only)) -> dict[str, Any]:
    return {"borradas": get_db().clear_demo_history()}
