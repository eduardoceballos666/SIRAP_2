# Notebooks

| Notebook | Contenido |
|---|---|
| [`SIRAP_backend.ipynb`](SIRAP_backend.ipynb) | Flujo completo de preparación, detector YOLO11-s, OCR, optimización, evaluación, video de garita y modo en vivo. El notebook no incrusta videos. |
| [`01_exploracion.ipynb`](01_exploracion.ipynb) | Análisis exploratorio del dataset de detección y de SAVH. |
| [`02_preprocesamiento.ipynb`](02_preprocesamiento.ipynb) | Preparación del dataset YOLO, normalización y referencia de SAVH. |
| [`03_modelado.ipynb`](03_modelado.ipynb) | Entrenamiento del detector, OCR y regla de decisión. |
| [`04_optimizacion.ipynb`](04_optimizacion.ipynb) | Estudio de sensibilidad de hiperparámetros con Optuna, fANOVA y PDP. |
| [`05_evaluacion.ipynb`](05_evaluacion.ipynb) | Evaluación del detector, velocidad, OCR y resultados finales. |
| [`06_afinamiento_ocr.ipynb`](06_afinamiento_ocr.ipynb) | Afinamiento opcional del OCR con datos ecuatorianos. |
| [`07_validacion_multisemilla.ipynb`](07_validacion_multisemilla.ipynb) | Validación de entrenamiento con distintas semillas. |

## Ejecutar `SIRAP_backend.ipynb` desde GitHub

1. Abre el notebook desde GitHub en Colab y ejecuta la sección 0. Clona el repositorio, instala dependencias y prepara las rutas. No monta Google Drive.
2. Para descargar el dataset público de Roboflow y ejecutar entrenamiento o evaluación de componentes, agrega `ROBOFLOW_API_KEY` a Secrets de Colab. La alternativa es configurar `DATASET_SOURCE = "local"` y proporcionar el ZIP del dataset en `data/raw/dataset_placas_yolo.zip`.
3. La sección 0 descarga automáticamente el video fuente desde el [Release `datos-garita-v1`](https://github.com/eduardoceballos666/SIRAP_2/releases/tag/datos-garita-v1) a `artifacts/video_camiones.mp4` y verifica tamaño e integridad. La sección 6.1 usa ese video por defecto; `USE_SAMPLE_VIDEO = True` selecciona la demo y no sirve para medir el caso de los camiones.
4. Corre las celdas previas en el mismo runtime antes de cada sección. En una sesión nueva, los pesos de entrenamiento y los umbrales guardados en el espacio temporal no se conservan. Si no hay un checkpoint de la corrida en `/content/SIRAP_workspace`, ejecuta 3.2; después corre 4.1 para generar los umbrales.
5. La evaluación 7.3 usa las 21 imágenes y `garita/ground_truth.csv` versionadas en el repositorio. Necesita que el detector y los umbrales estén listos en la sesión antes de ejecutarla.
6. Las salidas se guardan en `/content/SIRAP_workspace`, que es temporal. Descarga los archivos que quieras conservar desde el panel **Files** de Colab. Los videos anotados no se incrustan ni se publican automáticamente como Release assets.

## Resultados y límites

Los resultados agregados y gráficos pequeños están en [`results/metrics/`](../results/metrics/) y [`results/figures/`](../results/figures/). La evaluación de video de la sección 7.2 sigue siendo provisional: usa 18 cuadros puntuales y no cubre intervalos completos ni todos los vehículos. Consulta la [revisión de la referencia de video](../blind_eval/video_ground_truth_review.md) y el archivo de [puntos provisionales](../blind_eval/video_ground_truth_points_provisional.csv). No presentes esas métricas como evaluación integral del video.


## Aplicación y código fuente

El notebook forma parte del proyecto SIRAP_2 y produce evidencia del detector/OCR; la aplicación web desplegada se encuentra en [Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP) y puede abrirse en https://eduardoceballos-sirap.hf.space. La interfaz ofrece español e inglés y la [API interactiva](https://eduardoceballos-sirap.hf.space/docs) está disponible para consulta.

Consulta el [repositorio GitHub](https://github.com/eduardoceballos666/SIRAP_2) para el código y los artefactos; los videos de presentación están al final de su [README](../README.md).