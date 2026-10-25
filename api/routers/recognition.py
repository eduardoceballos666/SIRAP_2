"""Reconocimiento y Acceso: reconocer una placa, verificarla a mano y registrar operaciones."""

from __future__ import annotations

import base64
import uuid
from dataclasses import asdict

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from api import schemas
from api.jsonsafe import plain
from api.deps import current_user, get_barrier, get_config, get_store, get_pipeline, thresholds
from src.access_control import AccessDecision, decide_access
from src.data_processing import ImageLimits, ImageValidationError, load_image, normalize_plate
from src.storage import StorageError
from src.detection_export import append_detection, enrich_detection
from src.utils import ROOT_DIR, get_logger, now_local

logger = get_logger("sirap.api.recognition")
router = APIRouter(prefix="/api", tags=["Reconocimiento y Acceso"])

SAMPLES_DIR = ROOT_DIR / "data" / "samples"
SAMPLE_LABELS = {
    "garita3_PBA-8901.jpg": "Garita 3 · PBA-8901 (lista blanca)",
    "garita2_GBO-0429.jpg": "Garita 2 · GBO-0429 (lista restringida)",
    "garita1_GSA-1234.jpg": "Garita 1 · GSA-1234 (no registrada)",
    "garita3_PCD-5678_desenfocada.jpg": "Garita 3 · imagen desenfocada (verificación)",
}


def _decision_out(decision: AccessDecision) -> schemas.Decision:
    data = asdict(decision)
    data["permite_apertura"] = decision.permite_apertura
    data["vehiculo"] = plain(data.get("vehiculo"))
    return schemas.Decision(**data)


def _decide(plate: str | None, ocr_conf: float, det_conf: float | None) -> AccessDecision:
    ocr_threshold, det_threshold, distance = thresholds()
    return decide_access(plate, ocr_conf, get_store(), ocr_threshold, distance,
                         det_confidence=det_conf, det_threshold=det_threshold)


@router.get("/samples", summary="Imágenes de ejemplo precargadas")
def list_samples(_: dict = Depends(current_user)) -> list[dict[str, str]]:
    return [{"nombre": name, "etiqueta": label, "url": f"/api/samples/{name}"}
            for name, label in SAMPLE_LABELS.items() if (SAMPLES_DIR / name).exists()]


@router.get("/samples/{name}", summary="Descargar una imagen de ejemplo", include_in_schema=False)
def get_sample(name: str) -> FileResponse:
    if name not in SAMPLE_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ejemplo no encontrado.")
    return FileResponse(SAMPLES_DIR / name, media_type="image/jpeg")


