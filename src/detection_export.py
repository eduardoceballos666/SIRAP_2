"""Exporta operaciones confirmadas a un CSV de un repositorio GitHub privado
y enriquece cada fila con consultas públicas del SRI y EcuadorLegalOnline.
"""

from __future__ import annotations

import base64
import csv
import io
import json
import re
import threading
import time
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import quote

import requests

from src.utils import get_logger, get_secret, now_local

logger = get_logger("sirap.detection_export")

CSV_FIELDS = (
    "event_id", "fecha_hora", "modelo_detector", "corrida", "video", "camara", "garita",
    "operador", "tipo_movimiento", "accion", "origen", "track_id", "frame_index", "segundo_video",
    "placa", "texto_ocr", "formato_valido", "confianza_ocr", "confianza_yolo",
    "area_deteccion_px", "disparador", "resultado_acceso", "lista",
    "estado_vehiculo_planta", "transportista", "marca_planta", "modelo_planta", "color_planta",
    "tipo_vehiculo_planta", "propietario_registrado", "marca_coincide_sri",
    "sri_consultado_en", "sri_encontrado", "sri_error", "sri_codigo_vehiculo", "sri_camv_cpn",
    "sri_marca", "sri_modelo", "sri_anio_modelo", "sri_pais", "sri_clase", "sri_servicio",
    "sri_canton", "sri_estado_exoneracion", "sri_ultimo_anio_pagado", "sri_matricula_al_dia",
    "sri_prohibido_enajenar", "sri_rubros_pendientes", "sri_total_pendiente", "sri_alerta",
    "sri_respuesta_vehiculo", "sri_respuesta_rubros",
    "propietario_nombre", "propietario_fuente", "propietario_consultado_en",
    "propietario_estado", "propietario_detalle", "propietario_cambiado_en",
    "propietario_anterior", "propietario_nuevo",
)

_API = "https://api.github.com"
_CSV_LOCK = threading.RLock()


def _config() -> tuple[str, str, str, str]:
    token = get_secret("GITHUB_TOKEN")
    repository = get_secret("GITHUB_DATA_REPOSITORY")
    branch = get_secret("GITHUB_DATA_BRANCH", "main") or "main"
    path = get_secret("GITHUB_DATA_PATH", "data/detecciones.csv") or "data/detecciones.csv"
    if not token or not repository:
        raise RuntimeError("Faltan los secretos GITHUB_TOKEN o GITHUB_DATA_REPOSITORY.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise RuntimeError("GITHUB_DATA_REPOSITORY debe tener el formato propietario/repositorio.")
    return token, repository, branch, path


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _ensure_private(token: str, repository: str) -> None:
    response = requests.get(f"{_API}/repos/{repository}", headers=_headers(token), timeout=15)
    response.raise_for_status()
    if response.json().get("private") is not True:
        raise RuntimeError("El repositorio de datos debe ser privado; no se guardó información.")


def _contents_url(repository: str, path: str) -> str:
    return f"{_API}/repos/{repository}/contents/{quote(path, safe='/')}"


def _read_csv(token: str, repository: str, branch: str, path: str) -> tuple[list[dict], str | None]:
    response = requests.get(_contents_url(repository, path), headers=_headers(token),
                            params={"ref": branch}, timeout=20)
    if response.status_code == 404:
        return [], None
    response.raise_for_status()
    item = response.json()
    if item.get("encoding") != "base64" or not item.get("content"):
        raise RuntimeError("GitHub no devolvió el CSV codificado en base64.")
    raw = base64.b64decode(item["content"]).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw))), item["sha"]


