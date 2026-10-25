"""Modelos Pydantic de entrada y salida de la API."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Resultado = Literal["AUTORIZADO", "DENEGADO", "NO_REGISTRADO", "VERIFICACION_MANUAL"]
Accion = Literal["APERTURA_AUTOMATICA", "APERTURA_MANUAL", "SOLO_REGISTRO", "RECHAZO"]
Movimiento = Literal["ENTRADA", "SALIDA"]
Rol = Literal["OPERADOR", "SUPERVISOR", "ADMINISTRADOR"]


class LoginIn(BaseModel):
    usuario: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class User(BaseModel):
    usuario: str
    nombre: str
    rol: Rol


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class Decision(BaseModel):
    resultado: Resultado
    titulo: str
    detalle: str
    lista: Optional[str] = None
    vehiculo: Optional[dict[str, Any]] = None
    sugerencia: Optional[str] = None
    motivos: list[str] = []
    permite_apertura: bool


class Recognition(BaseModel):
    plate: Optional[str]
    plate_raw: str
    ocr_confidence: float
    ocr_mean_confidence: float
    det_confidence: float
    box: Optional[list[float]]
    detector: str
    detector_is_model: bool
    timings_ms: dict[str, float]
    crop_jpeg_base64: Optional[str] = None
    image_width: int
    image_height: int


class RecognizeOut(BaseModel):
    recognition: Recognition
    decision: Decision


class VerifyIn(BaseModel):
    placa: str = Field(min_length=3, max_length=12)


class VerifyOut(BaseModel):
    placa: str
    decision: Decision


class OperationIn(BaseModel):
    garita: str = Field(min_length=1, max_length=60)
    tipo_movimiento: Movimiento
    accion: Accion
    placa_leida: Optional[str] = Field(default=None, max_length=16)
    placa_final: Optional[str] = Field(default=None, max_length=12)
    confianza_ocr: Optional[float] = Field(default=None, ge=0, le=1)
    det_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    motivo: Optional[str] = Field(default=None, max_length=250)
    origen: Literal["DETECCION", "MANUAL"] = "DETECCION"
    tiempo_ms: Optional[float] = None


class OperationOut(BaseModel):
    registrada: bool
    resultado: Resultado
    accion: Accion
    barrera_abierta: bool
    barrera_simulada: bool
    mensaje: str


class VehicleIn(BaseModel):
    placa: str = Field(min_length=3, max_length=12)
    marca: str = ""
    modelo: str = ""
    color: str = ""
    tipo: Literal["LIVIANO", "CAMION", "MOTO", "OTRO"] = "LIVIANO"
    propietario: Optional[str] = None
    transportista: Optional[str] = None


class AdminVehicleIn(BaseModel):
    placa: str = Field(min_length=3, max_length=12)
    marca: str = Field(min_length=1, max_length=80)
    modelo: str = Field(min_length=1, max_length=80)
    color: str = Field(min_length=1, max_length=40)
    tipo: Literal["LIVIANO", "CAMION", "MOTO", "OTRO"]
    propietario: str = Field(min_length=1, max_length=120)
    transportista: str = Field(min_length=1, max_length=120)


class AuthorizationIn(BaseModel):
    placa: str = Field(min_length=3, max_length=12)
    lista: Literal["BLANCA", "RESTRINGIDA"]
    motivo: str = Field(min_length=1, max_length=250)
    vigente_hasta: date


class BulkTruckAuthorizationIn(BaseModel):
    placas: list[str] = Field(min_length=1, max_length=100)
    lista: Optional[Literal["BLANCA", "RESTRINGIDA"]] = None


class GateIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    ubicacion: str = ""


class UserIn(BaseModel):
    usuario: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    nombre: str = Field(min_length=1, max_length=120)
    rol: Rol
    password: str = Field(min_length=8, max_length=128)
