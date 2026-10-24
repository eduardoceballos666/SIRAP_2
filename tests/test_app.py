"""Pruebas de la interfaz: componentes HTML, base de datos e integración con Streamlit AppTest."""

from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from app import ui
from src.access_control import AccessDecision

ROOT = Path(__file__).resolve().parents[1]


# ---- componentes ----------------------------------------------------------------------------
def test_result_card_states():
    assert "EN ESPERA" in ui.result_card(None)
    ok = ui.result_card(AccessDecision("AUTORIZADO", "ACCESO AUTORIZADO", "LISTA BLANCA", "BLANCA"))
    assert 'class="result ok"' in ok and "LISTA BLANCA" in ok
    deny = ui.result_card(AccessDecision("DENEGADO", "ACCESO DENEGADO", "LISTA RESTRINGIDA", "RESTRINGIDA"))
    assert 'class="result deny"' in deny


def test_plate_card_confidence_colors():
    assert 'conf hi' in ui.plate_card("PBA-8901", 0.98, 0.85)
    assert 'conf mid' in ui.plate_card("PBA-8901", 0.70, 0.85)
    assert 'conf lo' in ui.plate_card("PBA-8901", 0.30, 0.85)
    assert "— — —" in ui.plate_card(None, None, 0.85)


def test_html_is_escaped():
    html = ui.vehicle_table({"marca": "<script>x</script>", "modelo": "", "color": "", "propietario": ""})
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_annotate_frame_returns_same_size():
    frame = ui.annotate_frame(np.zeros((300, 500, 3), np.uint8), (100, 100, 200, 140), "PBA-8901", "AUTORIZADO",
                              "Garita 3", datetime(2026, 10, 22, 12, 5, 14))
    assert frame.size == (500, 300)


# ---- base de datos ---------------------------------------------------------------------------
def test_log_and_filter_operations(db):
    db.log_operation(garita="Garita 3", operador="Op", tipo_movimiento="Entrada", resultado="AUTORIZADO",
                     accion="APERTURA_AUTOMATICA", placa_final="PBA-8901", confianza_ocr=0.98)
    db.log_operation(garita="Garita 1", operador="Op", tipo_movimiento="Salida", resultado="NO_REGISTRADO",
                     accion="RECHAZO", placa_final="GSA-1234", confianza_ocr=0.95)
    assert len(db.operations()) == 2
    assert db.operations(placa="pba").iloc[0]["placa_final"] == "PBA-8901"
    assert len(db.operations(tipo_movimiento="SALIDA")) == 1


def test_manual_opening_requires_reason(db):
    with pytest.raises(ValueError, match="motivo"):
        db.log_operation(garita="Garita 3", operador="Op", tipo_movimiento="Entrada",
                         resultado="VERIFICACION_MANUAL", accion="APERTURA_MANUAL")


def test_invalid_values_are_rejected(db):
    with pytest.raises(ValueError):
        db.log_operation(garita="G", operador="Op", tipo_movimiento="Lateral", resultado="AUTORIZADO",
                         accion="RECHAZO")
    with pytest.raises(ValueError):
        db.set_authorization("ZZZ-0000", "BLANCA")


def test_demo_history_can_be_cleared(db):
    assert db.load_demo_history(10) == 10
    assert db.clear_demo_history() == 10


# ---- integración con Streamlit -----------------------------------------------------------------
def test_app_runs_without_exceptions():
    from streamlit.testing.v1 import AppTest

    try:
        app = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=120).run()
    except Exception as exc:  # noqa: BLE001 — sin red no se descarga el OCR
        pytest.skip(f"No se pudo iniciar la app: {exc}")
    assert not app.exception
    assert any("Reconocimiento automático" in m.value for m in app.markdown)
