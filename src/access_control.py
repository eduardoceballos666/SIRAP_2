"""Regla de decisión de acceso y controlador de barrera de SIRAP.

Regla (en este orden):

1. Sin placa válida, confianza del detector menor que su umbral de decisión calibrado en *val*
   (0,30 para YOLO11-s) o confianza OCR menor que el umbral → **VERIFICACION_MANUAL**.
2. Placa en la lista **RESTRINGIDA** vigente → **DENEGADO**.
3. Placa en la lista **BLANCA** vigente → **AUTORIZADO**.
4. Placa no registrada pero a distancia ≤ 1 de una registrada (posible error del OCR)
   → **VERIFICACION_MANUAL**, sugiriendo la placa parecida.
5. Placa registrada sin autorización vigente, o no registrada → **NO_REGISTRADO**.

La decisión **nunca** abre la barrera por sí sola: la interfaz pide la acción del operador
(«Registrar y Abrir Barrera») y solo la habilita cuando el resultado es AUTORIZADO. La apertura
manual de contingencia exige un motivo y queda registrada en el historial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.data_processing import closest_plate, is_valid_plate
from src.utils import get_logger, get_secret

logger = get_logger("sirap.access")


@dataclass
class AccessDecision:
    """Resultado de evaluar una placa contra las listas."""

    resultado: str                       # AUTORIZADO | DENEGADO | NO_REGISTRADO | VERIFICACION_MANUAL
    titulo: str                          # texto grande de la tarjeta de resultado
    detalle: str                         # subtítulo (lista o motivo)
    lista: str | None = None             # BLANCA | RESTRINGIDA | None
    vehiculo: dict[str, Any] | None = None
    sugerencia: str | None = None        # placa registrada parecida (posible error de OCR)
    motivos: list[str] = field(default_factory=list)

    @property
    def permite_apertura(self) -> bool:
        """Solo un AUTORIZADO habilita la apertura normal de la barrera."""
        return self.resultado == "AUTORIZADO"


def decide_access(plate: str | None, ocr_confidence: float, db: Any,
                  confidence_threshold: float = 0.99, max_similar_distance: int = 1,
                  det_confidence: float | None = None, det_threshold: float = 0.0) -> AccessDecision:
    """Aplica la regla de decisión de SIRAP.

    Args:
        plate: placa normalizada ``XXX-0000`` (o ``None`` si no se pudo leer).
        ocr_confidence: confianza del OCR (0–1). Use 1.0 cuando el operador escribe la placa.
        db: objeto con ``get_vehicle(placa)`` y ``registered_plates()`` (``src.database.Database``).
        confidence_threshold: umbral bajo el cual se pide verificación manual.
        max_similar_distance: distancia de Levenshtein para sugerir una placa registrada parecida.
        det_confidence: confianza del detector entrenado (``None`` si la placa se escribió a mano o se
            usó el localizador de respaldo, cuyo puntaje no es una probabilidad).
        det_threshold: umbral de decisión del detector (``conf_decision`` calibrado en *val*).

    Returns:
        La ``AccessDecision`` correspondiente.
    """
    if not plate or not is_valid_plate(plate):
        return AccessDecision("VERIFICACION_MANUAL", "VERIFICACIÓN MANUAL", "PLACA NO LEGIBLE",
                              motivos=["No se obtuvo una placa con formato válido (XXX-0000)."])

    vehicle = db.get_vehicle(plate)
    if det_confidence is not None and det_confidence < det_threshold:
        return AccessDecision("VERIFICACION_MANUAL", "VERIFICACIÓN MANUAL", "DETECCIÓN DUDOSA", vehiculo=vehicle,
                              motivos=[f"Confianza del detector {det_confidence:.0%} < umbral {det_threshold:.0%}."])
    low_confidence = ocr_confidence < confidence_threshold
    if low_confidence:
        decision = AccessDecision("VERIFICACION_MANUAL", "VERIFICACIÓN MANUAL", "CONFIANZA OCR BAJA",
                                  vehiculo=vehicle,
                                  motivos=[f"Confianza OCR {ocr_confidence:.0%} < umbral {confidence_threshold:.0%}."])
        if vehicle is None:
            decision.sugerencia = _suggest(plate, db, max_similar_distance)
        return decision

    if vehicle is not None:
        auth = vehicle.get("autorizacion")
        if auth and auth.get("lista") == "RESTRINGIDA":
            return AccessDecision("DENEGADO", "ACCESO DENEGADO", "LISTA RESTRINGIDA", "RESTRINGIDA", vehicle,
                                  motivos=[auth.get("motivo") or "Placa en lista restringida."])
        if auth and auth.get("lista") == "BLANCA":
            return AccessDecision("AUTORIZADO", "ACCESO AUTORIZADO", "LISTA BLANCA", "BLANCA", vehicle,
                                  motivos=[auth.get("motivo") or "Placa en lista blanca vigente."])
        return AccessDecision("NO_REGISTRADO", "SIN AUTORIZACIÓN", "REGISTRADO SIN PERMISO VIGENTE", None, vehicle,
                              motivos=["El vehículo existe pero no tiene una autorización vigente."])

    suggestion = _suggest(plate, db, max_similar_distance)
    if suggestion:
        return AccessDecision("VERIFICACION_MANUAL", "VERIFICACIÓN MANUAL", f"¿QUISO DECIR {suggestion}?",
                              sugerencia=suggestion,
                              motivos=[f"La lectura difiere en un carácter de la placa registrada {suggestion}."])
    return AccessDecision("NO_REGISTRADO", "ACCESO NO REGISTRADO", "PLACA NO REGISTRADA",
                          motivos=["La placa no está en la base de vehículos."])


def _suggest(plate: str, db: Any, max_distance: int) -> str | None:
    candidate, distance = closest_plate(plate, db.registered_plates())
    return candidate if candidate and 0 < distance <= max_distance else None


# --------------------------------------------------------------------------------------------
# Barrera
# --------------------------------------------------------------------------------------------

class BarrierController(Protocol):
    """Interfaz de un controlador de barrera."""

    def open(self, garita: str, motivo: str) -> bool:  # pragma: no cover - protocolo
        """Envía la orden de apertura; devuelve ``True`` si el dispositivo la confirmó."""


class SimulatedBarrier:
    """Barrera simulada: registra la orden en el log pero no mueve ningún dispositivo."""

    simulated = True

    def open(self, garita: str, motivo: str) -> bool:
        logger.info("[SIMULADA] Apertura de barrera en %s (%s)", garita, motivo)
        return True


class HttpBarrier:
    """Envía la orden a un controlador HTTP (relé/PLC) protegido con un token.

    Variables: ``BARRERA_URL`` (p. ej. ``https://garita3.local/abrir``) y ``BARRERA_TOKEN``.
    """

    simulated = False

    def __init__(self, url: str, token: str, timeout_s: float = 3.0):
        if not url.startswith("https://"):
            raise ValueError("BARRERA_URL debe usar HTTPS.")
        self.url, self.token, self.timeout_s = url, token, timeout_s

    def open(self, garita: str, motivo: str) -> bool:
        import json
        import urllib.request

        request = urllib.request.Request(
            self.url, data=json.dumps({"garita": garita, "motivo": motivo}).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:  # noqa: S310
                return 200 <= response.status < 300
        except OSError as exc:
            logger.error("La barrera de %s no respondió: %s", garita, exc)
            return False


def barrier_from_config(config: dict[str, Any]) -> BarrierController:
    """Crea la barrera según ``config['barrera']['modo']`` (``simulada`` por defecto)."""
    cfg = config.get("barrera", {})
    if cfg.get("modo") == "http":
        url, token = get_secret("BARRERA_URL"), get_secret("BARRERA_TOKEN")
        if url and token:
            return HttpBarrier(url, token, cfg.get("timeout_s", 3))
        logger.warning("Modo de barrera http sin BARRERA_URL/BARRERA_TOKEN: se usa la barrera simulada.")
    return SimulatedBarrier()
