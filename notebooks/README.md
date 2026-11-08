# Notebooks de SIRAP

Los notebooks documentan el análisis de datos, la preparación, el entrenamiento, la optimización y la evaluación del sistema.

| Notebook | Propósito |
|---|---|
| [SIRAP_backend.ipynb](SIRAP_backend.ipynb) | Flujo principal: detector YOLO11-s, OCR, reglas de acceso, video de garita, evaluaciones 7.2 y 7.3, y modo en vivo. No incrusta videos. |
| [Evaluacion_IC_Wilson.ipynb](Evaluacion_IC_Wilson.ipynb) | Cálculo reproducible de los IC de Wilson para coincidencia exacta y cobertura OCR en el holdout SAVH. |
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
4. Las celdas de Colab y sus archivos temporales se pierden al reiniciar la sesión. En una sesión limpia, el notebook usa el checkpoint publicado `models/best_model.pt` y recupera los umbrales versionados de `results/metrics/umbrales.json` si no hay valores generados en esa sesión; no necesitas volver a entrenar ni calibrar para usar esos valores. Ejecuta las celdas previas que indique cada evaluación en el mismo runtime. Si decides reentrenar, activa `FORCE_RETRAIN = True` o corre el entrenamiento correspondiente; luego ejecuta 4.1 para recalibrar los umbrales.
5. Las evaluaciones guardan salidas nuevas en `/content/SIRAP_workspace`. Descarga desde el panel **Files** los archivos que quieras conservar. Los videos anotados no se incrustan en el notebook ni se publican automáticamente como assets de Release.

## Historial y resumen de entrenamiento YOLO11

Los artefactos de entrenamiento ya están versionados en [métricas](../results/metrics/). Cada CSV contiene los valores por época, incluidas las pérdidas de entrenamiento y validación, precisión, recall y mAP. Los JSON conservan el resumen de la corrida.

| Corrida | Datos usados | Historial por época | Resumen |
|---|---|---|---|
| **Completa (preset vigente: `TRAINING_PRESET = "completo"`)** | 40 épocas; `train_fraction = 1`, `val_fraction = 1` | [entrenamiento_yolo11_results.csv](../results/metrics/entrenamiento_yolo11_results.csv) | [entrenamiento_yolo11_completo.json](../results/metrics/entrenamiento_yolo11_completo.json) |
| Rápida | 15 épocas; `train_fraction = 0.3`, `val_fraction = 0.25` | [entrenamiento_yolo11_rapido_results.csv](../results/metrics/entrenamiento_yolo11_rapido_results.csv) | [entrenamiento_yolo11_rapido.json](../results/metrics/entrenamiento_yolo11_rapido.json) |

Para revisar posible sobreajuste, compara por época las pérdidas de entrenamiento y validación, junto con las métricas de validación. Un puntaje final aislado no basta para concluir que no hubo sobreajuste. La corrida completa con `TRAINING_PRESET = "completo"` es el preset utilizado y documentado como referencia. La corrida rápida sirve solo como ejecución reducida; debido a que usa fracciones distintas del dataset, sus resultados no son directamente comparables con los de la corrida completa. Los CSV y JSON son registros de las corridas publicadas; el checkpoint `models/best_model.pt` contiene los pesos y no reemplaza el historial.

## Resultados y límites de evaluación

### Imágenes de la garita — sección 7.3

La sección 7.3 procesa 21 imágenes y usa `garita/ground_truth.csv`. El informe publicado registra detección 19/21, EMR **8/21 (38,1 %)** y latencia media de 37,69 ms. La salida guardada del notebook registra otra ejecución con detección 19/21, EMR **9/21 (42,9 %)** y latencia media de 1,400674 s. Como esa salida no tiene fecha ni ID de corrida, se presentan por separado y no se combinan. El informe documenta que la lista de autorizaciones estaba vacía; la salida del notebook no conserva cuál lista cargó. El archivo `data/authorized_plates.csv` está poblado en el repositorio actual, así que el cero del informe no demuestra el comportamiento con la lista publicada actualmente. Consulta el [informe de evaluación por imágenes](../results/metrics/garita_imagenes_e2e_20261101.md).

### Video de garita — sección 7.2

La sección 7.2 usa la **referencia publicada** [`blind_eval/video_ground_truth.csv`](../blind_eval/video_ground_truth.csv): 20 pasadas con columnas `plate_gt,frame_start,frame_end` e intervalos inclusivos. En la reejecución más reciente, 6.9 procesó 18.115 cuadros y registró 51 lecturas; 7.2 comparó 30 con la referencia y obtuvo EMR 18/30 (60 %), recall de placas únicas 16/17 (94,12 %) y 2/30 falsas autorizaciones observadas entre las lecturas clasificables. Las otras 21 lecturas no tienen referencia y quedan sin clasificar, por lo que la tasa integral para todo el video no es estimable. Dos pasadas dudosas siguen excluidas. La corrida guardada anterior (34 lecturas, EMR 17/24, recall 15/17 y 0/24 falsas autorizaciones) se documenta por separado; no combines sus resultados con la reejecución. Consulta el [informe de métricas](../results/metrics/video_e2e_intervalos_final.md). Las cifras 11/18 (61,1 %) y 9/16 (56,25 %) son históricas ([reporte](../results/metrics/video_e2e_puntos_provisionales_20261101.md)).

Los gráficos pequeños y las métricas agregadas están en [figuras](../results/figures/) y [métricas](../results/metrics/). El video de origen se descarga desde el Release; las nuevas salidas permanecen en el espacio temporal de Colab hasta que se descarguen.

## Aplicación y código fuente

La aplicación web se encuentra en [Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP) y puede abrirse en [eduardoceballos-sirap.hf.space](https://eduardoceballos-sirap.hf.space). La interfaz ofrece español e inglés; la [API interactiva](https://eduardoceballos-sirap.hf.space/docs) está disponible para consulta. El workflow de despliegue sincroniza `SIRAP_backend.ipynb` con el Space cuando ese notebook cambia en `main`.

El código, los notebooks y los artefactos están en [GitHub SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2). Los videos de presentación están enlazados al final del [README principal](../README.md).


## IC de Wilson

El notebook calcula y explica el IC score de Wilson al 95 % para las proporciones binarias del holdout SAVH. Muestra los conteos, porcentajes e intervalos para OCR base y afinado. La explicación metodológica está en [docs/ic_wilson.md](../docs/ic_wilson.md).
