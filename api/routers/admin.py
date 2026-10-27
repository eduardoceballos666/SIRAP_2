"""Administración: vehículos, listas de autorización, propietarios, garitas, usuarios y datos de demostración."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status

from api import schemas
from api.jsonsafe import plain
from api.deps import current_user, get_store, require_roles
from api.security import set_password
from src.data_processing import normalize_plate
from src.storage import StorageError

router = APIRouter(prefix="/api/admin", tags=["Administración"])
admin_only = require_roles("ADMINISTRADOR")

Table = Literal["vehiculos", "propietarios", "autorizaciones", "garitas", "usuarios"]


def _plate(raw: str) -> str:
    plate = normalize_plate(raw)
    if not plate:
        raise HTTPException(422, "Placa inválida (3 letras y 3 o 4 dígitos).")
    return plate


def _active(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "si", "sí", "yes"}


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (StorageError, ValueError) as exc:
        raise HTTPException(422, str(exc))


@router.get("/{table}", summary="Contenido de una tabla")
def get_table(table: Table, _: dict = Depends(current_user)) -> list[dict[str, Any]]:
    df = get_store().table(table)
    return plain(df.to_dict(orient="records"))


@router.post("/vehiculos", status_code=201, summary="Crear o actualizar un vehículo")
def upsert_vehicle(body: schemas.AdminVehicleIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(body.placa)
    fields = [body.marca, body.modelo, body.color, body.propietario, body.transportista]
    if any(not value.strip() for value in fields):
        raise HTTPException(422, "Complete todos los campos obligatorios del vehículo.")
    db = get_store()
    updating = _run(db.get_vehicle, plate) is not None
    _run(db.upsert_vehicle, plate, body.marca.strip(), body.modelo.strip(), body.color.strip(), body.tipo,
         body.propietario.strip(), body.transportista.strip())
    message = "Registro actualizado correctamente." if updating else f"Vehículo {plate} guardado correctamente."
    return {"placa": plate, "mensaje": message}


@router.post("/autorizaciones", status_code=201, summary="Asignar lista blanca o restringida")
def set_authorization(body: schemas.AuthorizationIn, user: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(body.placa)
    if not body.motivo.strip():
        raise HTTPException(422, "El motivo es obligatorio.")
    _run(get_store().set_authorization, plate, body.lista, body.motivo.strip(), body.vigente_hasta, user["usuario"])
    return {"placa": plate, "mensaje": f"{plate} ahora está en la lista {body.lista}."}


@router.put("/autorizaciones/{placa}", summary="Actualizar un registro existente de autorización")
def update_authorization(placa: str, body: schemas.AuthorizationIn,
                         user: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(placa)
    if _plate(body.placa) != plate:
        raise HTTPException(422, "La placa del formulario no coincide con la placa que se actualiza.")
    if not body.motivo.strip():
        raise HTTPException(422, "El motivo es obligatorio.")
    _run(get_store().update_authorization, plate, body.lista, body.motivo.strip(),
         body.vigente_hasta, user["usuario"])
    return {"placa": plate, "mensaje": f"Autorización de {plate} actualizada en la lista {body.lista}."}


@router.delete("/autorizaciones/{placa}", summary="Quitar una placa de todas las listas")
def revoke_authorization(placa: str, _: dict = Depends(admin_only)) -> dict[str, str]:
    plate = _plate(placa)
    _run(get_store().revoke_authorization, plate)
    return {"placa": plate, "mensaje": f"{plate} quedó sin autorización."}


@router.post("/autorizaciones/seleccionadas", summary="Autorizar o quitar autorización a camiones seleccionados")
def update_selected_truck_authorizations(body: schemas.BulkTruckAuthorizationIn,
                                         user: dict = Depends(admin_only)) -> dict[str, str | int]:
    plates = list(dict.fromkeys(_plate(raw) for raw in body.placas))
    db = get_store()
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
    except (StorageError, ValueError) as exc:
        raise HTTPException(422, f"No se pudo actualizar la autorización: {exc}")
    action = f"lista {body.lista}" if body.lista else "sin autorización"
    return {"actualizadas": len(plates),
            "mensaje": f"{len(plates)} camión(es) actualizado(s): {action}."}


@router.post("/garitas", status_code=201, summary="Agregar una garita")
def add_gate(body: schemas.GateIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    nombre, ubicacion = body.nombre.strip(), body.ubicacion.strip()
    if not nombre or not ubicacion:
        raise HTTPException(422, "Complete el nombre y la ubicación antes de agregar la garita.")
    _run(get_store().add_garita, nombre, ubicacion)
    return {"mensaje": "Garita " + nombre + " agregada."}


@router.post("/garitas/estado", summary="Activar o inactivar garitas seleccionadas")
def set_gates_state(body: schemas.BulkGateStateIn,
                    _: dict = Depends(admin_only)) -> dict[str, str | int]:
    nombres = list(dict.fromkeys(nombre.strip() for nombre in body.nombres))
    if not nombres or any(not nombre for nombre in nombres):
        raise HTTPException(422, "Seleccione una o más garitas válidas.")
    updated = _run(get_store().set_garitas_active, nombres, body.activa)
    action = "activada(s)" if body.activa else "inactivada(s)"
    return {"actualizadas": updated, "mensaje": str(updated) + " garita(s) " + action + "."}


@router.post("/usuarios", status_code=201, summary="Agregar un usuario con contraseña")
def add_user(body: schemas.UserIn, _: dict = Depends(admin_only)) -> dict[str, str]:
    usuario = body.usuario.strip()
    nombre = body.nombre.strip()
    if not usuario or not nombre or not body.password.strip():
        raise HTTPException(422, "Complete todos los campos obligatorios del usuario.")
    db = get_store()
    _run(db.add_user, usuario, nombre, body.rol)
    _run(set_password, db, usuario, body.password)
    return {"mensaje": "Usuario " + usuario + " creado."}


@router.put("/usuarios/{usuario}", summary="Actualizar nombre y rol de un usuario")
def update_user(usuario: str, body: schemas.AdminUserUpdateIn,
                actor: dict = Depends(admin_only)) -> dict[str, str]:
    target = usuario.strip()
    if not target:
        raise HTTPException(422, "Seleccione un usuario válido.")
    db = get_store()
    users = _run(db.table, "usuarios")
    target_rows = users[users["usuario"].astype(str) == target]
    if target_rows.empty:
        raise HTTPException(404, "El usuario seleccionado no existe.")
    target_row = target_rows.iloc[-1]
    if target_row["rol"] == "ADMINISTRADOR" and body.rol != "ADMINISTRADOR" and _active(target_row["activo"]):
        active_admins = int(((users["rol"] == "ADMINISTRADOR") & users["activo"].map(_active)).sum())
        if active_admins <= 1:
            raise HTTPException(409, "No se puede cambiar el rol del último usuario Administrador activo.")
    _run(db.update_user, target, body.nombre, body.rol)
    return {"usuario": target, "mensaje": "Datos del usuario " + target + " actualizados."}


@router.put("/usuarios/{usuario}/password", summary="Restablecer contraseña de un usuario")
def reset_user_password(usuario: str, body: schemas.AdminPasswordResetIn,
                        _: dict = Depends(admin_only)) -> dict[str, str]:
    target = usuario.strip()
    if not target:
        raise HTTPException(422, "Seleccione un usuario válido.")
    users = _run(get_store().table, "usuarios")
    if not (users["usuario"].astype(str) == target).any():
        raise HTTPException(404, "El usuario seleccionado no existe.")
    _run(set_password, get_store(), target, body.password)
    return {"usuario": target, "mensaje": "Contraseña de " + target + " restablecida correctamente."}


@router.delete("/usuarios/{usuario}", summary="Inactivar un usuario")
def inactivate_user(usuario: str, actor: dict = Depends(admin_only)) -> dict[str, str]:
    target = usuario.strip()
    if not target:
        raise HTTPException(422, "Seleccione un usuario válido.")
    if target == actor["usuario"]:
        raise HTTPException(409, "No puede inactivar su propio usuario.")

    db = get_store()
    users = _run(db.table, "usuarios")
    target_rows = users[users["usuario"].astype(str) == target]
    if target_rows.empty:
        raise HTTPException(404, "El usuario seleccionado no existe.")
    target_row = target_rows.iloc[-1]
    if not _active(target_row["activo"]):
        raise HTTPException(409, "El usuario ya está inactivo.")
    if target_row["rol"] == "ADMINISTRADOR":
        active_admins = users[
            (users["rol"] == "ADMINISTRADOR") & users["activo"].map(_active)
        ]
        if len(active_admins) <= 1:
            raise HTTPException(409, "No se puede inactivar al último usuario Administrador activo.")

    _run(db.deactivate_user, target)
    return {"usuario": target, "mensaje": "Usuario " + target + " inactivado."}


@router.post("/usuarios/estado", summary="Activar o inactivar usuarios seleccionados")
def set_users_state(body: schemas.BulkUserStateIn,
                    actor: dict = Depends(admin_only)) -> dict[str, str | int]:
    usuarios = list(dict.fromkeys(usuario.strip() for usuario in body.usuarios))
    if not usuarios or any(not usuario for usuario in usuarios):
        raise HTTPException(422, "Seleccione uno o más usuarios válidos.")

    db = get_store()
    users = _run(db.table, "usuarios")
    selected = users[users["usuario"].astype(str).isin(usuarios)]
    found = set(selected["usuario"].astype(str).tolist())
    missing = [usuario for usuario in usuarios if usuario not in found]
    if missing:
        raise HTTPException(404, "No se encontraron estos usuarios: " + ", ".join(missing) + ".")

    if not body.activo:
        if actor["usuario"] in usuarios:
            raise HTTPException(409, "No puede inactivar su propio usuario.")
        active_admins = int(
            ((users["rol"] == "ADMINISTRADOR") & users["activo"].map(_active)).sum()
        )
        selected_admins = int(
            ((selected["rol"] == "ADMINISTRADOR") & selected["activo"].map(_active)).sum()
        )
        if active_admins - selected_admins <= 0:
            raise HTTPException(409, "No se puede inactivar al último usuario Administrador activo.")

    updated = _run(db.set_users_active, usuarios, body.activo)
    action = "activado(s)" if body.activo else "inactivado(s)"
    return {"actualizados": updated, "mensaje": str(updated) + " usuario(s) " + action + "."}


@router.post("/demo", summary="Generar operaciones de demostración (origen DEMO)")
def demo_generate(n: int = 120, _: dict = Depends(admin_only)) -> dict[str, Any]:
    n = max(1, min(int(n), 1000))
    return {"creadas": get_store().load_demo_history(n)}


@router.delete("/demo", summary="Borrar las operaciones de demostración")
def demo_clear(_: dict = Depends(admin_only)) -> dict[str, Any]:
    return {"borradas": get_store().clear_demo_history()}
