# Modelos

| Archivo | Qué es | Cómo se obtiene |
|---|---|---|
| `best_model.pt` | Pesos de **YOLO11-s** entrenado (mejor época en *val*) | `MyDrive/proyecto_integrador_placas/experimentos/license-plate-recognition-rxg4e-v11/runs/YOLO11_yolo11s_completo/weights/best.pt` |
| `best_model.onnx` | El mismo modelo exportado a ONNX (640 px) | `python -m src.train --export-only models/best_model.pt` |
| *OCR* | `fast-plate-ocr` · `cct-s-v2-global-model` (≈5 MB) | Se descarga solo la primera vez que corre la app |
| `ocr_afinado.onnx` + `ocr_afinado_plate_config.yaml` *(opcional)* | OCR afinado con placas ecuatorianas | `notebooks/06_afinamiento_ocr.ipynb`; súbalo **solo** si la sección 5 de ese notebook decide «adoptar». Si existen, la app los usa en lugar del modelo del hub |

La app carga primero el **ONNX** con ONNX Runtime: no necesita PyTorch y cabe en Streamlit Community Cloud. Si
no hay ONNX usa `best_model.pt` (requiere `ultralytics`). Si no hay ninguno, usa un localizador clásico de OpenCV
y la interfaz muestra el aviso **«Detector de respaldo activo»**.

> **No reentrenar.** El entrenamiento ya se hizo en Colab (sección 2.1 del notebook, preset `completo`).
> `best_model.pt` es ese `best.pt` y `best_model.onnx` su exportación (opset 12, 640 px, `simplify=True`).
> Verificado: en las imágenes de `data/samples/` las cajas y confianzas del ONNX coinciden con las de Ultralytics
> (diferencia ≤ 1 px y ≤ 0,002).

## Ficha del detector

| Campo | Valor |
|---|---|
| Arquitectura | YOLO11-s (Ultralytics 8.4.177), 9,41 M parámetros, 21,4 GFLOPs a 640 px |
| Pesos iniciales | `yolo11s.pt` (COCO) |
| Dataset | License Plate Recognition v11 (Roboflow, CC BY 4.0), 1 clase |
| Entrenamiento | 40 épocas, imgsz 640, batch 16 (nbs 64), paciencia 10, semilla 0, AdamW (elegido por Ultralytics) |
| Postproceso | NMS con IoU 0,7 (por defecto de Ultralytics) |
| Umbral | calibrado en *val*: 0,30 (`results/metrics/umbrales.json`) |
| Entrenamiento | 40 épocas (mejor: 40), 0,70 h y 6,9 GB de GPU pico en una NVIDIA L4 |
| Métricas en *test* | mAP@0.5 0,972 · mAP@0.5:0.95 0,693 · P 0,986 · R 0,956 · F1 0,971 (`results/metrics/detector_test.json`) |
| Velocidad | 22,2 ms por imagen (lote 1, FP16, L4) · 9,41 M parámetros · 21,4 GFLOPs |

## Versiones anteriores

El proyecto pasó por YOLOv8 + EasyOCR/PaddleOCR (v1), RF-DETR + OC-SORT + GLM-OCR y YOLOv8n + GLM-OCR antes de la
versión final YOLO11-s + fast-plate-ocr. Si se conservan pesos de esas versiones, guárdelos como `model_v1.pt`,
`model_v2.pt`, … con una línea en esta tabla indicando de qué versión son.
