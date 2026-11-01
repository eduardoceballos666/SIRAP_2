# Notebooks de SIRAP

Los notebooks documentan el análisis de datos, la preparación, el entrenamiento, la optimización y la evaluación del sistema.

| Notebook | Propósito |
|---|---|
| [SIRAP_backend.ipynb](SIRAP_backend.ipynb) | Flujo principal: detector YOLO11-s, OCR, reglas de acceso, video de garita, evaluaciones 7.2 y 7.3, y modo en vivo. No incrusta videos. |
| [01_exploracion.ipynb](01_exploracion.ipynb) | Análisis exploratorio del dataset de detección y de SAVH. |
| [02_preprocesamiento.ipynb](02_preprocesamiento.ipynb) | Preparación del dataset YOLO, normalización y referencias de SAVH. |
| [03_modelado.ipynb](03_modelado.ipynb) | Entrenamiento del detector, integración OCR y regla de decisión. |
| [04_optimizacion.ipynb](04_optimizacion.ipynb) | Búsqueda de hiperparámetros con Optuna y análisis de sensibilidad. |
| [05_evaluacion.ipynb](05_evaluacion.ipynb) | Evaluación del detector, velocidad, OCR y resultados de componentes. |
| [06_afinamiento_ocr.ipynb](06_afinamiento_ocr.ipynb) | Experimento opcional de afinamiento del OCR con placas ecuatorianas. |
| [07_validacion_multisemilla.ipynb](07_validacion_multisemilla.ipynb) | Comparación del detector con distintas semillas. |

## Ejecutar `SIRAP_backend.ipynb` desde GitHub

1. Abre el notebook en Colab y ejecuta la sección 0. Clona SIRAP_2, prepara las rutas y descarga el video de garita. No monta Google Drive.
2. Roboflow es la fuente de dataset predeterminada. Configura `ROBOFLOW_API_KEY` en Secrets de Colab si vas a descargar ese dataset y ejecutar sus secciones de preparación o entrenamiento. Como alternativa, cambia `DATASET_SOURCE = "local"` y proporciona un ZIP YOLO en `data/raw/dataset_placas_yolo.zip`.
3. La sección 0 descarga el video fuente desde el [Release `datos-garita-v1`](https://github.com/eduardoceballos666/SIRAP_2/releases/tag/datos-garita-v1) a `artifacts/video_camiones.mp4` y valida su integridad. La sección 6.1 usa ese video por defecto (`USE_SAMPLE_VIDEO = False`). `True` selecciona el video de demostración de estacionamiento, que sirve para comprobar el flujo, no para medir el caso de los camiones.
4. Las celdas de Colab y sus archivos temporales se pierden al reiniciar la sesión. En una sesión limpia, la sección 0 prepara el checkpoint publicado `models/best_model.pt` y los umbrales versionados `results/metrics/umbrales.json`; no necesitas volver a entrenar ni calibrar para usar esos valores. Ejecuta las celdas previas que indique cada evaluación en el mismo runtime. Si decides reentrenar, activa `FORCE_RETRAIN = True` o corre el entrenamiento correspondiente; luego ejecuta 4.1 para recalibrar los umbrales. El historial de entrenamiento no está versionado, así que el checkpoint publicado no reproduce por sí solo las curvas.
5. Las evaluaciones guardan salidas nuevas en `/content/SIRAP_workspace`. Descarga desde el panel **Files** los archivos que quieras conservar. Los videos anotados no se incrustan en el notebook ni se publican automáticamente como assets de Release.

## Resultados y límites de evaluación

### Imágenes de la garita — sección 7.3

La sección 7.3 procesa 21 imágenes y usa `garita/ground_truth.csv`. En el resultado publicado, el detector encontró placa en 19/21 imágenes y el EMR fue **8/21 (38,1 %)**, por debajo de la meta de 80 %. La latencia media fue 37,69 ms por imagen. La lista de autorizaciones estaba vacía en esa evaluación, por lo que el resultado de cero falsos autorizados no demuestra cómo funciona la autorización con una lista poblada. Consulta el [informe de evaluación por imágenes](../results/metrics/garita_imagenes_e2e_20261101.md).

### Video de garita — sección 7.2

La referencia publicada contiene **18 cuadros puntuales**, no intervalos completos ni un censo de todos los vehículos. En esa muestra, la coincidencia exacta fue 11/18 (61,1 %) y el recall por placas únicas en los puntos fue 9/16 (56,25 %). Son métricas provisionales condicionadas a esos cuadros; no representan evaluación integral del video ni recall de todas las pasadas. Revisa el [informe de la referencia](../blind_eval/video_ground_truth_review.md), el [CSV provisional](../blind_eval/video_ground_truth_points_provisional.csv) y el [reporte de la corrida](../results/metrics/video_e2e_puntos_provisionales_20261101.md).

Los gráficos pequeños y las métricas agregadas están en [figuras](../results/figures/) y [métricas](../results/metrics/). El video de origen se descarga desde el Release; las nuevas salidas permanecen en el espacio temporal de Colab hasta que se descarguen.

## Aplicación y código fuente

La aplicación web se encuentra en [Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP) y puede abrirse en [eduardoceballos-sirap.hf.space](https://eduardoceballos-sirap.hf.space). La interfaz ofrece español e inglés; la [API interactiva](https://eduardoceballos-sirap.hf.space/docs) está disponible para consulta.

El código, los notebooks y los artefactos están en [GitHub SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2). Los videos de presentación están enlazados al final del [README principal](../README.md).