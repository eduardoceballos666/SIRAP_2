# Resultados

| Carpeta | Contenido |
|---|---|
| `figures/` | Gráficos del notebook para el informe y los documentos (`docs/`) |
| `metrics/` | Métricas en JSON/CSV que lee la app («Acerca del modelo») y el README |
| `reports/` | Logs de la app (`sirap.log`, ignorado por git) y reportes generados |

## Archivos de métricas esperados

| Archivo | Generado por | Campos |
|---|---|---|
| `metrics/detector_test.json` | Notebook, sección 3 · `python -m src.evaluate detector` | `map50`, `map50_95`, `precision`, `recall`, `f1` |
| `metrics/umbrales.json` | Notebook, sección 3 (calibración en *val*) | `{"YOLO11": {"conf": …}}` |
| `metrics/ocr_savh.json` | Notebook, sección 5 | `emr`, `cer`, `n` |
| `metrics/e2e.json` | Notebook, sección 7 · `python -m src.evaluate e2e` | `emr`, `cer`, `tiempo_ms_promedio` |
| `metrics/velocidad.json` | Notebook, sección 4 | latencia, FPS, parámetros, GFLOPs |

Los valores salen de las carpetas `resultados/` y `figuras/` del experimento en Drive
(`MyDrive/proyecto_integrador_placas/experimentos/<dataset>/`). Si un archivo no está, la app muestra
«pendiente» en lugar de inventar un número.
