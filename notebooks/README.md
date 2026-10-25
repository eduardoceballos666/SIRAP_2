# Notebooks

| Notebook | Contenido |
|---|---|
| `SIRAP_backend.ipynb` | **Notebook completo (fuente de verdad).** Sigue el ciclo de vida del enunciado: 0 preparación del entorno · 1 datos y análisis exploratorio · 2 preprocesamiento · 3 modelado (YOLO11-s, fast-plate-ocr, regla de decisión) · 4 optimización (umbrales, hiperparámetros, confianza del OCR) · 5 evaluación de los componentes · 6 sistema completo en video (OC-SORT, autorizaciones CSV, SRI) · 7 evaluación del sistema · 8 resultados finales · 9 modo en vivo |
| `01_exploracion.ipynb` | Datos y análisis exploratorio: dataset de detección y recortes de SAVH Guayaquil (secciones 0 y 1) |
| `02_preprocesamiento.ipynb` | Preparación del dataset para Ultralytics, normalización de placas y referencia corregida de SAVH (secciones 0, 1.1, 1.3 y 2) |
| `03_modelado.ipynb` | Entrenamiento de YOLO11-s (no reentrena: muestra el registro y las curvas), fast-plate-ocr y regla de decisión (secciones 0, 1.1, 2.1 y 3) |
| `04_optimizacion.ipynb` | Estudio de sensibilidad de hiperparámetros (Workshop S5): Optuna + fANOVA + PDP, y comparación antes/después en *test* |
| `05_evaluacion.ipynb` | Evaluación de los componentes (detector, velocidad, OCR en SAVH y regla de decisión) y resultados finales (secciones 5 y 8, con las celdas de 0 a 4 que necesitan) |
| `06_afinamiento_ocr.ipynb` | Afinamiento de fast-plate-ocr con placas ecuatorianas (SAVH + garita), separación por placa, comparación antes/después con McNemar y medición con recortes del detector |

Los notebooks 01, 02, 03 y 05 son extractos de `SIRAP_backend.ipynb` con las mismas celdas, salidas y numeración de
secciones. Todos corren en **Google Colab con GPU** y guardan en `MyDrive/proyecto_integrador_placas` (rutas en la sección 0).
Secrets necesarios: `ROBOFLOW_API_KEY` (dataset). Para sincronizar lecturas, opcionales `GITHUB_TOKEN` y `GITHUB_DATA_REPOSITORY` (un repositorio privado); para cámara, `CAMARA_URL` y `CAMARA_TOKEN`.

**Versión del 24/10/2026.** El backend usa un solo detector, YOLO11-s, y un solo OCR, fast-plate-ocr; las secciones
se ordenaron según el enunciado (datos → preprocesamiento → modelado → optimización → evaluación). El entrenamiento de YOLO11-s (preset `completo`, 40 épocas, 0,70 h en una GPU L4)
se conserva en Drive y el notebook no lo repite.
