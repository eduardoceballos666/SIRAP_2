"""Entrenamiento del detector de placas YOLO11-s (mismo protocolo que el notebook, sección 2.1).

El modelo **ya está entrenado**: sus pesos viven en ``MyDrive/proyecto_integrador_placas`` y se
copian a ``models/``. Este script existe para reproducir el entrenamiento; por defecto **no
reentrena** si ya hay pesos (use ``--force`` para repetirlo).

Uso::

    python -m src.train --data /ruta/data.yaml                 # entrena (o reanuda) YOLO11-s
    python -m src.train --data /ruta/data.yaml --export-only   # solo exporta best.pt → ONNX
    python -m src.train --roboflow                              # descarga el dataset de Roboflow (ROBOFLOW_API_KEY)

Hiperparámetros por defecto (preset «completo» del notebook): 40 épocas, imgsz 640, paciencia 10,
semilla 0, batch 16, optimizador elegido por Ultralytics (AdamW con este tamaño de dataset).
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from src.utils import get_logger, get_secret, resolve_path, save_json

logger = get_logger("sirap.train")

#: Dataset de detección usado en el notebook (Roboflow Universe, CC BY 4.0).
RF_WORKSPACE = "roboflow-universe-projects"
RF_PROJECT = "license-plate-recognition-rxg4e"
RF_VERSION = 11

DEFAULT_HPARAMS: dict[str, Any] = {
    "weights": "yolo11s.pt", "epochs": 40, "imgsz": 640, "patience": 10, "seed": 0,
    "batch": 16, "workers": 2, "deterministic": True,
}


def download_roboflow_dataset(target_dir: str | Path = "data/raw") -> Path:
    """Descarga el dataset de Roboflow en formato YOLO y devuelve la ruta de ``data.yaml``.

    Raises:
        RuntimeError: si falta el secreto ``ROBOFLOW_API_KEY``.
    """
    api_key = get_secret("ROBOFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("Falta ROBOFLOW_API_KEY (variable de entorno o secreto).")
    from roboflow import Roboflow  # type: ignore

    location = resolve_path(target_dir) / f"{RF_PROJECT}-v{RF_VERSION}"
    project = Roboflow(api_key=api_key).workspace(RF_WORKSPACE).project(RF_PROJECT)
    project.version(RF_VERSION).download("yolov11", location=str(location))
    return location / "data.yaml"


def train(data_yaml: str | Path, run_dir: str | Path = "results/runs", name: str = "YOLO11_yolo11s_completo",
          force: bool = False, **overrides: Any) -> Path:
    """Entrena YOLO11-s o reanuda un entrenamiento interrumpido.

    Args:
        data_yaml: ``data.yaml`` del dataset en formato YOLO.
        run_dir: carpeta de las corridas de Ultralytics.
        name: nombre de la corrida.
        force: borrar la corrida anterior y entrenar desde cero.
        **overrides: hiperparámetros que reemplazan a ``DEFAULT_HPARAMS``.

    Returns:
        La ruta de ``best.pt``.
    """
    from ultralytics import YOLO  # type: ignore

    hp = {**DEFAULT_HPARAMS, **overrides}
    project = resolve_path(run_dir)
    run_path = project / name
    best, last = run_path / "weights" / "best.pt", run_path / "weights" / "last.pt"
    if force and run_path.exists():
        shutil.rmtree(run_path)
    if best.exists() and not force and not last.exists():
        logger.info("Ya existe %s: no se reentrena (use --force).", best)
        return best
    if last.exists() and not force:
        logger.info("Reanudando desde %s", last)
        YOLO(str(last)).train(resume=True)
    else:
        model = YOLO(hp.pop("weights"))
        model.train(data=str(resolve_path(data_yaml)), project=str(project), name=name, exist_ok=True,
                    **{k: v for k, v in hp.items()})
    save_json({"run": name, "hparams": {**DEFAULT_HPARAMS, **overrides}}, run_path / "train_done.json")
    return best


def export_onnx(best_pt: str | Path, imgsz: int = 640, models_dir: str | Path = "models") -> Path:
    """Exporta ``best.pt`` a ONNX y copia ambos a ``models/best_model.{pt,onnx}``."""
    from ultralytics import YOLO  # type: ignore

    best_pt = resolve_path(best_pt)
    onnx_path = Path(YOLO(str(best_pt)).export(format="onnx", imgsz=imgsz, simplify=True, opset=12))
    out = resolve_path(models_dir)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_pt, out / "best_model.pt")
    shutil.copy2(onnx_path, out / "best_model.onnx")
    logger.info("Modelos copiados a %s", out)
    return out / "best_model.onnx"


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description="Entrena/exporta el detector YOLO11-s de SIRAP")
    parser.add_argument("--data", help="ruta de data.yaml")
    parser.add_argument("--roboflow", action="store_true", help="descargar el dataset de Roboflow")
    parser.add_argument("--epochs", type=int, default=DEFAULT_HPARAMS["epochs"])
    parser.add_argument("--imgsz", type=int, default=DEFAULT_HPARAMS["imgsz"])
    parser.add_argument("--batch", type=int, default=DEFAULT_HPARAMS["batch"])
    parser.add_argument("--force", action="store_true", help="reentrenar desde cero")
    parser.add_argument("--export-only", metavar="BEST_PT", help="solo exportar estos pesos a ONNX")
    args = parser.parse_args()

    if args.export_only:
        export_onnx(args.export_only, args.imgsz)
        return
    data_yaml = download_roboflow_dataset() if args.roboflow else args.data
    if not data_yaml:
        parser.error("indique --data o --roboflow")
    best = train(data_yaml, force=args.force, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch)
    export_onnx(best, args.imgsz)


if __name__ == "__main__":
    main()
