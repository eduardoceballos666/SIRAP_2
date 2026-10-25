"""Dashboard, Historial y Acerca del modelo."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from api.jsonsafe import plain
from api.deps import current_user, get_barrier, get_store, get_pipeline, require_roles, thresholds
from src.utils import load_json, now_local

router = APIRouter(prefix="/api", tags=["Dashboard, Historial y Modelo"])

RESULT_LABELS = {"AUTORIZADO": "Autorizado", "DENEGADO": "Denegado", "NO_REGISTRADO": "No registrado",
                 "VERIFICACION_MANUAL": "Verificación manual"}


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    out = df.copy()
    if "fecha_hora" in out:
        out["fecha_hora"] = out["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return plain(out.to_dict(orient="records"))


@router.get("/system", summary="Estado del sistema")
def system(_: dict = Depends(current_user)) -> dict[str, Any]:
    pipeline, db, barrier = get_pipeline(), get_store(), get_barrier()
    ocr_threshold, det_threshold, _ = thresholds()
    return {"detector": pipeline.detector.name, "detector_es_modelo": pipeline.detector.is_model,
            "ocr": pipeline.reader.model_name, "base_datos": db.engine,
            "barrera": "simulada" if getattr(barrier, "simulated", True) else "conectada",
            "umbral_ocr": ocr_threshold, "umbral_detector": det_threshold, "garitas": db.garitas()}


@router.get("/operations", summary="Historial filtrado")
def operations(desde: Optional[date] = None, hasta: Optional[date] = None, placa: Optional[str] = None,
               garita: Optional[str] = None, resultado: Optional[str] = None,
               tipo_movimiento: Optional[str] = None, limit: int = Query(1000, ge=1, le=5000),
               _: dict = Depends(current_user)) -> list[dict[str, Any]]:
    return _records(get_store().operations(desde, hasta, placa, garita, resultado, tipo_movimiento, limit))


@router.get("/operations/export.csv", summary="Exportar el historial filtrado a CSV")
def export_csv(desde: Optional[date] = None, hasta: Optional[date] = None, placa: Optional[str] = None,
               garita: Optional[str] = None, resultado: Optional[str] = None,
               tipo_movimiento: Optional[str] = None,
               _: dict = Depends(require_roles("SUPERVISOR", "ADMINISTRADOR"))) -> Response:
    df = get_store().operations(desde, hasta, placa, garita, resultado, tipo_movimiento)
    name = f"sirap_historial_{now_local():%Y%m%d}.csv"
    return Response(df.to_csv(index=False).encode("utf-8-sig"), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/dashboard", summary="Indicadores y datos para los gráficos")
def dashboard(days: int = Query(7, ge=1, le=365), include_demo: bool = True,
              _: dict = Depends(current_user)) -> dict[str, Any]:
    today = now_local().date()
    df = get_store().operations(desde=today - timedelta(days=days - 1), hasta=today)
    if not include_demo and not df.empty:
        df = df[df["origen"] != "DEMO"]
    if df.empty:
        return {"kpis": {"ingresos": 0, "salidas": 0, "identificados": 0, "alertas": 0},
                "por_hora": [], "por_resultado": [], "por_garita": [], "alertas": []}
    df["resultado_txt"] = df["resultado"].map(RESULT_LABELS).fillna(df["resultado"])
    alerts = df[df["resultado"].isin(["DENEGADO", "NO_REGISTRADO"]) | (df["accion"] == "APERTURA_MANUAL")]
    by_hour = df.assign(hora=df["fecha_hora"].dt.hour).groupby(["hora", "resultado_txt"]).size()
    return {
        "kpis": {"ingresos": int((df["tipo_movimiento"] == "ENTRADA").sum()),
                 "salidas": int((df["tipo_movimiento"] == "SALIDA").sum()),
                 "identificados": int(df["placa_final"].dropna().nunique()),
                 "alertas": int(len(alerts))},
        "por_hora": [{"hora": int(h), "resultado": r, "n": int(n)} for (h, r), n in by_hour.items()],
        "por_resultado": [{"resultado": r, "n": int(n)} for r, n in df["resultado_txt"].value_counts().items()],
        "por_garita": [{"garita": g, "movimiento": m, "n": int(n)}
                       for (g, m), n in df.groupby(["garita", "tipo_movimiento"]).size().items()],
        "alertas": _records(alerts[["fecha_hora", "garita", "placa_final", "resultado_txt", "accion", "operador"]]
                            .head(12)),
    }


@router.get("/model/info", summary="Métricas y descripción del modelo")
def model_info(_: dict = Depends(current_user)) -> dict[str, Any]:
    names = ("detector_test", "ocr_savh", "e2e", "velocidad", "entrenamiento", "umbrales", "ocr_afinamiento",
             "regla_decision_savh", "optimizacion_resumen")
    ocr_threshold, det_threshold, _ = thresholds()
    return {"metricas": {n: load_json(f"results/metrics/{n}.json") for n in names},
            "detector": get_pipeline().detector.name, "ocr": get_pipeline().reader.model_name,
            "umbral_ocr": ocr_threshold, "umbral_detector": det_threshold}
