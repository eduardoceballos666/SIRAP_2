# Notebooks

| Notebook | Contenido |
|---|---|
| [`SIRAP_backend.ipynb`](SIRAP_backend.ipynb) | Notebook completo actualizado desde Drive. Incluye preparación del entorno, datos, preprocesamiento, YOLO11-s, fast-plate-ocr, optimización, evaluación de componentes, pipeline de video, evaluaciones 7.2/7.3 y modo en vivo. El video no está incrustado. |
| `01_exploracion.ipynb` | Análisis exploratorio del dataset de detección y de SAVH. |
| `02_preprocesamiento.ipynb` | Preparación del dataset YOLO, normalización y referencia de SAVH. |
| `03_modelado.ipynb` | Entrenamiento del detector, OCR y regla de decisión. |
| `04_optimizacion.ipynb` | Estudio de sensibilidad de hiperparámetros con Optuna, fANOVA y PDP. |
| `05_evaluacion.ipynb` | Evaluación de detector, velocidad, OCR y resultados finales. |
| `06_afinamiento_ocr.ipynb` | Afinamiento opcional del OCR con datos ecuatorianos. |

## Ejecutar `SIRAP_backend.ipynb` sin Google Drive

1. Abre el notebook desde GitHub en Google Colab y ejecuta la sección 0. Esta clona el repositorio y lee de GitHub el modelo, los archivos SAVH y el CSV de revisión, la lista autorizada y los resultados ya publicados.
2. Configura el secreto `ROBOFLOW_API_KEY` en Colab para descargar el dataset público y correr entrenamiento/evaluación. El notebook no monta Drive ni solicita autorización de Google Sheets.
3. La sección 6.1 usa por defecto un video público de demostración. Para evaluar el video fuente del proyecto, publica `video_camiones.mp4` como artefacto separado y cópialo a `artifacts/video_camiones.mp4` en el entorno de Colab. Las imágenes completas de garita y la referencia revisada son entradas opcionales de 7.3.
4. El video anotado se guarda aparte; la celda 6.11 solo muestra su ruta y tamaño, nunca incrusta el MP4.
5. Los resultados de una corrida nueva quedan en `/content/SIRAP_workspace`. Descárgalos desde Colab si deseas conservarlos o publicarlos. Los resultados compactos ya comprobados están en [`../results/metrics/`](../results/metrics/) y los gráficos pequeños en [`../results/figures/`](../results/figures/).

El dataset público puede requerir su clave de API; el resto de insumos de evaluación SAVH y los pesos de YOLO11-s ya están en el repositorio. Las corridas de entrenamiento pueden tardar y necesitan GPU; abrir el notebook no inicia entrenamiento.

## Límites de la evaluación de video

La sección 7.2 registra una corrida provisional sobre 18 cuadros puntuales. Se publica explícitamente como tal en [`video_e2e_puntos_provisionales_20261101.md`](../results/metrics/video_e2e_puntos_provisionales_20261101.md); no representa intervalos completos, todos los vehículos ni validación humana independiente. El artefacto fuente completo de 459 MB todavía no se ha publicado en GitHub.
