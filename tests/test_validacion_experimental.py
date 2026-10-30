"""Pruebas sin GPU ni imágenes privadas de los auxiliares de validación SIRAP."""
import pandas as pd

from scripts.auditar_savh import audit
from scripts.validar_multisemilla_yolo11 import summary_for


def test_auditoria_savh_agrupa_copias_y_no_inventa_respuestas():
    sheet = pd.DataFrame([
        {"n": "1", "fila_gt": "99", "imagen": "a.jpg", "texto_actual": "ABC1234",
         "sugerencia": "ABC1234", "igual_a": "", "revision: ok o placa correcta": ""},
        {"n": "2", "fila_gt": "100", "imagen": "b.jpg", "texto_actual": "ABC1234",
         "sugerencia": "ABC1234", "igual_a": "1", "revision: ok o placa correcta": ""},
        {"n": "3", "fila_gt": "101", "imagen": "c.jpg", "texto_actual": "DEF5678",
         "sugerencia": "DEF5678", "igual_a": "", "revision: ok o placa correcta": "ok"},
    ])
    summary, pending = audit(sheet)
    assert summary["filas_hoja"] == 3
    assert summary["grupos_unicos"] == 2
    assert summary["grupos_pendientes"] == 1
    assert summary["grupos_revisados"] == 1
    assert len(pending) == 1
    assert int(pending.iloc[0]["copias_en_grupo"]) == 2


def test_auditoria_savh_detecta_respuestas_en_conflicto():
    sheet = pd.DataFrame([
        {"n": "1", "fila_gt": "99", "imagen": "a.jpg", "texto_actual": "ABC1234",
         "sugerencia": "ABC1234", "igual_a": "", "revision: ok o placa correcta": "ok"},
        {"n": "2", "fila_gt": "100", "imagen": "b.jpg", "texto_actual": "ABC1234",
         "sugerencia": "ABC1234", "igual_a": "1", "revision: ok o placa correcta": "XYZ1234"},
    ])
    summary, _ = audit(sheet)
    assert summary["grupos_conflicto"] == 1
    assert summary["grupos_pendientes"] == 0


def test_resumen_multisemilla_deltas_emparejadas_y_parcial():
    rows = [
        {"semilla": 0, "modelo": "base", "map50_95": 0.60, "recall": 0.90},
        {"semilla": 0, "modelo": "optimizada", "map50_95": 0.61, "recall": 0.88},
        {"semilla": 1, "modelo": "base", "map50_95": 0.62, "recall": 0.91},
        {"semilla": 1, "modelo": "optimizada", "map50_95": 0.64, "recall": 0.92},
    ]
    summary = summary_for(rows, [0, 1, 2])
    assert summary["estado"] == "parcial"
    assert summary["pares_completos"] == 2
    assert abs(summary["delta_medio_map50_95"] - 0.015) < 1e-10
    assert summary["semillas_con_mejora"] == 2
    assert summary["delta_std_map50_95"] > 0
    assert summary["comparaciones_pareadas"][0]["delta_recall"] < 0
