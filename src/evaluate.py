"""Evaluación de SIRAP: detector (mAP, P, R, F1) y sistema completo (EMR, CER, tiempo).

Uso::

    # Detector en el split test (requiere ultralytics y los pesos best_model.pt)
    python -m src.evaluate detector --data /ruta/data.yaml

    # Punta a punta con imágenes anotadas: CSV con columnas image_path, plate_gt
    python -m src.evaluate e2e --csv data/processed/garita_ground_truth.csv

Los resultados se guardan en ``results/metrics/`` como JSON y CSV.
"""

from __future__ import annotations

import argparse
from typing import Any, Iterable

import pandas as pd

from src.data_processing import clean_text, load_image, normalize_plate, plate_distance
from src.utils import get_logger, load_config, resolve_path, save_json

logger = get_logger("sirap.evaluate")


def exact_match_rate(predictions: Iterable[str | None], references: Iterable[str | None]) -> float:
    """Fracción de placas leídas exactamente (tras normalizar ambas).

    Una predicción ``None`` (no se encontró placa) cuenta como error.
    """
    pairs = list(zip(predictions, references))
    if not pairs:
        return 0.0
    hits = sum(1 for p, r in pairs if p is not None and normalize_plate(p) == normalize_plate(r))
    return hits / len(pairs)


def character_error_rate(predictions: Iterable[str | None], references: Iterable[str | None]) -> float:
    """CER: suma de distancias de Levenshtein / suma de caracteres de la referencia."""
    errors = total = 0
    for p, r in zip(predictions, references):
        ref = clean_text(r)
        errors += plate_distance(p or "", ref)
        total += len(ref)
    return errors / total if total else 0.0


def f1_score(precision: float, recall: float) -> float:
    """F1 a partir de precisión y recall."""
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def evaluate_detector(data_yaml: str, weights: str = "models/best_model.pt", imgsz: int = 640,
                      split: str = "test") -> dict[str, Any]:
    """Valida YOLO11 en ``split`` con Ultralytics y guarda ``results/metrics/detector_<split>.json``."""
    from ultralytics import YOLO  # type: ignore

    metrics = YOLO(str(resolve_path(weights))).val(data=str(resolve_path(data_yaml)), imgsz=imgsz,
                                                    split=split, verbose=False)
    precision, recall = float(metrics.box.mp), float(metrics.box.mr)
    result = {"split": split, "imgsz": imgsz, "map50": float(metrics.box.map50),
              "map50_95": float(metrics.box.map), "precision": precision, "recall": recall,
              "f1": f1_score(precision, recall)}
    save_json(result, f"results/metrics/detector_{split}.json")
    logger.info("Detector (%s): %s", split, result)
    return result


def evaluate_end_to_end(csv_path: str, pipeline: Any | None = None) -> dict[str, Any]:
    """Corre el pipeline sobre imágenes anotadas y mide EMR, CER y tiempo por imagen.

    Args:
        csv_path: CSV con columnas ``image_path`` (relativa a la raíz o absoluta) y ``plate_gt``.
        pipeline: ``ALPRPipeline`` ya creado (si no, se crea con la configuración).
    """
    from src.model import ALPRPipeline

    pipeline = pipeline or ALPRPipeline.from_config()
    df = pd.read_csv(resolve_path(csv_path))
    if not {"image_path", "plate_gt"} <= set(df.columns):
        raise ValueError("El CSV debe tener las columnas image_path y plate_gt.")
    rows = []
    for _, row in df.iterrows():
        try:
            image = load_image(resolve_path(row["image_path"]).read_bytes())
            rec = pipeline.recognize(image)
            rows.append({"image_path": row["image_path"], "plate_gt": normalize_plate(row["plate_gt"]),
                         "plate_pred": rec.plate, "ocr_confidence": rec.ocr_confidence,
                         "tiempo_ms": rec.timings_ms.get("total")})
        except Exception as exc:  # noqa: BLE001 — una imagen dañada no detiene la evaluación
            logger.error("No se pudo evaluar %s: %s", row["image_path"], exc)
            rows.append({"image_path": row["image_path"], "plate_gt": normalize_plate(row["plate_gt"]),
                         "plate_pred": None, "ocr_confidence": 0.0, "tiempo_ms": None})
    out = pd.DataFrame(rows)
    out.to_csv(resolve_path("results/metrics/e2e_predicciones.csv"), index=False)
    targets = load_config()["metas"]
    result = {
        "n": len(out), "detector": pipeline.detector.name,
        "emr": exact_match_rate(out["plate_pred"], out["plate_gt"]),
        "cer": character_error_rate(out["plate_pred"], out["plate_gt"]),
        "tiempo_ms_promedio": float(out["tiempo_ms"].dropna().mean()) if out["tiempo_ms"].notna().any() else None,
        "meta_emr": targets["emr"], "meta_tiempo_s": targets["tiempo_e2e_s"],
    }
    save_json(result, "results/metrics/e2e.json")
    logger.info("Punta a punta: %s", result)
    return result


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description="Evaluación de SIRAP")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_det = sub.add_parser("detector")
    p_det.add_argument("--data", required=True)
    p_det.add_argument("--weights", default="models/best_model.pt")
    p_det.add_argument("--split", default="test")
    p_e2e = sub.add_parser("e2e")
    p_e2e.add_argument("--csv", required=True)
    args = parser.parse_args()
    if args.cmd == "detector":
        evaluate_detector(args.data, args.weights, split=args.split)
    else:
        evaluate_end_to_end(args.csv)


if __name__ == "__main__":
    main()
