"""Pruebas del pipeline de reconocimiento, la regla de decisión y las métricas.

Las pruebas del OCR descargan el modelo de fast-plate-ocr (≈5 MB) la primera vez; si no hay
red se omiten.
"""

from pathlib import Path

import numpy as np
import pytest

from src.access_control import decide_access
from src.evaluate import character_error_rate, exact_match_rate, f1_score
from src.model import Detection, PlateDetector, _nms

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


# ---- regla de decisión ----------------------------------------------------------------------
@pytest.mark.parametrize("plate, conf, expected", [
    ("PBA-8901", 0.98, "AUTORIZADO"),          # lista blanca
    ("GBO-0429", 0.98, "DENEGADO"),            # lista restringida
    ("GSA-1234", 0.98, "NO_REGISTRADO"),       # no está en la base
    ("PBA-8907", 0.98, "VERIFICACION_MANUAL"),  # a un carácter de una placa registrada
    ("PBA-8901", 0.40, "VERIFICACION_MANUAL"),  # confianza baja
    (None, 0.0, "VERIFICACION_MANUAL"),        # sin lectura
])
def test_decide_access(db, plate, conf, expected):
    decision = decide_access(plate, conf, db, confidence_threshold=0.85)
    assert decision.resultado == expected
    assert decision.permite_apertura == (expected == "AUTORIZADO")


def test_decision_suggests_similar_plate(db):
    assert decide_access("PBA-8907", 0.99, db).sugerencia == "PBA-8901"


def test_authorized_vehicle_details(db):
    vehicle = decide_access("PBA-8901", 0.99, db).vehiculo
    assert vehicle["marca"] == "Toyota" and vehicle["propietario"] == "Juan Pérez"


def test_revoked_vehicle_is_not_authorized(db):
    db.revoke_authorization("PBA-8901")
    assert decide_access("PBA-8901", 0.99, db).resultado == "NO_REGISTRADO"


# ---- métricas ---------------------------------------------------------------------------------
def test_metrics():
    assert exact_match_rate(["PBA8901", "GBO-0429", None], ["PBA-8901", "GBO-0428", "GSA-1234"]) == pytest.approx(1 / 3)
    assert character_error_rate(["PBA8901"], ["PBA8901"]) == 0.0
    assert character_error_rate(["PBA8907"], ["PBA8901"]) == pytest.approx(1 / 7)
    assert f1_score(0.9, 0.8) == pytest.approx(0.8470588, rel=1e-5)
    assert f1_score(0, 0) == 0.0


# ---- detector -------------------------------------------------------------------------------
def test_nms_removes_overlaps():
    boxes = np.array([[0, 0, 10, 10], [1, 1, 10, 10], [50, 50, 60, 60]], np.float32)
    scores = np.array([0.9, 0.8, 0.7], np.float32)
    assert _nms(boxes, scores, 0.5) == [0, 2]


def test_detector_without_weights_uses_fallback(tmp_path):
    detector = PlateDetector(tmp_path / "no.onnx", tmp_path / "no.pt", allow_fallback=True)
    assert detector.backend == "opencv" and not detector.is_model


def test_detector_without_weights_and_without_fallback_fails(tmp_path):
    detector = PlateDetector(tmp_path / "no.onnx", None, allow_fallback=False)
    with pytest.raises(RuntimeError):
        detector.detect(np.zeros((200, 200, 3), np.uint8))


def test_detection_area():
    assert Detection((0, 0, 10, 5), 0.9).area == 50


# ---- pipeline completo (requiere el modelo de OCR) ------------------------------------------
@pytest.fixture(scope="module")
def pipeline():
    try:
        from src.model import ALPRPipeline

        return ALPRPipeline.from_config()
    except Exception as exc:  # noqa: BLE001 — sin red no se puede descargar el OCR
        pytest.skip(f"OCR no disponible: {exc}")


@pytest.mark.parametrize("filename, plate", [
    ("garita3_PBA-8901.jpg", "PBA-8901"),
    ("garita2_GBO-0429.jpg", "GBO-0429"),
    ("garita1_GSA-1234.jpg", "GSA-1234"),
])
def test_pipeline_reads_sample_plates(pipeline, filename, plate):
    from src.data_processing import load_image

    result = pipeline.recognize(load_image((SAMPLES / filename).read_bytes()))
    assert result.plate == plate
    assert 0.0 <= result.ocr_confidence <= 1.0
    assert result.timings_ms["total"] < 5000


def test_pipeline_flags_blurred_image(pipeline, db):
    from src.data_processing import load_image

    result = pipeline.recognize(load_image((SAMPLES / "garita3_PCD-5678_desenfocada.jpg").read_bytes()))
    decision = decide_access(result.plate, result.ocr_confidence, db, confidence_threshold=0.85)
    assert decision.resultado == "VERIFICACION_MANUAL"


def test_low_detector_confidence_goes_to_manual(db):
    decision = decide_access("PBA-8901", 1.0, db, det_confidence=0.2, det_threshold=0.30)
    assert decision.resultado == "VERIFICACION_MANUAL" and "DETECCIÓN" in decision.detalle
    assert decide_access("PBA-8901", 1.0, db, det_confidence=0.8, det_threshold=0.30).resultado == "AUTORIZADO"
