# Resultados

| Carpeta | Contenido |
|---|---|
| `figures/` | Gráficos del notebook para el informe y los documentos (`docs/`) |
| `metrics/` | Métricas en JSON/CSV que lee la app («Acerca del modelo») y el README |
| `reports/` | Logs de la app (`sirap.log`, ignorado por git) y reportes generados |

## Archivos de métricas esperados

| Archivo | Generado por | Campos |
|---|---|---|
| `metrics/detector_test.json` | Notebook, sección 5.1 · `python -m src.evaluate detector` | `map50`, `map50_95`, `precision`, `recall`, `f1` |
| `metrics/umbrales.json` | Notebook, sección 4.1 (calibración en *val*) | `{"YOLO11": {"conf": …}}` |
| `metrics/ocr_savh.json` | Notebook, secciones 4.3 y 5.4 | `emr`, `cer`, `n` |
| `metrics/e2e.json` | Notebook, sección 7 · `python -m src.evaluate e2e` | `emr`, `cer`, `tiempo_ms_promedio` |
| `metrics/velocidad.json` | Notebook, sección 5.3 | latencia, FPS, parámetros, GFLOPs |
| `metrics/optimizacion_trials.csv` | `notebooks/04_optimizacion.ipynb` | Hiperparámetros, mAP@0.5:0.95 y mAP@0.5 (*val*) de los 24 *trials* |
| `metrics/optimizacion_importancia.csv` | `notebooks/04_optimizacion.ipynb` | Importancia fANOVA y por permutación |
| `metrics/optimizacion_antes_despues.csv`, `optimizacion_resumen.json` | `notebooks/04_optimizacion.ipynb` | Mejor configuración y comparación en *test* |

Los valores salen de las carpetas `resultados/` y `figuras/` del experimento en Drive
(`MyDrive/proyecto_integrador_placas/experimentos/<dataset>/`). Si un archivo no está, la app muestra
«pendiente» en lugar de inventar un número.

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.