@router.post("/recognize", response_model=schemas.RecognizeOut, summary="Reconocer la placa de una imagen")
def recognize(file: UploadFile = File(..., description="JPG, PNG o WEBP; máx. 10 MB"),
              _: dict = Depends(current_user)) -> schemas.RecognizeOut:
    """Detecta la placa con YOLO11-s, la lee con fast-plate-ocr, la normaliza y aplica la regla de acceso.

    No registra nada: el operador confirma después con ``POST /api/operations``.
    """
    cfg = get_config()["app"]
    try:
        image = load_image(file.file.read(), ImageLimits(cfg["max_tamano_imagen_mb"], cfg["min_lado_imagen_px"]))
    except ImageValidationError as exc:
        raise HTTPException(422, str(exc))
    pipeline = get_pipeline()
    try:
        rec = pipeline.recognize(image)
        decision = _decide(rec.plate, rec.ocr_confidence,
                           rec.det_confidence if pipeline.detector.is_model else None)
    except StorageError as exc:
        logger.exception("Almacenamiento CSV: %s", exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudieron consultar los archivos CSV.")
    crop_b64 = None
    if rec.crop is not None and rec.crop.size:
        ok, buffer = cv2.imencode(".jpg", cv2.cvtColor(rec.crop, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        crop_b64 = base64.b64encode(buffer.tobytes()).decode() if ok else None
    data = rec.as_dict()
    recognition = schemas.Recognition(
        plate=data["plate"], plate_raw=data["plate_raw"], ocr_confidence=data["ocr_confidence"],
        ocr_mean_confidence=data["ocr_mean_confidence"], det_confidence=data["det_confidence"], box=data["box"],
        detector=data["detector"], detector_is_model=pipeline.detector.is_model, timings_ms=data["timings_ms"],
        crop_jpeg_base64=crop_b64, image_width=int(image.shape[1]), image_height=int(image.shape[0]))
    return schemas.RecognizeOut(recognition=recognition, decision=_decision_out(decision))


@router.post("/plates/verify", response_model=schemas.VerifyOut, summary="Verificar una placa escrita a mano")
def verify_plate(body: schemas.VerifyIn, _: dict = Depends(current_user)) -> schemas.VerifyOut:
    plate = normalize_plate(body.placa)
    if not plate:
        raise HTTPException(422,
                            "Formato inválido: use 3 letras y 3 o 4 dígitos (ej.: PBA-8901).")
    ocr_threshold, det_threshold, _ = thresholds()
    decision = decide_access(plate, 1.0, get_store(), ocr_threshold, 0)
    return schemas.VerifyOut(placa=plate, decision=_decision_out(decision))


@router.post("/plates/register", status_code=201, summary="Registrar un camión detectado como nuevo")
def register_vehicle(body: schemas.VehicleIn, user: dict = Depends(current_user)) -> dict[str, str]:
    """Permite al operador completar el registro de un camión que no existe en la base."""
    plate = normalize_plate(body.placa)
    if not plate:
        raise HTTPException(422,
                            "Formato inválido: use 3 letras y 3 o 4 dígitos (ej.: PBA-8901).")
    required = {"marca": body.marca, "modelo": body.modelo, "color": body.color,
                "propietario": body.propietario or ""}
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        raise HTTPException(422, f"Complete los campos obligatorios: {', '.join(missing)}.")
    try:
        db = get_store()
        db.upsert_vehicle(plate, body.marca.strip(), body.modelo.strip(), body.color.strip(), "CAMION",
                          body.propietario.strip(), (body.transportista or "").strip() or None)
        db.set_authorization(plate, "BLANCA", "Autorizado al registrar el camión", None, user["usuario"])
    except (StorageError, ValueError) as exc:
        raise HTTPException(422, f"No se pudo registrar y autorizar el camión: {exc}")
    return {"placa": plate, "mensaje": f"El camión {plate} se registró y quedó autorizado."}


@router.post("/operations", response_model=schemas.OperationOut, status_code=201,
             summary="Registrar una operación (y abrir la barrera si corresponde)")
def register_operation(body: schemas.OperationIn, background_tasks: BackgroundTasks, user: dict = Depends(current_user)) -> schemas.OperationOut:
    """El resultado **no** se toma del cliente: se vuelve a calcular en el servidor con la placa final.

    - ``APERTURA_AUTOMATICA`` solo se acepta si la placa está AUTORIZADA.
    - ``APERTURA_MANUAL`` exige un motivo de al menos 10 caracteres.
    """
    plate = normalize_plate(body.placa_final) if body.placa_final else None
    if body.placa_final and not plate:
        raise HTTPException(422, "Placa final con formato inválido.")
    confidence = 1.0 if body.origen == "MANUAL" else (body.confianza_ocr or 0.0)
    decision = _decide(plate, confidence, None if body.origen == "MANUAL" else body.det_confidence)
    if body.accion == "APERTURA_AUTOMATICA" and not decision.permite_apertura:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"No se puede abrir automáticamente: el resultado es {decision.resultado}. "
                            "Use la apertura manual (contingencia) si corresponde.")
    if body.accion == "APERTURA_MANUAL" and len((body.motivo or "").strip()) < 10:
        raise HTTPException(422, "La apertura manual exige un motivo (mín. 10 caracteres).")
    barrier = get_barrier()
    opened = False
    if body.accion in ("APERTURA_AUTOMATICA", "APERTURA_MANUAL"):
        opened = barrier.open(body.garita, body.accion)
        if not opened:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                                "La barrera no confirmó la apertura. Use la apertura manual y avise a soporte.")
    final = plate if decision.resultado != "VERIFICACION_MANUAL" or body.origen == "MANUAL" else None
    try:
        get_store().log_operation(
            garita=body.garita, operador=user["nombre"], tipo_movimiento=body.tipo_movimiento,
            resultado=decision.resultado, accion=body.accion, placa_leida=body.placa_leida, placa_final=final,
            confianza_ocr=body.confianza_ocr, lista=decision.lista, motivo=(body.motivo or None),
            origen=body.origen, tiempo_ms=body.tiempo_ms)
    except (StorageError, ValueError) as exc:
        raise HTTPException(422, f"No se pudo registrar: {exc}")
    export_saved = False
    if body.origen == "DETECCION" and final:
        vehicle = decision.vehiculo or {}
        auth = vehicle.get("autorizacion") or {}
        row = {
            "event_id": str(uuid.uuid4()),
            "fecha_hora": now_local().isoformat(sep=" ", timespec="seconds"),
            "modelo_detector": "YOLO11-s" if body.det_confidence is not None else "",
            "camara": "",
            "garita": body.garita,
            "operador": user["nombre"],
            "tipo_movimiento": body.tipo_movimiento,
            "accion": body.accion,
            "origen": body.origen,
            "placa": final,
            "texto_ocr": body.placa_leida or final,
            "formato_valido": True,
            "confianza_ocr": body.confianza_ocr,
            "confianza_yolo": body.det_confidence,
            "disparador": "operacion_confirmada",
            "resultado_acceso": decision.resultado,
            "lista": decision.lista,
            "estado_vehiculo_planta": auth.get("lista", ""),
            "transportista": vehicle.get("transportista", ""),
            "marca_planta": vehicle.get("marca", ""),
            "modelo_planta": vehicle.get("modelo", ""),
            "color_planta": vehicle.get("color", ""),
            "tipo_vehiculo_planta": vehicle.get("tipo", ""),
            "propietario_registrado": vehicle.get("propietario", ""),
        }
        try:
            append_detection(row)
            export_saved = True
            background_tasks.add_task(enrich_detection, row["event_id"], final, row["marca_planta"])
        except Exception as exc:
            logger.exception("No se pudo guardar la detección en GitHub: %s", exc)
    messages = {"APERTURA_AUTOMATICA": "Operación registrada y barrera abierta.",
                "APERTURA_MANUAL": "Apertura manual registrada en el historial.",
                "RECHAZO": "Rechazo registrado; la barrera permanece cerrada.",
                "SOLO_REGISTRO": "Operación registrada sin abrir la barrera."}
    if body.origen == "DETECCION" and final:
        messages[body.accion] += (" Detección guardada en el CSV de GitHub; consultando SRI y propietario."
                                  if export_saved else
                                  " No se guardó en GitHub; revise la configuración del repositorio y el token.")
    return schemas.OperationOut(registrada=True, resultado=decision.resultado, accion=body.accion,
                                barrera_abierta=opened, barrera_simulada=getattr(barrier, "simulated", True),
                                mensaje=messages[body.accion])
