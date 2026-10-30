"""Repite base vs. trial 12 con semillas emparejadas sin sustituir el modelo publicado.

Requiere Ultralytics, CUDA y el data_abs.yaml de Roboflow v11 preparado por
notebooks/04_optimizacion.ipynb. Usa el mismo test SOLO para reportar, no para
elegir hiperparámetros. Guarda una corrida por semilla y evita sobreescrituras.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = {
    "lr0": 0.002,
    "weight_decay": 0.0005,
    "imgsz": 640,
    "batch": 16,
    "mosaic": 1.0,
    "hsv_v": 0.4,
    "cos_lr": False,
}
PARAM_KEYS = set(BASE)


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def summary_for(rows: list[dict], seeds: list[int]) -> dict:
    by_seed = {}
    for row in rows:
        by_seed.setdefault(row["semilla"], {})[row["modelo"]] = row
    pairs = []
    for seed in seeds:
        models = by_seed.get(seed, {})
        if "base" in models and "optimizada" in models:
            b, o = models["base"], models["optimizada"]
            pairs.append({
                "semilla": seed,
                "map50_95_base": b["map50_95"],
                "map50_95_optimizada": o["map50_95"],
                "delta_map50_95": o["map50_95"] - b["map50_95"],
                "delta_recall": o["recall"] - b["recall"],
            })
    deltas = [p["delta_map50_95"] for p in pairs]
    return {
        "estado": "completo" if len(pairs) == len(seeds) else "parcial",
        "semillas_planeadas": seeds,
        "pares_completos": len(pairs),
        "comparaciones_pareadas": pairs,
        "delta_medio_map50_95": statistics.mean(deltas) if deltas else None,
        "delta_std_map50_95": statistics.stdev(deltas) if len(deltas) > 1 else None,
        "semillas_con_mejora": sum(d > 0 for d in deltas),
        "nota": (
            "Comparación experimental multisemilla, distinta de los pesos publicados. "
            "Tres semillas solo permiten evaluar estabilidad descriptiva; "
            "no demuestran significación estadística ni mejora punta a punta."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validación multisemilla de YOLO11-s")
    parser.add_argument("--data-yaml", type=Path, required=True)
    parser.add_argument("--opt-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    import pandas as pd
    import torch
    import ultralytics
    from ultralytics import YOLO

    if len(set(args.seeds)) != len(args.seeds) or len(args.seeds) < 2:
        raise ValueError("Incluya al menos dos semillas distintas, por ejemplo 0 1 2.")
    if not torch.cuda.is_available():
        raise RuntimeError("Se requiere GPU CUDA. Active GPU T4/L4 en Google Colab.")
    if not args.data_yaml.is_file():
        raise FileNotFoundError(f"No existe data.yaml: {args.data_yaml}")
    if not args.opt_summary.is_file():
        raise FileNotFoundError(f"No existe resumen del trial 12: {args.opt_summary}")
    best = json.loads(args.opt_summary.read_text(encoding="utf-8"))["mejor_config"]
    if set(best) != PARAM_KEYS:
        raise ValueError("La configuración optimizada no contiene los 7 parámetros esperados.")
    configs = {"base": BASE, "optimizada": best}
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    data_file = args.data_yaml.expanduser().resolve()
    data_hash = hashlib.sha256(data_file.read_bytes()).hexdigest()
    manifest = {
        "estudio": "SIRAP YOLO11-s validación multisemilla",
        "data_yaml": str(data_file),
        "data_yaml_sha256": data_hash,
        "pretrained": "yolo11s.pt",
        "epochs": 40,
        "patience": 10,
        "optimizer": "AdamW",
        "deterministic": True,
        "seeds": args.seeds,
        "configuraciones": configs,
        "ultralytics": ultralytics.__version__,
        "pytorch": torch.__version__,
        "gpu": torch.cuda.get_device_name(0),
        "modelo_deploy": "SIN CAMBIOS: models/best_model.onnx",
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_file = output / "protocolo.json"
    if manifest_file.exists():
        previous = json.loads(manifest_file.read_text(encoding="utf-8"))
        check = ["data_yaml_sha256", "epochs", "patience", "optimizer",
                 "deterministic", "seeds", "configuraciones", "ultralytics"]
        if any(previous.get(k) != manifest[k] for k in check):
            raise RuntimeError("Protocolo distinto en carpeta existente: use otro --output-dir.")
    else:
        save_json(manifest_file, manifest)

    all_rows = []
    for seed in args.seeds:
        for label, params in configs.items():
            name = f"{label}_semilla_{seed}"
            run_dir = output / "runs" / name
            weights = run_dir / "weights" / "best.pt"
            record_file = output / "metricas_individuales" / f"{name}.json"
            if record_file.exists():
                result = json.loads(record_file.read_text(encoding="utf-8"))
                if result.get("semilla") != seed or result.get("modelo") != label:
                    raise ValueError(f"Resultado previo incompatible: {record_file}")
                all_rows.append(result)
                print(f"Reutilizando métricas verificadas: {name}")
                continue
            if not weights.exists():
                if run_dir.exists():
                    raise RuntimeError(
                        f"Corrida incompleta en {run_dir}. Revise el checkpoint antes de reanudar "
                        "o use otra carpeta; no se sobrescribirá automáticamente."
                    )
                print(f"Entrenando {name}...")
                YOLO("yolo11s.pt").train(
                    data=str(data_file),
                    epochs=40,
                    patience=10,
                    seed=seed,
                    deterministic=True,
                    optimizer="AdamW",
                    workers=args.workers,
                    device=args.device,
                    project=str(output / "runs"),
                    name=name,
                    exist_ok=False,
                    plots=False,
                    verbose=False,
                    **params,
                )
                if not weights.exists():
                    raise RuntimeError(f"No se generaron pesos: {weights}")
            # Evaluación test idéntica en ambas configuraciones; no elegir parámetros con test.
            m = YOLO(str(weights)).val(
                data=str(data_file),
                split="test",
                imgsz=int(params["imgsz"]),
                device=args.device,
                verbose=False,
                plots=False,
            )
            record = {
                "semilla": seed, "modelo": label,
                "map50": float(m.box.map50),
                "map50_95": float(m.box.map),
                "precision": float(m.box.mp),
                "recall": float(m.box.mr),
                "weights": str(weights),
            }
            save_json(record_file, record)
            all_rows.append(record)
            print(f"{name}: mAP50-95={record['map50_95']:.4f}")

            # Salida intermedia tras cada corrida completa.
            pd.DataFrame(all_rows).sort_values(["semilla", "modelo"]).to_csv(
                output / "comparacion_multisemilla.csv", index=False
            )
            save_json(output / "resumen_multisemilla.json", summary_for(all_rows, args.seeds))

    all_rows.sort(key=lambda r: (r["semilla"], r["modelo"]))
    pd.DataFrame(all_rows).to_csv(output / "comparacion_multisemilla.csv", index=False)
    summary = summary_for(all_rows, args.seeds)
    save_json(output / "resumen_multisemilla.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("Resultados:", output)


if __name__ == "__main__":
    main()