def _write_csv(token: str, repository: str, branch: str, path: str,
               rows: list[dict], sha: str | None, message: str) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = {
        "message": message,
        "branch": branch,
        "content": base64.b64encode(output.getvalue().encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha
    response = requests.put(_contents_url(repository, path), headers=_headers(token),
                            json=payload, timeout=30)
    response.raise_for_status()


def append_detection(row: dict) -> None:
    token, repository, branch, path = _config()
    _ensure_private(token, repository)
    with _CSV_LOCK:
        for attempt in range(3):
            rows, sha = _read_csv(token, repository, branch, path)
            if any(existing.get("event_id") == row["event_id"] for existing in rows):
                return
            rows.append({key: row.get(key) for key in CSV_FIELDS})
            try:
                _write_csv(token, repository, branch, path, rows, sha,
                           f"Registrar detección {row.get('placa', '')}")
                return
            except requests.HTTPError as exc:
                if attempt == 2 or exc.response is None or exc.response.status_code not in (409, 422):
                    raise
                time.sleep(0.4 * (attempt + 1))
    raise RuntimeError("No se pudo guardar la detección en GitHub tras varios intentos.")


def update_detection(event_id: str, fields: dict) -> None:
    token, repository, branch, path = _config()
    _ensure_private(token, repository)
    allowed = set(CSV_FIELDS)
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return
    with _CSV_LOCK:
        for attempt in range(3):
            rows, sha = _read_csv(token, repository, branch, path)
            target = next((row for row in rows if row.get("event_id") == event_id), None)
            if target is None:
                raise RuntimeError("No se encontró la detección para completar sus datos.")
            target.update({key: "" if value is None else value for key, value in updates.items()})
            try:
                _write_csv(token, repository, branch, path, rows, sha,
                           f"Completar datos de detección {target.get('placa', '')}")
                return
            except requests.HTTPError as exc:
                if attempt == 2 or exc.response is None or exc.response.status_code not in (409, 422):
                    raise
                time.sleep(0.4 * (attempt + 1))
    raise RuntimeError("No se pudo actualizar la detección en GitHub tras varios intentos.")


def _sri_get(url: str, params: dict) -> tuple[object, str]:
    headers = {"Accept": "application/json", "User-Agent": "SIRAP-ALPR/1.0 (consulta publica)"}
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code in (204, 404):
                return None, response.text
            if response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            text = response.text.strip()
            return (json.loads(text) if text else None), text
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    return None, ""


_SRI_URL = (
    "https://srienlinea.sri.gob.ec/"
    "sri-matriculacion-vehicular-recaudacion-servicio-internet/rest"
)
_SRI_LOCK = threading.Lock()
_SRI_LAST_CALL = 0.0


def _query_sri(plate: str) -> dict:
    global _SRI_LAST_CALL
    compact = re.sub(r"[^A-Z0-9]", "", plate.upper())
    url = f"{_SRI_URL}/BaseVehiculo/obtenerPorNumeroPlacaOPorNumeroCampvOPorNumeroCpn"
    with _SRI_LOCK:
        wait = 2.0 - (time.monotonic() - _SRI_LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        _SRI_LAST_CALL = time.monotonic()
        vehicle, raw = _sri_get(url, {"numeroPlacaCampvCpn": compact})
        if not (isinstance(vehicle, dict) and (vehicle.get("numeroPlaca") or vehicle.get("codigoVehiculo")))                 and re.fullmatch(r"[A-Z]{3}0[0-9]{3}", compact):
            time.sleep(1)
            vehicle, raw = _sri_get(url, {"numeroPlacaCampvCpn": compact[:3] + compact[4:]})
    result = {
        "sri_consultado_en": now_local().isoformat(sep=" ", timespec="seconds"),
        "sri_encontrado": False,
        "sri_respuesta_vehiculo": raw[:4000] or "",
    }
    if not isinstance(vehicle, dict) or not (vehicle.get("numeroPlaca") or vehicle.get("codigoVehiculo")):
        result["sri_alerta"] = "Placa no encontrada en el SRI."
        return result
    try:
        last_paid = int(vehicle.get("ultimoAnioPagado"))
    except (TypeError, ValueError):
        last_paid = None
    result.update({
        "sri_encontrado": True,
        "sri_codigo_vehiculo": vehicle.get("codigoVehiculo"),
        "sri_camv_cpn": vehicle.get("numeroCamvCpn"),
        "sri_marca": vehicle.get("descripcionMarca"),
        "sri_modelo": vehicle.get("descripcionModelo"),
        "sri_anio_modelo": vehicle.get("anioAuto"),
        "sri_pais": vehicle.get("descripcionPais"),
        "sri_clase": vehicle.get("nombreClase"),
        "sri_servicio": vehicle.get("descripcionServicio"),
        "sri_canton": vehicle.get("descripcionCanton"),
        "sri_estado_exoneracion": vehicle.get("estadoExoneracion"),
        "sri_ultimo_anio_pagado": last_paid,
        "sri_matricula_al_dia": None if last_paid is None else last_paid >= now_local().year,
        "sri_prohibido_enajenar": vehicle.get("prohibidoEnajenar"),
        "sri_alerta": "",
    })
    alerts = []
    if result["sri_matricula_al_dia"] is False:
        alerts.append(f"Sin pago del año {now_local().year} (último: {last_paid})")
    code = vehicle.get("codigoVehiculo")
    if code:
        try:
            rubros, raw_rubros = _sri_get(f"{_SRI_URL}/ConsultaRubros/obtenerPorCodigoVehiculo",
                                          {"codigoVehiculo": code})
            result["sri_respuesta_rubros"] = raw_rubros[:4000]
            if rubros is None or isinstance(rubros, list):
                items = rubros or []
                result["sri_rubros_pendientes"] = len(items)
                values = [item.get("valor") for item in items if isinstance(item, dict)]
                if items and len(values) == len(items) and all(isinstance(v, (int, float)) for v in values):
                    result["sri_total_pendiente"] = sum(values)
                if items:
                    alerts.append(f"{len(items)} valores pendientes")
        except Exception as exc:
            result["sri_respuesta_rubros"] = f"error: {type(exc).__name__}: {exc}"[:500]
    result["sri_alerta"] = "; ".join(alerts)
    return result


_OWNER_URL = (
    "https://www.ecuadorlegalonline.com/consultas/agencia-nacional-de-transito/"
    "consultar-a-quien-pertenece-un-vehiculo-por-placa-ant/"
)
_OWNER_LOCK = threading.Lock()
_OWNER_LAST_CALL = 0.0


def _visible_name(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    if (not value or len(value) > 250 or not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", value)
            or re.fullmatch(r"[xX*\- .]+", value)
            or re.match(r"^(?:c[eé]dula|ruc|direcci[oó]n|tel[eé]fono|due[nñ]o anterior|disponible|no disponible|oculto|ninguno|nombre$)", value, re.I)):
        return None
    return value


def _query_owner(plate: str) -> dict:
    global _OWNER_LAST_CALL
    compact = re.sub(r"[^A-Z0-9]", "", plate.upper())
    if not re.fullmatch(r"[A-Z]{3}[0-9]{3,4}", compact):
        return {"propietario_estado": "placa_invalida"}
    normalized = compact[:3] + "-" + compact[3:].zfill(4)
    with _OWNER_LOCK:
        wait = 12.0 - (time.monotonic() - _OWNER_LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        _OWNER_LAST_CALL = time.monotonic()
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    page = browser.new_page(locale="es-EC", viewport={"width": 1360, "height": 900})
                    page.goto(_OWNER_URL, wait_until="domcontentloaded", timeout=25000)
                    entry = page.locator('input[name*="placa" i], input[placeholder*="placa" i]')
                    if entry.count() == 0:
                        entry = page.get_by_label("Placa", exact=True)
                    if entry.count() == 0:
                        return {"propietario_estado": "interfaz_no_reconocida",
                                "propietario_detalle": "No se localizó el campo Placa."}
                    entry.first.fill(compact)
                    submit = page.get_by_role("button", name=re.compile(r"^Consultar$", re.I))
                    if submit.count() == 0:
                        return {"propietario_estado": "interfaz_no_reconocida",
                                "propietario_detalle": "No se localizó el botón Consultar."}
                    submit.first.click(timeout=25000)
                    deadline = time.monotonic() + 45
                    while time.monotonic() < deadline:
                        text = page.locator("body").inner_text(timeout=8000)
                        if re.search(r"captcha|acceso denegado|verifica que (eres|no eres)", text, re.I):
                            return {"propietario_estado": "acceso_restringido",
                                    "propietario_detalle": "El sitio requiere verificación humana."}
                        match = re.search(r"Placa consultada\s*[:：]?\s*([A-Z]{3}[-\s]?[0-9]{3,4})\b", text, re.I)
                        if match:
                            result_plate = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
                            if result_plate != compact:
                                return {"propietario_estado": "placa_no_coincide",
                                        "propietario_detalle": "La placa de la respuesta no coincide."}
                            section = re.search(
                                r"DATOS DEL PROPIETARIO DEL VEH[IÍ]CULO(.*?)(?:VER REPORTE COMPLETO|¿No encuentra datos|$)",
                                text, re.I | re.S)
                            if section:
                                lines = [line.strip() for line in section.group(1).splitlines() if line.strip()]
                                for index, line in enumerate(lines):
                                    name_match = re.match(r"^Nombre\s*[:：]?\s*(.*)$", line, re.I)
                                    if name_match:
                                        name = _visible_name(name_match.group(1) or
                                                             (lines[index + 1] if index + 1 < len(lines) else ""))
                                        if name:
                                            return {
                                                "propietario_nombre": name,
                                                "propietario_fuente": "ecuadorlegalonline_publico",
                                                "propietario_consultado_en": now_local().isoformat(sep=" ", timespec="seconds"),
                                                "propietario_estado": "encontrado",
                                                "propietario_detalle": "",
                                            }
                            if re.search(r"no se encontr[oó]|sin resultados|veh[ií]culo no existe", text, re.I):
                                return {"propietario_estado": "sin_datos",
                                        "propietario_detalle": "El sitio no devolvió propietario."}
                        time.sleep(0.75)
                    return {"propietario_estado": "sin_respuesta_verificable",
                            "propietario_detalle": "No se confirmó que el resultado corresponda a la placa."}
                finally:
                    browser.close()
        except Exception as exc:
            return {"propietario_estado": "error",
                    "propietario_detalle": f"{type(exc).__name__}: {exc}"[:300]}
        finally:
            # No se accede a reportes completos, CAPTCHAs, datos ocultos, ni servicios de pago.
            pass


_ENRICHMENT_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sirap-enrichment")


def _normalized_brand(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _enrich(event_id: str, plate: str, plant_brand: str | None) -> None:
    try:
        sri = _query_sri(plate)
        sri_brand = sri.get("sri_marca")
        if plant_brand and sri_brand and sri.get("sri_encontrado"):
            sri["marca_coincide_sri"] = _normalized_brand(plant_brand) == _normalized_brand(sri_brand)
        update_detection(event_id, sri)
    except Exception as exc:
        logger.exception("No se pudo consultar/guardar SRI para %s: %s", plate, exc)
        try:
            update_detection(event_id, {
                "sri_consultado_en": now_local().isoformat(sep=" ", timespec="seconds"),
                "sri_encontrado": "",
                "sri_error": f"{type(exc).__name__}: {exc}"[:500],
            })
        except Exception:
            logger.exception("No se pudo registrar el error SRI para %s", plate)
    try:
        owner = _query_owner(plate)
        owner.setdefault("propietario_fuente", "ecuadorlegalonline_publico")
        owner.setdefault("propietario_consultado_en", now_local().isoformat(sep=" ", timespec="seconds"))
        update_detection(event_id, owner)
    except Exception as exc:
        logger.exception("No se pudo completar propietario para %s: %s", plate, exc)
        try:
            update_detection(event_id, {
                "propietario_consultado_en": now_local().isoformat(sep=" ", timespec="seconds"),
                "propietario_estado": "error",
                "propietario_detalle": f"{type(exc).__name__}: {exc}"[:300],
            })
        except Exception:
            logger.exception("No se pudo registrar el error del propietario para %s", plate)


def enrich_detection(event_id: str, plate: str, plant_brand: str | None = None) -> None:
    """Encola las consultas externas para que no retrasen la respuesta del operador."""
    _ENRICHMENT_POOL.submit(_enrich, event_id, plate, plant_brand)
