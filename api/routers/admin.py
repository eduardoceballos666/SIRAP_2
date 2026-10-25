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
    if not body.motivo.strip():
        raise HTTPException(422, "El motivo es obligatorio.")
    _run(get_db().set_authorization, plate, body.lista, body.motivo.strip(), body.vigente_hasta, user["usuario"])
    return {"placa": plate, "mensaje": f"{plate} ahora está en la lista {body.lista}."}


@router.put("/autorizaciones/{placa}", summary="Actualizar un registro existente de autorización")
def update_authorization(placa: str, body: schemas.AuthorizationIn,
                         user: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(placa)
    if _plate(body.placa) != plate:
        raise HTTPException(422, "La placa del formulario no coincide con la placa que se actualiza.")
    if not body.motivo.strip():
        raise HTTPException(422, "El motivo es obligatorio.")
    _run(get_db().update_authorization, plate, body.lista, body.motivo.strip(),
         body.vigente_hasta, user["usuario"])
    return {"placa": plate, "mensaje": f"Autorización de {plate} actualizada en la lista {body.lista}."}


@router.delete("/autorizaciones/{placa}", summary="Quitar una placa de todas las listas")
def revoke_authorization(placa: str, _: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(placa)
    _run(get_db().revoke_authorization, plate)
    return {"placa": plate, "mensaje": f"{plate} quedó sin autorización."}


@router.post("/autorizaciones/seleccionadas", summary="Autorizar o quitar autorización a camiones seleccionados")
def update_selected_truck_authorizations(body: schemas.BulkTruckAuthorizationIn,
                                         user: dict = Depends(admin_only)) -> dict[str, str | int]:
    plates = list(dict.fromkeys(_plate(raw) for raw in body.placas))
    db = get_db()
    vehicles = {plate: db.get_vehicle(plate) for plate in plates}
    missing = [plate for plate, vehicle in vehicles.items() if vehicle is None]
    non_trucks = [plate for plate, vehicle in vehicles.items()
                  if vehicle is not None and vehicle.get("tipo") != "CAMION"]
    if missing or non_trucks:
        invalid = missing + non_trucks
        raise HTTPException(422, f"Solo se pueden cambiar camiones registrados. Revise: {', '.join(invalid)}.")
    try:
        for plate in plates:
            if body.lista:
                db.set_authorization(plate, body.lista,
                                     "Autorización aplicada desde Administración", None, user["usuario"])
            else:
                db.revoke_authorization(plate)
    except (DatabaseError, ValueError) as exc:
        raise HTTPException(422, f"No se pudo actualizar la autorización: {exc}")
    action = f"lista {body.lista}" if body.lista else "sin autorización"
    return {"actualizadas": len(plates),
            "mensaje": f"{len(plates)} camión(es) actualizado(s): {action}."}


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
