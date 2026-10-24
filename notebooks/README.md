# Notebooks

| Notebook | Contenido |
|---|---|
| `SIRAP_backend.ipynb` | **Notebook completo (fuente de verdad).** Secciones 0–10: preparación, dataset, entrenamiento de YOLO11-s, evaluación, velocidad, OCR y regla de decisión, pipeline en video con OC-SORT, base de la planta y SRI, evaluación con referencia, resultados finales y modo en vivo |
| `01_exploracion.ipynb` | EDA del dataset de detección (secciones 0–1) |
| `02_preprocesamiento.ipynb` | Preparación del dataset para Ultralytics y normalización de placas |
| `03_modelado.ipynb` | Entrenamiento de YOLO11-s (no reentrena: muestra el registro y las curvas) |
| `04_optimizacion.ipynb` | Estudio de sensibilidad de hiperparámetros (Workshop S5): Optuna + fANOVA + PDP |
| `05_evaluacion.ipynb` | Evaluación del detector, velocidad, OCR en SAVH, regla de decisión y resultados finales |

Los notebooks 01, 02, 03 y 05 son extractos de `SIRAP_backend.ipynb` con las mismas celdas y salidas.
Todos corren en **Google Colab con GPU** y guardan en `MyDrive/proyecto_integrador_placas` (rutas en la sección 0).
Secrets necesarios: `ROBOFLOW_API_KEY` (dataset) y, opcionales, `PG_DSN`, `CAMARA_URL`, `CAMARA_TOKEN`.

**Versión 4.0 (24/10/2026).** El backend usa un solo detector, YOLO11-s; se retiró el segundo detector y la
comparación entre detectores. El entrenamiento de YOLO11-s (preset `completo`, 40 épocas, 0,70 h en una GPU L4)
se conserva en Drive y el notebook no lo repite.
